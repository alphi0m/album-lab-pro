"""
Finestra principale dell'applicazione Album Lab Pro con integrazione catalogo visuale e vincoli dinamici.
"""

import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from src.core.constants import FORMATI, FILETYPES_FOTO, BASE_DIR, MODO_ALBUM, MODO_STAMPE
from src.core.config import ConfigManager, open_folder
from src.core.models import FotoItem
from src.core.catalog import MODELLI_ALBUM, get_modello_by_id
from src.core.exporter import OrderExporter
from src.ui.theme import (
    apply_dark_studio_theme, BG_APP, BG_CARD, PRIMARY, TEXT_PRIMARY, TEXT_MUTED, BORDER_COLOR
)
from src.ui.editor import EditorPanel
from src.ui.thumbnails import MiniaturePanel
from src.ui.panels import ModelloPanel, FormatiPanel, MaterialiPanel, InfoOrdinePanel
from src.ui.catalog_dialog import CatalogGalleryWindow
from src.ui.upload_dialog import UploadDialog


class MainApp:
    """Applicazione Desktop Principale Album Lab Pro — Studio Edition."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Album Lab Pro — Studio Edition")
        self.root.geometry("1420x880")
        self.root.minsize(1120, 720)

        self.config_mgr = ConfigManager()

        self.foto_list = []
        self.foto_corrente_index = None
        self.modello_selezionato = None
        self.modalita = MODO_ALBUM

        # Applica il tema Dark Studio
        apply_dark_studio_theme(self.root)

        # Imposta l'icona applicazione
        self._imposta_icona()

        # Costruzione Interfaccia
        self._crea_menu_bar()
        self._crea_header_branding()
        self._crea_top_toolbar()
        self._crea_layout_principale()

        # Registrazione scorciatoie
        self._registra_scorciatoie()
        self._setup_mousewheel()

    # -------------------------------------------------------------------------
    # Icona Applicazione
    # -------------------------------------------------------------------------
    def _imposta_icona(self):
        icon_path = BASE_DIR / "assets" / "icon.png"
        if icon_path.exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(icon_path).resize((64, 64), Image.Resampling.LANCZOS)
                self._app_icon_tk = ImageTk.PhotoImage(img)
                self.root.iconphoto(False, self._app_icon_tk)
            except Exception as e:
                print(f"Nota: impossibile impostare l'icona della finestra: {e}")

    # -------------------------------------------------------------------------
    # Header & Toolbar Dark
    # -------------------------------------------------------------------------
    def _crea_header_branding(self):
        header = tk.Frame(self.root, bg=BG_APP, height=46, highlightbackground=BORDER_COLOR, highlightthickness=1)
        header.pack(fill="x", side="top")

        brand_frame = tk.Frame(header, bg=BG_APP)
        brand_frame.pack(side="left", padx=16, pady=7)

        lbl_logo = tk.Label(
            brand_frame,
            text="ALBUM LAB",
            bg=BG_APP,
            fg="#FFFFFF",
            font=("Helvetica", 13, "bold")
        )
        lbl_logo.pack(side="left")

        lbl_badge = tk.Label(
            brand_frame,
            text="PRO",
            bg=PRIMARY,
            fg="#FFFFFF",
            font=("Helvetica", 9, "bold"),
            padx=7,
            pady=2
        )
        lbl_badge.pack(side="left", padx=(7, 0))

        self.lbl_stats = tk.Label(
            header,
            text="Nessun modello album selezionato   |   0 foto caricate",
            bg=BG_APP,
            fg=TEXT_MUTED,
            font=("Helvetica", 10)
        )
        self.lbl_stats.pack(side="right", padx=18, pady=9)

    def _crea_top_toolbar(self):
        toolbar = tk.Frame(self.root, bg="#1E2025", height=50, highlightbackground=BORDER_COLOR, highlightthickness=1)
        toolbar.pack(fill="x", side="top")

        # Selettore Modalità di Lavoro Duale (Segmented Control Studio)
        mode_box = tk.Frame(toolbar, bg="#141518", highlightbackground=BORDER_COLOR, highlightthickness=1)
        mode_box.pack(side="left", padx=(10, 8), pady=6)

        self.btn_modo_album = ttk.Button(
            mode_box,
            text="📖 Stampa Album",
            style="Primary.TButton",
            command=lambda: self.imposta_modalita(MODO_ALBUM)
        )
        self.btn_modo_album.pack(side="left", padx=2, pady=2)

        self.btn_modo_stampe = ttk.Button(
            mode_box,
            text="🖼️ Stampe Singole",
            style="TButton",
            command=lambda: self.imposta_modalita(MODO_STAMPE)
        )
        self.btn_modo_stampe.pack(side="left", padx=2, pady=2)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6, pady=8)

        # Pulsanti Toolbar con accesso al Catalogo
        self.btn_catalogo = ttk.Button(
            toolbar, text="📖 Sfoglia Catalogo", style="TButton",
            command=self.apri_catalogo
        )
        self.btn_catalogo.pack(side="left", padx=4, pady=6)

        ttk.Button(toolbar, text="📂 Carica Foto (Ctrl+O)", style="TButton",
                   command=self.carica_foto_multiple).pack(side="left", padx=4, pady=6)

        ttk.Button(toolbar, text="🔄 Ruota Crop (R)", style="TButton",
                   command=self.flip_crop).pack(side="left", padx=4, pady=6)

        ttk.Button(toolbar, text="🗑️ Rimuovi Foto", style="TButton",
                   command=self.cancella_foto_selezionate).pack(side="left", padx=4, pady=6)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=8, pady=8)

        ttk.Button(toolbar, text="✨ Nuovo Ordine", style="TButton",
                   command=self.nuovo_ordine).pack(side="left", padx=4, pady=6)

        # Pulsanti Azione Ordine a destra
        ttk.Button(toolbar, text="🚀 INVIA AL LABORATORIO", style="Primary.TButton",
                   command=self.invia_al_laboratorio).pack(side="right", padx=(4, 12), pady=6)

        ttk.Button(toolbar, text="💾 Salva Locale (Ctrl+S)", style="Success.TButton",
                   command=self.salva_ordine).pack(side="right", padx=4, pady=6)

    def imposta_modalita(self, modalita: str):
        """Commuta la modalità di lavoro tra 'Stampa Album' e 'Stampe Singole'."""
        self.modalita = modalita
        if modalita == MODO_STAMPE:
            self.btn_modo_stampe.config(style="Primary.TButton")
            self.btn_modo_album.config(style="TButton")
            self.btn_catalogo.config(state="disabled")
        else:
            self.btn_modo_album.config(style="Primary.TButton")
            self.btn_modo_stampe.config(style="TButton")
            self.btn_catalogo.config(state="normal")

        # Propaga la modalità ai pannelli laterali
        self.modello_panel.set_modalita(modalita)
        self.formati_panel.set_modalita(modalita)
        self.materiali_panel.set_modalita(modalita)
        self.info_panel.set_modalita(modalita)

        self._aggiorna_stats()

    def _crea_menu_bar(self):
        menubar = tk.Menu(self.root)

        menu_file = tk.Menu(menubar, tearoff=0)
        menu_file.add_command(label="Modalità: 📖 Stampa Album", command=lambda: self.imposta_modalita(MODO_ALBUM))
        menu_file.add_command(label="Modalità: 🖼️ Stampe Singole", command=lambda: self.imposta_modalita(MODO_STAMPE))
        menu_file.add_separator()
        menu_file.add_command(label="Sfoglia Catalogo Album...", command=self.apri_catalogo)
        menu_file.add_command(label="Carica Foto... (Ctrl+O)", command=self.carica_foto_multiple)
        menu_file.add_separator()
        menu_file.add_command(label="🚀 Invia al Laboratorio...", command=self.invia_al_laboratorio)
        menu_file.add_command(label="💾 Salva Locale (Ctrl+S)", command=self.salva_ordine)
        menu_file.add_separator()
        menu_file.add_command(label="Nuovo Ordine / Reset", command=self.nuovo_ordine)
        menu_file.add_separator()
        menu_file.add_command(label="Esci", command=self.root.quit)
        menubar.add_cascade(label="File", menu=menu_file)

        menu_edit = tk.Menu(menubar, tearoff=0)
        menu_edit.add_command(label="Inverti Orientamento Ritaglio (Spazio / R)", command=self.flip_crop)
        menu_edit.add_command(label="+1 Copia (+)", command=lambda: self.modifica_quantita(1))
        menu_edit.add_command(label="-1 Copia (-)", command=lambda: self.modifica_quantita(-1))
        menu_edit.add_separator()
        menu_edit.add_command(label="Seleziona Tutto (Ctrl+A)", command=self.seleziona_tutto)
        menu_edit.add_command(label="Rimuovi Foto Selezionate (Canc)", command=self.cancella_foto_selezionate)
        menubar.add_cascade(label="Modifica", menu=menu_edit)

        menu_help = tk.Menu(menubar, tearoff=0)
        menu_help.add_command(label="Informazioni su Album Lab Pro", command=self._mostra_info)
        menubar.add_cascade(label="Aiuto", menu=menu_help)

        self.root.config(menu=menubar)

    def _crea_layout_principale(self):
        main_pane = ttk.PanedWindow(self.root, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=6, pady=6)

        # 1. Colonna Sinistra: Miniature
        left_frame = ttk.Frame(main_pane, width=320, style="Card.TFrame")
        self.miniature_panel = MiniaturePanel(left_frame, self)
        self.miniature_panel.pack(fill="both", expand=True)
        main_pane.add(left_frame, weight=1)

        # 2. Area Centrale: Editor Canvas
        center_frame = ttk.Frame(main_pane, style="Darkest.TFrame")
        self.editor_panel = EditorPanel(center_frame, self)
        self.editor_panel.pack(fill="both", expand=True)
        main_pane.add(center_frame, weight=3)

        # 3. Colonna Destra: Catalogo, Formati, Materiali e Dati Commessa (con scroll fluido)
        self.right_outer = ttk.Frame(main_pane, width=410, style="Card.TFrame")
        self.right_outer.pack_propagate(False)

        self.right_canvas = tk.Canvas(self.right_outer, bg=BG_APP, highlightthickness=0)
        self.right_scrollbar = ttk.Scrollbar(self.right_outer, orient="vertical", command=self.right_canvas.yview)
        self.right_canvas.configure(yscrollcommand=self.right_scrollbar.set)

        self.right_scrollbar.pack(side="right", fill="y")
        self.right_canvas.pack(side="left", fill="both", expand=True)

        self.right_content = ttk.Frame(self.right_canvas, style="Card.TFrame")
        self.right_window = self.right_canvas.create_window((0, 0), window=self.right_content, anchor="nw")

        def _on_right_content_configure(event):
            self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all"))

        def _on_right_canvas_configure(event):
            self.right_canvas.itemconfig(self.right_window, width=event.width)

        self.right_content.bind("<Configure>", _on_right_content_configure)
        self.right_canvas.bind("<Configure>", _on_right_canvas_configure)

        # Selettore Modello Album
        self.modello_panel = ModelloPanel(self.right_content, self)
        self.modello_panel.pack(fill="x", pady=4, padx=6)

        # Pannello Formati (vincolato al modello)
        self.formati_panel = FormatiPanel(self.right_content, self)
        self.formati_panel.pack(fill="x", pady=4, padx=6)

        # Pannello Materiali (campionari colore reali)
        self.materiali_panel = MaterialiPanel(self.right_content, self)
        self.materiali_panel.pack(fill="x", pady=4, padx=6)

        # Pannello Dati Commessa & Sposi
        self.info_panel = InfoOrdinePanel(self.right_content, self)
        self.info_panel.pack(fill="x", pady=4, padx=6)

        main_pane.add(self.right_outer, weight=1)

    # -------------------------------------------------------------------------
    # Selezione & Vincolo Catalogo
    # -------------------------------------------------------------------------
    def apri_catalogo(self):
        """Apre la galleria visuale di tutti i modelli del catalogo."""
        CatalogGalleryWindow(self.root, self.imposta_modello_scelto)

    def imposta_modello_scelto(self, modello: dict):
        """Propaga il modello selezionato a tutti i componenti dell'applicazione."""
        self.modello_selezionato = modello

        # Aggiorna pannelli laterali
        self.modello_panel.set_modello(modello)
        self.formati_panel.set_modello(modello)
        self.materiali_panel.set_modello(modello)
        self.info_panel.set_modello(modello)

        self._aggiorna_stats()

    # -------------------------------------------------------------------------
    # Scorciatoie da Banco
    # -------------------------------------------------------------------------
    def _is_text_focused(self) -> bool:
        """Verifica se l'utente sta scrivendo in un campo testo (note, nome, busta, ecc.)."""
        try:
            w = self.root.focus_get()
            if w is None:
                return False
            if isinstance(w, (tk.Text, tk.Entry, ttk.Entry)):
                return True
            cls_name = w.winfo_class().lower()
            return "text" in cls_name or "entry" in cls_name
        except Exception:
            return False

    def _safe_action(self, fn):
        """Esegue l'azione solo se il focus non è attualmente in un widget di testo."""
        if self._is_text_focused():
            return
        fn()

    def _registra_scorciatoie(self):
        self.root.bind("<Left>", lambda e: self._safe_action(self.prev_foto))
        self.root.bind("<Right>", lambda e: self._safe_action(self.next_foto))

        self.root.bind("<space>", lambda e: self._safe_action(self.flip_crop))
        self.root.bind("<r>", lambda e: self._safe_action(self.flip_crop))
        self.root.bind("<R>", lambda e: self._safe_action(self.flip_crop))

        self.root.bind("+", lambda e: self._safe_action(lambda: self.modifica_quantita(1)))
        self.root.bind("-", lambda e: self._safe_action(lambda: self.modifica_quantita(-1)))
        self.root.bind("<KP_Add>", lambda e: self._safe_action(lambda: self.modifica_quantita(1)))
        self.root.bind("<KP_Subtract>", lambda e: self._safe_action(lambda: self.modifica_quantita(-1)))

        self.root.bind("<Delete>", lambda e: self._safe_action(self.cancella_foto_selezionate))
        self.root.bind("<BackSpace>", lambda e: self._safe_action(self.cancella_foto_selezionate))

        ctrl = "Command" if sys.platform == "darwin" else "Control"
        self.root.bind(f"<{ctrl}-s>", lambda e: self.salva_ordine())
        self.root.bind(f"<{ctrl}-S>", lambda e: self.salva_ordine())
        self.root.bind(f"<{ctrl}-o>", lambda e: self._safe_action(self.carica_foto_multiple))
        self.root.bind(f"<{ctrl}-O>", lambda e: self._safe_action(self.carica_foto_multiple))
        self.root.bind(f"<{ctrl}-a>", lambda e: self._safe_action(self.seleziona_tutto))
        self.root.bind(f"<{ctrl}-A>", lambda e: self._safe_action(self.seleziona_tutto))

    def _setup_mousewheel(self):
        """Gestore unificato e fluido della rotellina del mouse senza conflitti enter/leave."""
        def _on_global_mousewheel(event):
            try:
                w = self.root.winfo_containing(event.x_root, event.y_root)
                if not w:
                    return

                # Se il mouse si trova dentro un'area di testo (es. Note), lasciamo lo scroll nativo del Text
                if isinstance(w, tk.Text):
                    return

                delta = 0
                if hasattr(event, "delta") and event.delta != 0:
                    delta = -1 if event.delta > 0 else 1
                elif event.num == 4:
                    delta = -1
                elif event.num == 5:
                    delta = 1

                if delta == 0:
                    return

                # Risali la gerarchia per identificare se il cursore è sulla colonna destra o sulle miniature
                curr = w
                is_right = False
                is_thumbs = False
                while curr:
                    if hasattr(self, "right_outer") and curr == self.right_outer:
                        is_right = True
                        break
                    if hasattr(self, "miniature_panel") and curr == self.miniature_panel:
                        is_thumbs = True
                        break
                    curr = getattr(curr, "master", None)

                if is_right and hasattr(self, "right_canvas"):
                    self.right_canvas.yview_scroll(delta * 2, "units")
                elif is_thumbs and hasattr(self, "miniature_panel"):
                    self.miniature_panel.canvas.yview_scroll(delta * 2, "units")
            except Exception:
                pass

        self.root.bind_all("<MouseWheel>", _on_global_mousewheel)
        self.root.bind_all("<Button-4>", _on_global_mousewheel)
        self.root.bind_all("<Button-5>", _on_global_mousewheel)

    # -------------------------------------------------------------------------
    # Formato e Ritaglio
    # -------------------------------------------------------------------------
    def get_crop_size(self) -> tuple[int, int]:
        formato_str = self.formati_panel.get_formato()
        base = formato_str.split(" ")[0].lower()
        if base in FORMATI:
            return FORMATI[base]
        if "x" in base:
            try:
                w, h = map(int, base.split("x"))
                return (w, h)
            except Exception:
                pass
        return (10, 15)

    def flip_crop(self):
        self.editor_panel.flip_crop_orientation()

    # -------------------------------------------------------------------------
    # Gestione Foto
    # -------------------------------------------------------------------------
    def carica_foto_multiple(self):
        filepaths = filedialog.askopenfilenames(
            title="Seleziona foto dell'ordine",
            filetypes=FILETYPES_FOTO
        )
        if not filepaths:
            return

        nuove_foto = []
        for path in filepaths:
            try:
                foto = FotoItem(path)
                nuove_foto.append(foto)
            except Exception as e:
                print(f"Errore caricamento {path}: {e}")

        if not nuove_foto:
            return

        self.foto_list.extend(nuove_foto)
        self.miniature_panel.set_foto_items(self.foto_list)

        if self.foto_corrente_index is None and self.foto_list:
            self.set_foto_corrente(0)
        else:
            self.miniature_panel.aggiorna_vista()

        self._aggiorna_stats()

    def set_foto_corrente(self, index: int):
        if not self.foto_list or index < 0 or index >= len(self.foto_list):
            return

        self.foto_corrente_index = index
        self.miniature_panel.active_index = index
        foto = self.foto_list[index]
        self.editor_panel.mostra_foto(foto)
        self.miniature_panel.aggiorna_evidenza()
        self._aggiorna_stats()

    def next_foto(self):
        if self.foto_corrente_index is not None and self.foto_corrente_index < len(self.foto_list) - 1:
            self.set_foto_corrente(self.foto_corrente_index + 1)

    def prev_foto(self):
        if self.foto_corrente_index is not None and self.foto_corrente_index > 0:
            self.set_foto_corrente(self.foto_corrente_index - 1)

    def modifica_quantita(self, delta: int):
        self.miniature_panel.modifica_quantita_selezionate(delta)
        self._aggiorna_stats()

    def seleziona_tutto(self):
        self.miniature_panel.seleziona_tutto()

    def cancella_foto_selezionate(self):
        if not self.foto_list:
            return

        target_indices = sorted(self.miniature_panel.selected_indices, reverse=True)
        if not target_indices and self.foto_corrente_index is not None:
            target_indices = [self.foto_corrente_index]

        if not target_indices:
            return

        for idx in target_indices:
            if 0 <= idx < len(self.foto_list):
                del self.foto_list[idx]

        self.miniature_panel.selected_indices.clear()

        if self.foto_list:
            new_idx = min(self.foto_corrente_index or 0, len(self.foto_list) - 1)
            self.set_foto_corrente(new_idx)
        else:
            self.foto_corrente_index = None
            self.editor_panel.clear()

        self.miniature_panel.set_foto_items(self.foto_list)
        self._aggiorna_stats()

    def _aggiorna_stats(self):
        tot_foto = len(self.foto_list)
        tot_copie = sum(f.quantita for f in self.foto_list)
        if self.modalita == MODO_STAMPE:
            self.lbl_stats.config(
                text=f"Modalità: Stampe Fotografiche Singole   |   {tot_foto} foto caricate   |   {tot_copie} stampe totali"
            )
        else:
            mod_nome = self.modello_selezionato["nome"] if self.modello_selezionato else "Nessun modello"
            self.lbl_stats.config(
                text=f"Stampa Album: {mod_nome}   |   {tot_foto} foto caricate   |   {tot_copie} copie totali"
            )

    # -------------------------------------------------------------------------
    # Salvataggio Ordine & Archivio
    # -------------------------------------------------------------------------
    def salva_ordine(self):
        if not self.foto_list:
            messagebox.showwarning("Attenzione", "Nessuna foto caricata nell'ordine!")
            return

        dati_commessa = self.info_panel.get_data()
        num_busta = dati_commessa["num_busta"]

        # Controllo conflitti numero busta prima del salvataggio
        if self.config_mgr.is_busta_in_conflitto(num_busta):
            prossimo = self.config_mgr.trova_prossimo_num_busta()
            risposta = messagebox.askyesnocancel(
                "Conflitto Numero Busta",
                f"La busta N° '{num_busta}' esiste già nell'archivio locale delle commesse.\n\n"
                f"Vuoi assegnare automaticamente il prossimo numero disponibile ({prossimo})?\n\n"
                f"• Clicca 'Sì' per usare la nuova busta N° {prossimo}\n"
                f"• Clicca 'No' per sovrascrivere la commessa archiviata\n"
                f"• Clicca 'Annulla' per correggere manualmente il numero"
            )
            if risposta is None:
                return  # Annulla l'operazione
            elif risposta is True:
                num_busta = str(prossimo)
                dati_commessa["num_busta"] = num_busta
                self.info_panel.num_busta_var.set(num_busta)

        dati_commessa["formato"] = self.formati_panel.get_formato()
        dati_commessa["materiale"] = self.materiali_panel.get_materiale()

        if self.modalita == MODO_STAMPE:
            dati_commessa["tipo_servizio"] = "STAMPE_FOTO"
            dati_commessa["modello_id"] = "stampe_singole"
            dati_commessa["modello_nome"] = "Stampe Fotografiche Singole"
            dati_commessa["modello_cofanetto"] = "Nessuno (Stampe Sciolte)"
        else:
            dati_commessa["tipo_servizio"] = "STAMPA_ALBUM"
            if self.modello_selezionato:
                dati_commessa["modello_id"] = self.modello_selezionato.get("id")
                dati_commessa["modello_nome"] = self.modello_selezionato.get("nome")
                dati_commessa["modello_cofanetto"] = self.modello_selezionato.get("cofanetto")
            else:
                dati_commessa["modello_id"] = ""
                dati_commessa["modello_nome"] = "Album Standard"
                dati_commessa["modello_cofanetto"] = ""

        self.config_mgr.set("codice_cliente", dati_commessa["codice_cliente"])

        ok, res_path = OrderExporter.salva_ordine(dati_commessa, self.foto_list, self.config_mgr.data)

        if ok:
            # Aggiorna progressivo in configurazione se numerico
            try:
                num_int = int(num_busta)
                if num_int >= self.config_mgr.get("ultimo_num_busta", 1):
                    self.config_mgr.set("ultimo_num_busta", num_int + 1)
            except ValueError:
                pass

            msg = f"Commessa Busta N° {num_busta} salvata con successo!\n\nCartella di produzione:\n{res_path}\n\nVuoi aprire la cartella dell'ordine adesso?"
            if messagebox.askyesno("Ordine Salvato", msg):
                open_folder(res_path)

            self.info_panel.reset_for_new_order()
        else:
            messagebox.showerror("Errore Salvataggio", f"Si è verificato un errore:\n{res_path}")

    def invia_al_laboratorio(self):
        """Apre la finestra di trasmissione remota al laboratorio fotografico."""
        if not self.foto_list:
            messagebox.showwarning("Nessuna Foto", "Carica almeno una foto prima di inviare l'ordine al laboratorio.")
            return

        dati_commessa = self.info_panel.get_data()
        num_busta = dati_commessa["num_busta"]

        # Controllo conflitti numero busta
        if self.config_mgr.is_busta_in_conflitto(num_busta):
            prossimo = self.config_mgr.trova_prossimo_num_busta()
            risposta = messagebox.askyesnocancel(
                "Conflitto Numero Busta",
                f"La busta N° '{num_busta}' esiste già nell'archivio ordini.\n\n"
                f"Vuoi assegnare automaticamente il prossimo numero disponibile ({prossimo})?\n\n"
                f"• Clicca 'Sì' per usare la busta N° {prossimo}\n"
                f"• Clicca 'No' per inviare comunque con questo numero\n"
                f"• Clicca 'Annulla' per correggere manualmente il numero"
            )
            if risposta is None:
                return
            elif risposta is True:
                num_busta = str(prossimo)
                dati_commessa["num_busta"] = num_busta
                self.info_panel.num_busta_var.set(num_busta)

        if self.modalita == MODO_STAMPE:
            dati_commessa["tipo_servizio"] = "STAMPE_FOTO"
            dati_commessa["modello_id"] = "stampe_singole"
            dati_commessa["modello_nome"] = "Stampe Fotografiche Singole"
            dati_commessa["modello_cofanetto"] = "Nessuno (Stampe Sciolte)"
        else:
            dati_commessa["tipo_servizio"] = "STAMPA_ALBUM"
            if not self.modello_selezionato:
                risposta = messagebox.askyesnocancel(
                    "Nessun Modello Album Selezionato",
                    "Sei in modalità 'Stampa Album' ma non hai scelto alcun modello dal catalogo.\n\n"
                    "• Clicca 'Sì' per aprire il catalogo e selezionare un modello\n"
                    "• Clicca 'No' per inviare la commessa come 'Stampe Fotografiche Singole'\n"
                    "• Clicca 'Annulla' per fermarti",
                    icon="question"
                )
                if risposta is None:
                    return
                elif risposta is True:
                    self.apri_catalogo()
                    return
                else:
                    self.imposta_modalita(MODO_STAMPE)
                    dati_commessa["tipo_servizio"] = "STAMPE_FOTO"
                    dati_commessa["modello_id"] = "stampe_singole"
                    dati_commessa["modello_nome"] = "Stampe Fotografiche Singole"
                    dati_commessa["modello_cofanetto"] = "Nessuno (Stampe Sciolte)"

            if self.modello_selezionato:
                dati_commessa["modello_id"] = self.modello_selezionato.get("id")
                dati_commessa["modello_nome"] = self.modello_selezionato.get("nome")
                dati_commessa["modello_cofanetto"] = self.modello_selezionato.get("cofanetto")

        dati_commessa["formato"] = self.formati_panel.get_formato()
        dati_commessa["materiale"] = self.materiali_panel.get_materiale()

        self.config_mgr.set("codice_cliente", dati_commessa["codice_cliente"])

        UploadDialog(
            parent=self.root,
            order_data=dati_commessa,
            foto_list=self.foto_list,
            on_success_callback=self._on_ordine_inviato
        )

    def _on_ordine_inviato(self, order_id: str):
        """Eseguito al termine dell'invio con successo al laboratorio."""
        try:
            curr_busta = int(self.info_panel.num_busta_var.get().strip())
            if curr_busta >= self.config_mgr.get("ultimo_num_busta", 1):
                self.config_mgr.set("ultimo_num_busta", curr_busta + 1)
        except ValueError:
            pass
        self.info_panel.reset_for_new_order()

    def nuovo_ordine(self):
        if self.foto_list or self.modello_selezionato:
            conferma = messagebox.askyesno(
                "Nuovo Ordine",
                "Vuoi svuotare la sessione attuale e iniziare un nuovo ordine?",
                icon="question"
            )
            if not conferma:
                return

        self.foto_list.clear()
        self.foto_corrente_index = None
        self.modello_selezionato = None
        self.editor_panel.clear()
        self.miniature_panel.set_foto_items([])
        self.imposta_modalita(self.modalita)
        self.info_panel.reset_for_new_order()
        self._aggiorna_stats()

    def _mostra_info(self):
        messagebox.showinfo(
            "Album Lab Pro",
            "Album Lab Pro — Studio Edition\nCatalogo Prodotti & Gestione Produzione Fotografica"
        )


def run_app():
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()
