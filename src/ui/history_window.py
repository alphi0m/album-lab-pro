"""
Finestra Storico Ordini & Stato Lavorazione in Tempo Reale per il Fotografo.
Permette allo studio fotografico di monitorare lo stato di avanzamento delle proprie commesse
(IN ATTESA, IN STAMPA, IN LEGATORIA, PRONTO) con autenticazione sicura tramite Codice Fotografo (3/4 cifre) e PIN.
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

from src.ui.theme import BG_APP, BG_CARD, PRIMARY, SUCCESS, ACCENT_AMBER, TEXT_PRIMARY, TEXT_MUTED, BORDER_COLOR
from src.core.config import open_folder, ARCHIVIO_DIR


class AuthStudioDialog(tk.Toplevel):
    """Dialogo modale per inserire o modificare il Codice Fotografo (3/4 cifre) e il PIN segreto."""

    def __init__(self, parent, config_mgr, on_success=None):
        super().__init__(parent)
        self.parent = parent
        self.config_mgr = config_mgr
        self.on_success = on_success
        self.success = False

        self.title("Accesso Studio Fotografico")
        self.geometry("450x380")
        self.resizable(False, False)
        self.configure(bg=BG_APP)
        self.transient(parent)
        self.grab_set()

        # Centra la finestra
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 380) // 2
        self.geometry(f"+{max(10, x)}+{max(10, y)}")

        self._init_ui()

    def _init_ui(self):
        pad = 20
        container = tk.Frame(self, bg=BG_APP, padx=pad, pady=pad)
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text="🔑 Identificazione Studio Fotografico",
            bg=BG_APP,
            fg=TEXT_PRIMARY,
            font=("Helvetica", 14, "bold")
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            container,
            text="Inserisci il tuo Codice Studio (3 o 4 cifre) e il PIN segreto\nrilasciati dal laboratorio per accedere ai tuoi ordini.",
            bg=BG_APP,
            fg=TEXT_MUTED,
            font=("Helvetica", 9),
            justify="left"
        ).pack(anchor="w", pady=(0, 16))

        card = tk.Frame(container, bg=BG_CARD, padx=14, pady=14, highlightbackground=BORDER_COLOR, highlightthickness=1)
        card.pack(fill="x", pady=(0, 14))

        # Codice Studio
        tk.Label(card, text="Codice Studio (es. 101):", bg=BG_CARD, fg=TEXT_PRIMARY, font=("Helvetica", 9, "bold")).pack(anchor="w", pady=(0, 3))
        self.entry_cod = ttk.Entry(card, font=("Helvetica", 11, "bold"))
        self.entry_cod.pack(fill="x", pady=(0, 10))
        self.entry_cod.insert(0, str(self.config_mgr.get("codice_cliente", "") or "101"))

        # PIN Segreto
        tk.Label(card, text="PIN Segreto di Sicurezza (4 cifre):", bg=BG_CARD, fg=TEXT_PRIMARY, font=("Helvetica", 9, "bold")).pack(anchor="w", pady=(0, 3))
        self.entry_pin = ttk.Entry(card, font=("Helvetica", 11, "bold"), show="•")
        self.entry_pin.pack(fill="x", pady=(0, 6))
        self.entry_pin.insert(0, str(self.config_mgr.get("pin_cliente", "") or "1234"))

        self.lbl_error = tk.Label(container, text="", bg=BG_APP, fg="#E74C3C", font=("Helvetica", 9, "bold"))
        self.lbl_error.pack(fill="x", pady=(0, 8))

        btn_box = tk.Frame(container, bg=BG_APP)
        btn_box.pack(fill="x", side="bottom")

        ttk.Button(btn_box, text="Annulla", style="TButton", command=self.destroy).pack(side="left")
        self.btn_login = ttk.Button(btn_box, text="✓ Verifica & Accedi", style="Primary.TButton", command=self._verifica)
        self.btn_login.pack(side="right")

    def _verifica(self):
        cod = self.entry_cod.get().strip()
        pin = self.entry_pin.get().strip()

        if not cod or not pin:
            self.lbl_error.config(text="⚠️ Compila sia il Codice Studio che il PIN.")
            return

        server_url = self.config_mgr.get("server_url", "http://localhost:5050").rstrip("/")
        self.lbl_error.config(text="Verifica in corso...", fg=ACCENT_AMBER)
        self.update_idletasks()

        try:
            req_data = json.dumps({"codice": cod, "pin": pin}).encode("utf-8")
            req = urllib.request.Request(
                f"{server_url}/api/auth/verify",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if data and data.get("success"):
                self.config_mgr.set("codice_cliente", cod)
                self.config_mgr.set("pin_cliente", pin)
                self.config_mgr.set("nome_studio", data.get("nome_studio", f"Studio {cod}"))
                self.success = True
                self.destroy()
                if self.on_success:
                    self.on_success()
            else:
                self.lbl_error.config(text="❌ Codice o PIN errati. Verifica con il laboratorio.", fg="#E74C3C")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.lbl_error.config(text="❌ Accesso negato: PIN fotografo errato.", fg="#E74C3C")
            else:
                self.lbl_error.config(text=f"❌ Errore server ({e.code})", fg="#E74C3C")
        except Exception as e:
            # Se il server è temporaneamente offline, salviamo in locale con avviso
            self.config_mgr.set("codice_cliente", cod)
            self.config_mgr.set("pin_cliente", pin)
            messagebox.showwarning(
                "Modalità Offline",
                f"Impossibile contattare il server ({e}).\nCodice salvato in locale per visualizzare le commesse memorizzate."
            )
            self.success = True
            self.destroy()
            if self.on_success:
                self.on_success()


class StoricoOrdiniWindow(tk.Toplevel):
    """Finestra Dark Studio per la consultazione dello storico commesse e stato avanzamento."""

    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.parent = parent
        self.main_app = main_app
        self.config_mgr = main_app.config_mgr

        self.title("I Miei Ordini — Storico & Avanzamento Lavorazioni")
        self.geometry("980x600")
        self.minsize(800, 480)
        self.configure(bg=BG_APP)
        self.transient(parent)

        self._ordini_caricati = []
        self._init_ui()

        # Verifica subito credenziali
        codice = self.config_mgr.get("codice_cliente", "")
        pin = self.config_mgr.get("pin_cliente", "")
        if not codice or not pin:
            self.after(100, self._richiedi_login)
        else:
            self.after(100, self.aggiorna_ordini)

    def _init_ui(self):
        # ---------------- 1. Header con Branding e Info Studio ----------------
        header = tk.Frame(self, bg=BG_CARD, height=60, highlightbackground=BORDER_COLOR, highlightthickness=1)
        header.pack(fill="x", side="top")

        left_hdr = tk.Frame(header, bg=BG_CARD)
        left_hdr.pack(side="left", padx=16, pady=10)

        self.lbl_title = tk.Label(
            left_hdr,
            text="📦 I Miei Ordini & Stato Lavorazione",
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            font=("Helvetica", 13, "bold")
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_studio = tk.Label(
            left_hdr,
            text="Studio: — | Codice: —",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=("Helvetica", 9)
        )
        self.lbl_studio.pack(anchor="w")

        right_hdr = tk.Frame(header, bg=BG_CARD)
        right_hdr.pack(side="right", padx=16, pady=10)

        self.btn_refresh = ttk.Button(
            right_hdr,
            text="🔄 Aggiorna Stato Live",
            style="Primary.TButton",
            command=self.aggiorna_ordini
        )
        self.btn_refresh.pack(side="left", padx=(0, 8))

        self.btn_auth = ttk.Button(
            right_hdr,
            text="🔑 Codice / PIN",
            style="TButton",
            command=self._richiedi_login
        )
        self.btn_auth.pack(side="left")

        # ---------------- 2. Tabella Ordini ----------------
        table_frame = tk.Frame(self, bg=BG_APP, padx=12, pady=10)
        table_frame.pack(fill="both", expand=True)

        columns = ("order_id", "busta", "data", "servizio", "dettagli", "foto", "bordino", "stato")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("order_id", text="ID Commessa")
        self.tree.heading("busta", text="Busta N°")
        self.tree.heading("data", text="Data Invio")
        self.tree.heading("servizio", text="Tipo Servizio")
        self.tree.heading("dettagli", text="Specifiche / Sposi")
        self.tree.heading("foto", text="Foto")
        self.tree.heading("bordino", text="Bordino")
        self.tree.heading("stato", text="Stato Lavorazione")

        self.tree.column("order_id", width=140, anchor="w")
        self.tree.column("busta", width=65, anchor="center")
        self.tree.column("data", width=125, anchor="center")
        self.tree.column("servizio", width=130, anchor="w")
        self.tree.column("dettagli", width=180, anchor="w")
        self.tree.column("foto", width=65, anchor="center")
        self.tree.column("bordino", width=75, anchor="center")
        self.tree.column("stato", width=130, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        # ---------------- 3. Barra di Stato & Azioni Inferiori ----------------
        bottom_bar = tk.Frame(self, bg=BG_CARD, height=44, highlightbackground=BORDER_COLOR, highlightthickness=1)
        bottom_bar.pack(fill="x", side="bottom")

        self.lbl_stats = tk.Label(
            bottom_bar,
            text="Caricamento commesse...",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=("Helvetica", 9)
        )
        self.lbl_stats.pack(side="left", padx=16, pady=8)

        btn_box = tk.Frame(bottom_bar, bg=BG_CARD)
        btn_box.pack(side="right", padx=16, pady=8)

        ttk.Button(
            btn_box,
            text="📂 Apri Cartella Locale",
            style="TButton",
            command=self._apri_cartella_locale
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            btn_box,
            text="Chiudi",
            style="TButton",
            command=self.destroy
        ).pack(side="left")

    def _richiedi_login(self):
        AuthStudioDialog(self, self.config_mgr, on_success=self._on_login_success)

    def _on_login_success(self):
        if self.main_app and hasattr(self.main_app, "info_panel"):
            cod = self.config_mgr.get("codice_cliente", "")
            nome = self.config_mgr.get("nome_studio", "")
            if cod:
                self.main_app.info_panel.codice_cliente_var.set(cod)
            if nome and not self.main_app.info_panel.nome_cliente_var.get().strip():
                self.main_app.info_panel.nome_cliente_var.set(nome)
        self.aggiorna_ordini()

    def aggiorna_ordini(self):
        """Scarica lo stato degli ordini dal server per lo studio autenticato."""
        cod = str(self.config_mgr.get("codice_cliente", "")).strip()
        pin = str(self.config_mgr.get("pin_cliente", "")).strip()
        nome = self.config_mgr.get("nome_studio", f"Studio {cod}")

        self.lbl_studio.config(text=f"Studio: {nome}  |  Codice Fotografo: #{cod}")
        self.lbl_stats.config(text="Connessione al laboratorio in corso...", fg=ACCENT_AMBER)
        self.update_idletasks()

        server_url = self.config_mgr.get("server_url", "http://localhost:5050").rstrip("/")
        ordini = []
        is_live = False

        if cod and pin:
            try:
                params = urllib.parse.urlencode({"codice": cod, "pin": pin})
                url = f"{server_url}/api/orders/history?{params}"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    if res_data.get("success"):
                        ordini = res_data.get("ordini", [])
                        is_live = True
                        if res_data.get("studio"):
                            self.lbl_studio.config(text=f"Studio: {res_data['studio']}  |  Codice: #{cod}")
            except Exception as e:
                print(f"Info: Server remoto non raggiungibile ({e}). Consulto archivio locale...")

        # Se non trovati online o server offline, cerca nell'archivio locale
        if not is_live and ARCHIVIO_DIR.exists():
            for folder in ARCHIVIO_DIR.iterdir():
                if folder.is_dir() and folder.name.startswith("ordine_"):
                    j_path = folder / "ordine.json"
                    if j_path.exists():
                        try:
                            with open(j_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                # Filtra per codice se impostato
                                if not cod or str(data.get("codice_cliente", "")).strip() == cod:
                                    ordini.append({
                                        "order_id": folder.name,
                                        "num_busta": data.get("num_busta", ""),
                                        "data_ricezione": data.get("data", ""),
                                        "tipo_servizio": data.get("tipo_servizio", ""),
                                        "modello_nome": data.get("modello_nome", ""),
                                        "nomi_sposi": data.get("nomi_sposi", ""),
                                        "totale_file": data.get("totale_foto", 0),
                                        "bordino_bianco": data.get("bordino_bianco", False),
                                        "stato": data.get("stato", "SALVATO LOCALE"),
                                        "_local_path": str(folder)
                                    })
                        except Exception:
                            pass

        self._ordini_caricati = ordini
        self._riempi_tabella(ordini, is_live)

    def _riempi_tabella(self, ordini: list, is_live: bool):
        for item in self.tree.get_children():
            self.tree.delete(item)

        stati_count = {"IN ATTESA": 0, "IN STAMPA": 0, "IN LEGATORIA": 0, "PRONTO": 0}

        for o in ordini:
            oid = o.get("order_id", "—")
            busta = str(o.get("num_busta", "—"))
            data_r = o.get("data_ricezione", "")[:16]

            # Servizio
            srv = o.get("tipo_servizio", "")
            if srv == "STAMPE_FOTO" or o.get("modello_id") == "stampe_singole":
                servizio_fmt = "🖼️ Stampe Singole"
                dettagli = f"Formato: {o.get('formato_globale', '—')} ({o.get('materiale_globale', 'Lucida')})"
            else:
                servizio_fmt = f"📖 {o.get('modello_nome', 'Stampa Album')}"
                sposi = o.get("nomi_sposi")
                dettagli = f"💍 Sposi: {sposi}" if sposi else f"Formato: {o.get('formato_globale', '—')}"

            tot_foto = f"{o.get('totale_file', 0)} foto"
            bordino = "⚪ 3 mm" if o.get("bordino_bianco") else "—"

            stato_raw = str(o.get("stato", "IN ATTESA")).upper()
            if stato_raw in stati_count:
                stati_count[stato_raw] += 1

            if "PRONTO" in stato_raw:
                stato_badge = "🟢 PRONTO / SPEDITO"
            elif "LEGATORIA" in stato_raw:
                stato_badge = "🟣 IN LEGATORIA"
            elif "STAMPA" in stato_raw:
                stato_badge = "🔵 IN STAMPA"
            else:
                stato_badge = "🟡 IN ATTESA"

            self.tree.insert("", "end", values=(oid, busta, data_r, servizio_fmt, dettagli, tot_foto, bordino, stato_badge))

        conn_str = "✓ Sincronizzato con il Laboratorio" if is_live else "⚠️ Visualizzazione Locale (Offline)"
        tot = len(ordini)
        attesa = stati_count["IN ATTESA"]
        stampa = stati_count["IN STAMPA"]
        pronti = stati_count["PRONTO"]

        self.lbl_stats.config(
            text=f"{conn_str}  |  Totale: {tot} ordini  (🟡 In attesa: {attesa}  •  🔵 In stampa: {stampa}  •  🟢 Pronti: {pronti})",
            fg=SUCCESS if is_live else TEXT_MUTED
        )

    def _apri_cartella_locale(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Seleziona Ordine", "Seleziona prima una commessa dalla tabella.")
            return

        item = self.tree.item(sel[0])
        vals = item.get("values", [])
        if vals:
            busta = str(vals[1]).strip()
            cand1 = ARCHIVIO_DIR / f"ordine_{busta}"
            cand2 = ARCHIVIO_DIR / f"ordine_{int(busta):03d}" if busta.isdigit() else None
            if cand1.exists():
                open_folder(cand1)
            elif cand2 and cand2.exists():
                open_folder(cand2)
            elif ARCHIVIO_DIR.exists():
                open_folder(ARCHIVIO_DIR)
            else:
                messagebox.showwarning("Cartella Non Trovata", "La cartella locale di questa commessa non è presente sul disco.")
