"""
Finestra principale dell'applicazione Album Lab Pro con integrazione catalogo visuale e vincoli dinamici.
"""

import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from src.core.constants import FORMATI, FILETYPES_FOTO, BASE_DIR
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
from src.ui.archive import ArchivioOrdiniWindow
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

        # Pulsanti Toolbar con accesso rapido al Catalogo
        ttk.Button(toolbar, text="📖 Sfoglia Catalogo Album", style="Primary.TButton",
                   command=self.apri_catalogo).pack(side="left", padx=(10, 5), pady=6)

        ttk.Button(toolbar, text="📂 Carica Foto (Ctrl+O)", style="TButton",
                   command=self.carica_foto_multiple).pack(side="left", padx=5, pady=6)

        ttk.Button(toolbar, text="🔄 Ruota Crop (R)", style="TButton",
                   command=self.flip_crop).pack(side="left", padx=5, pady=6)

        ttk.Button(toolbar, text="🗑️ Rimuovi Foto", style="TButton",
                   command=self.cancella_foto_selezionate).pack(side="left", padx=5, pady=6)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=10, pady=8)

        ttk.Button(toolbar, text="📦 Archivio Ordini", style="TButton",
                   command=self.apri_archivio).pack(side="left", padx=5, pady=6)

        ttk.Button(toolbar, text="✨ Nuovo Ordine", style="TButton",
                   command=self.nuovo_ordine).pack(side="left", padx=5, pady=6)

        # Pulsanti Azione Ordine a destra
        ttk.Button(toolbar, text="🚀 INVIA AL LABORATORIO", style="Primary.TButton",
                   command=self.invia_al_laboratorio).pack(side="right", padx=(5, 12), pady=6)

        ttk.Button(toolbar, text="💾 Salva Locale (Ctrl+S)", style="Success.TButton",
                   command=self.salva_ordine).pack(side="right", padx=5, pady=6)

    def _crea_menu_bar(self):
        menubar = tk.Menu(self.root)

        menu_file = tk.Menu(menubar, tearoff=0)
        menu_file.add_command(label="Sfoglia Catalogo Album...", command=self.apri_catalogo)
        menu_file.add_command(label="Carica Foto... (Ctrl+O)", command=self.carica_foto_multiple)
        menu_file.add_separator()
        menu_file.add_command(label="🚀 Invia al Laboratorio...", command=self.invia_al_laboratorio)
        menu_file.add_command(label="💾 Salva Locale (Ctrl+S)", command=self.salva_ordine)
        menu_file.add_separator()
        menu_file.add_command(label="Archivio Ordini", command=self.apri_archivio)
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

        # 3. Colonna Destra: Catalogo, Formati, Materiali e Dati Commessa
        right_frame = ttk.Frame(main_pane, width=390, style="Card.TFrame")
        right_frame.pack_propagate(False)

        # Selettore Modello Album
        self.modello_panel = ModelloPanel(right_frame, self)
        self.modello_panel.pack(fill="x", pady=4, padx=6)

        # Pannello Formati (vincolato al modello)
        self.formati_panel = FormatiPanel(right_frame, self)
        self.formati_panel.pack(fill="x", pady=4, padx=6)

        # Pannello Materiali (campionari colore reali)
        self.materiali_panel = MaterialiPanel(right_frame, self)
        self.materiali_panel.pack(fill="x", pady=4, padx=6)

        # Pannello Dati Commessa & Sposi
        self.info_panel = InfoOrdinePanel(right_frame, self)
        self.info_panel.pack(fill="both", expand=True, pady=4, padx=6)

        main_pane.add(right_frame, weight=1)

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
    def _registra_scorciatoie(self):
        self.root.bind("<Left>", lambda e: self.prev_foto())
        self.root.bind("<Right>", lambda e: self.next_foto())

        self.root.bind("<space>", lambda e: self.flip_crop())
        self.root.bind("<r>", lambda e: self.flip_crop())
        self.root.bind("<R>", lambda e: self.flip_crop())

        self.root.bind("+", lambda e: self.modifica_quantita(1))
        self.root.bind("-", lambda e: self.modifica_quantita(-1))
        self.root.bind("<KP_Add>", lambda e: self.modifica_quantita(1))
        self.root.bind("<KP_Subtract>", lambda e: self.modifica_quantita(-1))

        self.root.bind("<Delete>", lambda e: self.cancella_foto_selezionate())
        self.root.bind("<BackSpace>", lambda e: self.cancella_foto_selezionate())

        ctrl = "Command" if sys.platform == "darwin" else "Control"
        self.root.bind(f"<{ctrl}-s>", lambda e: self.salva_ordine())
        self.root.bind(f"<{ctrl}-S>", lambda e: self.salva_ordine())
        self.root.bind(f"<{ctrl}-o>", lambda e: self.carica_foto_multiple())
        self.root.bind(f"<{ctrl}-O>", lambda e: self.carica_foto_multiple())
        self.root.bind(f"<{ctrl}-a>", lambda e: self.seleziona_tutto())
        self.root.bind(f"<{ctrl}-A>", lambda e: self.seleziona_tutto())

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
        mod_nome = self.modello_selezionato["nome"] if self.modello_selezionato else "Nessun modello"
        self.lbl_stats.config(text=f"Modello: {mod_nome}   |   {tot_foto} foto caricate   |   {tot_copie} copie totali")

    # -------------------------------------------------------------------------
    # Salvataggio Ordine & Archivio
    # -------------------------------------------------------------------------
    def salva_ordine(self):
        if not self.foto_list:
            messagebox.showwarning("Attenzione", "Nessuna foto caricata nell'ordine!")
            return

        dati_commessa = self.info_panel.get_data()
        dati_commessa["formato"] = self.formati_panel.get_formato()
        dati_commessa["materiale"] = self.materiali_panel.get_materiale()

        # Dati del catalogo
        if self.modello_selezionato:
            dati_commessa["modello_id"] = self.modello_selezionato.get("id")
            dati_commessa["modello_nome"] = self.modello_selezionato.get("nome")
            dati_commessa["modello_cofanetto"] = self.modello_selezionato.get("cofanetto")

        self.config_mgr.set("codice_cliente", dati_commessa["codice_cliente"])

        ok, res_path = OrderExporter.salva_ordine(dati_commessa, self.foto_list, self.config_mgr.data)

        if ok:
            num_busta = dati_commessa["num_busta"]
            msg = f"Ordine Busta {num_busta} salvato con successo!\n\nCartella di produzione:\n{res_path}\n\nVuoi aprire la cartella dell'ordine adesso?"
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

        if not self.modello_selezionato:
            conferma = messagebox.askyesno(
                "Nessun Modello Selezionato",
                "Non hai selezionato alcun modello di album dal catalogo.\n\nVuoi procedere comunque come stampe sciolte?",
                icon="question"
            )
            if not conferma:
                self.apri_catalogo()
                return

        dati_commessa = self.info_panel.get_data()
        dati_commessa["formato"] = self.formati_panel.get_formato()
        dati_commessa["materiale"] = self.materiali_panel.get_materiale()

        # Dati del catalogo
        if self.modello_selezionato:
            dati_commessa["modello_id"] = self.modello_selezionato.get("id")
            dati_commessa["modello_nome"] = self.modello_selezionato.get("nome")
            dati_commessa["modello_cofanetto"] = self.modello_selezionato.get("cofanetto")

        self.config_mgr.set("codice_cliente", dati_commessa["codice_cliente"])

        UploadDialog(
            parent=self.root,
            order_data=dati_commessa,
            foto_list=self.foto_list,
            on_success_callback=self._on_ordine_inviato
        )

    def _on_ordine_inviato(self, order_id: str):
        """Eseguito al termine dell'invio con successo al laboratorio."""
        self.info_panel.reset_for_new_order()

    def apri_archivio(self):
        try:
            ArchivioOrdiniWindow(self.root, self)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aprire l'archivio:\n{e}")

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
        self.modello_panel.set_modello(None)
        self.formati_panel.set_modello(None)
        self.materiali_panel.set_modello(None)
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
