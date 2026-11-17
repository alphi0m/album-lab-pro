"""
Finestra modale per la trasmissione sicura delle commesse dal fotografo al server del laboratorio.
Include test di connessione, riepilogo commessa, barra di avanzamento e report di conferma.
"""

import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from src.core.config import ConfigManager
from src.services.network import OrderUploader, check_server_status
from src.ui.theme import (
    BG_APP, BG_CARD, BG_DARKEST, PRIMARY, SUCCESS, WARNING, DANGER,
    TEXT_PRIMARY, TEXT_MUTED, BORDER_COLOR
)


class UploadDialog(tk.Toplevel):
    """Finestra di dialogo per l'invio dell'ordine via rete con streaming progressivo."""

    def __init__(
        self,
        parent: tk.Tk,
        order_data: dict,
        foto_list: list,
        on_success_callback: Optional[Callable[[str], None]] = None
    ):
        super().__init__(parent)
        self.parent = parent
        self.order_data = order_data
        self.foto_list = foto_list
        self.on_success_callback = on_success_callback

        self.config_mgr = ConfigManager()
        self.cancel_event = threading.Event()
        self.upload_thread = None
        self.completed_order_id = None

        self.title("Trasmissione Ordine al Laboratorio — Album Lab Pro")
        self.geometry("680x740")
        self.minsize(620, 680)
        self.configure(bg=BG_APP)
        self.resizable(False, False)

        # Rendi modale
        self.transient(parent)
        self.grab_set()

        # Centra la finestra rispetto al genitore
        self._centra_finestra(parent)

        # Costruisce i componenti
        self._build_ui()

        # Esegue un test di connessione iniziale in background
        self._test_connessione_async()

    def _centra_finestra(self, parent):
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = 680
        h = 740
        x = max(0, px + (pw - w) // 2)
        y = max(0, py + (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # Header Dark Studio
        header = tk.Frame(self, bg=BG_DARKEST, height=66, highlightbackground=BORDER_COLOR, highlightthickness=1)
        header.pack(fill="x", side="top")

        hdr_content = tk.Frame(header, bg=BG_DARKEST)
        hdr_content.pack(fill="both", expand=True, padx=22, pady=14)

        lbl_icon = tk.Label(hdr_content, text="🚀", bg=BG_DARKEST, font=("Helvetica", 22))
        lbl_icon.pack(side="left", padx=(0, 14))

        txt_frame = tk.Frame(hdr_content, bg=BG_DARKEST)
        txt_frame.pack(side="left", fill="both")

        lbl_title = tk.Label(
            txt_frame,
            text="TRASMISSIONE COMMESSA AL LABORATORIO",
            bg=BG_DARKEST,
            fg="#FFFFFF",
            font=("Helvetica", 12, "bold")
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            txt_frame,
            text="Upload automatico delle foto a 300 DPI e delle specifiche dell'album",
            bg=BG_DARKEST,
            fg=TEXT_MUTED,
            font=("Helvetica", 9)
        )
        lbl_sub.pack(anchor="w", pady=(3, 0))

        # Main Container
        container = tk.Frame(self, bg=BG_APP, padx=22, pady=18)
        container.pack(fill="both", expand=True)

        # 1. Sezione Connessione Server
        sec_conn = tk.LabelFrame(
            container,
            text="  INDIRIZZO SERVER LABORATORIO  ",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=("Helvetica", 9, "bold"),
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=14,
            pady=12
        )
        sec_conn.pack(fill="x", pady=(0, 14))

        srv_row = tk.Frame(sec_conn, bg=BG_CARD)
        srv_row.pack(fill="x")

        saved_url = self.config_mgr.get("server_url", "http://localhost:5050")
        self.var_url = tk.StringVar(value=saved_url)

        self.entry_url = tk.Entry(
            srv_row,
            textvariable=self.var_url,
            bg=BG_DARKEST,
            fg=TEXT_PRIMARY,
            insertbackground="#FFFFFF",
            font=("Helvetica", 10),
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=PRIMARY
        )
        self.entry_url.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))

        btn_test = ttk.Button(srv_row, text="🔍 Test Connessione", command=self._test_connessione_async)
        btn_test.pack(side="right")

        self.lbl_conn_status = tk.Label(
            sec_conn,
            text="Verifica raggiungibilità in corso...",
            bg=BG_CARD,
            fg=WARNING,
            font=("Helvetica", 9)
        )
        self.lbl_conn_status.pack(anchor="w", pady=(8, 0))

        # 2. Sezione Riepilogo Ordine
        sec_info = tk.LabelFrame(
            container,
            text="  RIEPILOGO COMMESSA  ",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=("Helvetica", 9, "bold"),
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=14,
            pady=12
        )
        sec_info.pack(fill="x", pady=(0, 14))

        grid = tk.Frame(sec_info, bg=BG_CARD)
        grid.pack(fill="x")

        def add_info_row(r, label, value, color="#FFFFFF", bold=False):
            lbl_l = tk.Label(grid, text=label, bg=BG_CARD, fg=TEXT_MUTED, font=("Helvetica", 9))
            lbl_l.grid(row=r, column=0, sticky="w", pady=3)
            f_weight = "bold" if bold else "normal"
            lbl_v = tk.Label(grid, text=value, bg=BG_CARD, fg=color, font=("Helvetica", 10, f_weight))
            lbl_v.grid(row=r, column=1, sticky="w", padx=(12, 0), pady=3)

        tot_copie = sum(f.quantita for f in self.foto_list)
        busta = self.order_data.get("num_busta", "—")
        cliente = f"{self.order_data.get('nome_cliente', '—')} (Cod. {self.order_data.get('codice_cliente', '—')})"
        modello = self.order_data.get("modello_nome") or "Stampe Libere"
        formato = self.order_data.get("formato") or "—"
        materiale = self.order_data.get("materiale") or "—"
        sposi = self.order_data.get("nomi_sposi") or "—"

        add_info_row(0, "Busta N°:", str(busta), bold=True)
        add_info_row(1, "Committente:", cliente)
        add_info_row(2, "Modello Album:", modello, color="#66B2FF", bold=True)
        add_info_row(3, "Formato & Copertina:", f"{formato}  |  {materiale}")
        if sposi != "—":
            add_info_row(4, "Incisione Sposi:", sposi, color="#F1C40F")
        add_info_row(5, "Scatti & Risoluzione:", f"{len(self.foto_list)} foto ({tot_copie} copie) a 300 DPI con ICC", color=SUCCESS)

        # 3. Sezione Avanzamento / Progress
        self.sec_progress = tk.LabelFrame(
            container,
            text="  STATO AVANZAMENTO  ",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=("Helvetica", 8, "bold"),
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=12,
            pady=10
        )
        self.sec_progress.pack(fill="x", pady=(0, 12))

        self.lbl_progress_status = tk.Label(
            self.sec_progress,
            text="Pronto per iniziare la trasmissione...",
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            font=("Helvetica", 9)
        )
        self.lbl_progress_status.pack(anchor="w", pady=(0, 6))

        self.progress_bar = ttk.Progressbar(self.sec_progress, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", ipady=2)
        self.progress_bar["value"] = 0

        # Card di successo (inizialmente nascosta)
        self.success_frame = tk.Frame(container, bg="#1A3326", highlightbackground=SUCCESS, highlightthickness=1, padx=12, pady=10)
        
        lbl_succ_title = tk.Label(
            self.success_frame,
            text="✅ ORDINE TRASMESSO CON SUCCESSO AL LABORATORIO!",
            bg="#1A3326",
            fg="#6EE7B7",
            font=("Helvetica", 9, "bold")
        )
        lbl_succ_title.pack(anchor="w")

        self.lbl_order_id_succ = tk.Label(
            self.success_frame,
            text="Codice Commessa Assegnato: ORD-...",
            bg="#1A3326",
            fg="#FFFFFF",
            font=("Helvetica", 9)
        )
        self.lbl_order_id_succ.pack(anchor="w", pady=(4, 6))

        btn_open_web = tk.Button(
            self.success_frame,
            text="🌐 Apri Dashboard Web Laboratorio",
            bg=PRIMARY,
            fg="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self._apri_dashboard_web
        )
        btn_open_web.pack(anchor="w")

        # Bottom Bar: Pulsanti di Azione
        btn_bar = tk.Frame(self, bg=BG_APP, height=54, highlightbackground=BORDER_COLOR, highlightthickness=1)
        btn_bar.pack(fill="x", side="bottom")

        btn_box = tk.Frame(btn_bar, bg=BG_APP)
        btn_box.pack(side="right", padx=16, pady=10)

        self.btn_cancel = ttk.Button(btn_box, text="Annulla", style="TButton", command=self._on_close)
        self.btn_cancel.pack(side="right", padx=(8, 0))

        self.btn_send = ttk.Button(
            btn_box,
            text="🚀 Invia Commessa Adesso",
            style="Primary.TButton",
            command=self._avvia_invio
        )
        self.btn_send.pack(side="right")

    # -------------------------------------------------------------------------
    # Connessione e Test
    # -------------------------------------------------------------------------
    def _test_connessione_async(self):
        url = self.var_url.get().strip()
        self.lbl_conn_status.config(text="Verifica connessione al server in corso...", fg=WARNING)

        def worker():
            ok, msg = check_server_status(url)
            self.after(0, lambda: self._update_conn_ui(ok, msg, url))

        threading.Thread(target=worker, daemon=True).start()

    def _update_conn_ui(self, ok: bool, msg: str, url: str):
        if ok:
            self.lbl_conn_status.config(text=f"🟢 {msg}", fg=SUCCESS)
            self.config_mgr.set("server_url", url)
        else:
            self.lbl_conn_status.config(text=f"🔴 {msg}", fg=DANGER)

    # -------------------------------------------------------------------------
    # Invio Ordine in Background
    # -------------------------------------------------------------------------
    def _avvia_invio(self):
        server_url = self.var_url.get().strip()
        if not server_url:
            messagebox.showwarning("Attenzione", "Inserisci l'URL del server del laboratorio.")
            return

        # Disabilita controlli durante l'invio
        self.btn_send.config(state="disabled")
        self.entry_url.config(state="disabled")
        self.btn_cancel.config(text="Interrompi Upload")
        self.cancel_event.clear()

        self.lbl_progress_status.config(text="Avvio esportazione file a 300 DPI...", fg=TEXT_PRIMARY)
        self.progress_bar["value"] = 5

        def worker():
            def cb(fase, pct, bytes_read, tot_bytes):
                self.after(0, lambda: self._on_progress_update(fase, pct))

            ok, res = OrderUploader.upload_order(
                server_url=server_url,
                order_data=self.order_data,
                foto_list=self.foto_list,
                config=self.config_mgr.data,
                progress_callback=cb,
                cancel_event=self.cancel_event
            )

            self.after(0, lambda: self._on_upload_complete(ok, res))

        self.upload_thread = threading.Thread(target=worker, daemon=True)
        self.upload_thread.start()

    def _on_progress_update(self, fase_testo: str, pct: float):
        self.lbl_progress_status.config(text=fase_testo)
        self.progress_bar["value"] = pct

    def _on_upload_complete(self, ok: bool, res: dict):
        if ok:
            order_id = res.get("order_id", "N/D")
            self.completed_order_id = order_id
            self.progress_bar["value"] = 100
            self.lbl_progress_status.config(text="Trasmissione completata con successo!", fg=SUCCESS)

            # Mostra card di successo
            self.lbl_order_id_succ.config(text=f"Codice Commessa Assegnato: {order_id}")
            self.success_frame.pack(fill="x", pady=(0, 12))

            self.btn_send.pack_forget()
            self.btn_cancel.config(text="Chiudi", style="Primary.TButton")

            # Callback al main window
            if self.on_success_callback:
                self.on_success_callback(order_id)
        else:
            self.btn_send.config(state="normal")
            self.entry_url.config(state="normal")
            self.btn_cancel.config(text="Chiudi")
            err = res.get("error", "Errore sconosciuto durante la trasmissione.")
            self.lbl_progress_status.config(text=f"Errore: {err}", fg=DANGER)
            messagebox.showerror("Errore Trasmissione", f"Impossibile inviare l'ordine:\n\n{err}")

    def _apri_dashboard_web(self):
        url = self.var_url.get().strip().rstrip("/")
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"http://{url}"
        webbrowser.open(f"{url}/admin")

    def _on_close(self):
        if self.upload_thread and self.upload_thread.is_alive():
            conferma = messagebox.askyesno(
                "Interrompi Trasmissione",
                "Il caricamento è attualmente in corso. Vuoi davvero interromperlo?",
                icon="warning"
            )
            if conferma:
                self.cancel_event.set()
                self.destroy()
        else:
            self.destroy()
