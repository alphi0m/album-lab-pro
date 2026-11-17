"""
Pannelli di controllo Dark Studio con selezione dinamica del catalogo, formati vincolati e campionari colore reali.
"""

import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from src.core.constants import FORMATI, BASE_DIR
from src.core.catalog import MODELLI_ALBUM, CAMPIONARI_COLORI
from src.ui.theme import (
    BG_CARD, BG_INPUT, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_COLOR
)


# =============================================================================
# 1. Pannello Selezione Modello Album dal Catalogo
# =============================================================================
class ModelloPanel(ttk.LabelFrame):
    """Pannello in testata della colonna destra per visualizzare e scegliere il modello album."""

    def __init__(self, master, main_app):
        super().__init__(master, text="Modello Album (Catalogo)", padding=12)
        self.main_app = main_app
        self.modello_corrente = None
        self.thumb_tk = None

        # Riga con nome modello e tasto per sfogliare
        header_frame = tk.Frame(self, bg=BG_CARD)
        header_frame.pack(fill="x")

        self.lbl_nome = tk.Label(
            header_frame,
            text="Nessun modello (Stampe Sfuse)",
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            font=("Helvetica", 11, "bold"),
            anchor="w"
        )
        self.lbl_nome.pack(side="left", fill="x", expand=True)

        btn_browse = ttk.Button(
            header_frame,
            text="📖 Catalogo...",
            style="Primary.TButton",
            width=13,
            command=self.main_app.apri_catalogo
        )
        btn_browse.pack(side="right")

        # Dettagli del modello selezionato
        self.details_frame = tk.Frame(self, bg=BG_CARD)
        self.details_frame.pack(fill="x", pady=(8, 0))

        self.lbl_preview_img = tk.Label(self.details_frame, bg=BG_CARD)
        self.lbl_preview_img.pack(side="left", padx=(0, 10))

        self.lbl_desc = tk.Label(
            self.details_frame,
            text="Clicca su 'Catalogo...' per scegliere uno dei 18 modelli esclusivi.",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=("Helvetica", 9),
            wraplength=260,
            justify="left",
            anchor="w"
        )
        self.lbl_desc.pack(side="left", fill="both", expand=True)

    def set_modello(self, modello: dict | None):
        self.modello_corrente = modello
        if not modello:
            self.lbl_nome.config(text="Nessun modello (Stampe Sfuse)", fg=TEXT_PRIMARY)
            self.lbl_desc.config(text="Seleziona un modello per vincolare formati e campionari.")
            self.lbl_preview_img.config(image="")
            self.thumb_tk = None
            return

        self.lbl_nome.config(text=modello["nome"], fg=PRIMARY)
        self.lbl_desc.config(text=f"{modello['sottotitolo']}\nCofanetto: {modello['cofanetto']}")

        # Carica anteprima miniatura modello
        img_path = BASE_DIR / modello["immagine"]
        if img_path.exists():
            try:
                pil_img = Image.open(str(img_path))
                pil_img.thumbnail((86, 62), Image.Resampling.LANCZOS)
                self.thumb_tk = ImageTk.PhotoImage(pil_img)
                self.lbl_preview_img.config(image=self.thumb_tk)
            except Exception as e:
                print(f"Errore miniatura: {e}")
                self.lbl_preview_img.config(image="")
        else:
            self.lbl_preview_img.config(image="")


# =============================================================================
# 2. Pannello Formati di Stampa con Vincolo Dinamico al Modello
# =============================================================================
class FormatiPanel(ttk.LabelFrame):
    """Pannello formati: genera pillole dinamiche in base al modello selezionato."""

    DEFAULT_FORMATS = ["10x15", "13x18", "15x20", "20x30", "30x30", "30x40", "40x40"]

    def __init__(self, master, main_app):
        super().__init__(master, text="Formato di Stampa", padding=12)
        self.main_app = main_app

        self.formato_var = tk.StringVar(value="10x15")
        self.pill_buttons = {}

        # Contenitore per i pulsanti pillola
        self.pills_frame = ttk.Frame(self, style="Card.TFrame")
        self.pills_frame.pack(fill="x", pady=(0, 6))

        # Dropdown per formati secondari
        self.row_sel = ttk.Frame(self, style="Card.TFrame")
        self.row_sel.pack(fill="x", pady=(3, 6))

        ttk.Label(self.row_sel, text="Tutti i formati:", style="Card.TLabel").pack(side="left", padx=(0, 8))
        self.combo = ttk.Combobox(
            self.row_sel,
            textvariable=self.formato_var,
            values=list(FORMATI.keys()),
            state="readonly",
            width=13
        )
        self.combo.pack(side="left", fill="x", expand=True)
        self.combo.bind("<<ComboboxSelected>>", self._on_combobox_selected)

        # Pulsante rotazione orientamento
        self.btn_rotate = ttk.Button(
            self,
            text="🔄 Inverti Orientamento (Spazio / R)",
            style="TButton",
            command=self._on_rotate_click
        )
        self.btn_rotate.pack(fill="x", pady=(6, 2))

        self.ricostruisci_pillole(self.DEFAULT_FORMATS)

    def ricostruisci_pillole(self, formati_list: list):
        """Ricrea i pulsanti a pillola in base ai formati abilitati."""
        for w in self.pills_frame.winfo_children():
            w.destroy()
        self.pill_buttons.clear()

        cols = 3
        for idx, f_name in enumerate(formati_list):
            r = idx // cols
            c = idx % cols

            btn = ttk.Button(
                self.pills_frame,
                text=f_name,
                style="Pill.TButton",
                command=lambda f=f_name: self.set_formato(f)
            )
            btn.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
            self.pill_buttons[f_name] = btn

        for c in range(cols):
            self.pills_frame.grid_columnconfigure(c, weight=1)

        self._aggiorna_pill_styles()

    def set_modello(self, modello: dict | None):
        """Aggiorna i formati consentiti quando viene scelto un modello dal catalogo."""
        if modello and "formati" in modello:
            formati_modello = modello["formati"]
            self.ricostruisci_pillole(formati_modello)
            self.combo["values"] = formati_modello
            if formati_modello:
                self.set_formato(formati_modello[0])
        else:
            self.ricostruisci_pillole(self.DEFAULT_FORMATS)
            self.combo["values"] = list(FORMATI.keys())

    def _aggiorna_pill_styles(self):
        curr = self.formato_var.get()
        for f_name, btn in self.pill_buttons.items():
            if f_name == curr:
                btn.config(style="PillActive.TButton")
            else:
                btn.config(style="Pill.TButton")

    def _on_combobox_selected(self, event=None):
        self._aggiorna_pill_styles()
        self._notifica_cambio_formato()

    def set_formato(self, val: str):
        self.formato_var.set(val)
        self._aggiorna_pill_styles()
        self._notifica_cambio_formato()

    def _notifica_cambio_formato(self):
        if hasattr(self.main_app, "editor_panel"):
            self.main_app.editor_panel.crop_orientation_override = None
            self.main_app.editor_panel._aggiorna_render()
        if hasattr(self.main_app, "miniature_panel"):
            self.main_app.miniature_panel.aggiorna_evidenza()

    def _on_rotate_click(self):
        if hasattr(self.main_app, "editor_panel"):
            self.main_app.editor_panel.flip_crop_orientation()

    def get_formato(self) -> str:
        return self.formato_var.get()


# =============================================================================
# 3. Pannello Materiali, Carta & Campionari Colore Reali
# =============================================================================
class MaterialiPanel(ttk.LabelFrame):
    """Pannello materiali: carica i campionari colore abbinati al modello scelto."""

    def __init__(self, master, main_app):
        super().__init__(master, text="Carta & Campionario Colori", padding=12)
        self.main_app = main_app

        self.tipo_carta_var = tk.StringVar(value="Carta Lucida")
        self.collezione_var = tk.StringVar()
        self.colore_var = tk.StringVar()

        # Tipo carta interna
        row_carta = ttk.Frame(self, style="Card.TFrame")
        row_carta.pack(fill="x", pady=3)

        ttk.Label(row_carta, text="Carta Interna:", style="Card.TLabel").pack(side="left", padx=(0, 8))
        combo_carta = ttk.Combobox(
            row_carta,
            textvariable=self.tipo_carta_var,
            values=["Carta Lucida", "Satinata / Opaca", "Tela Fine Art", "Metallic / Silk", "Velvet HD"],
            state="readonly"
        )
        combo_carta.pack(side="right", fill="x", expand=True)

        # Selezione Collezione Tessuto / Pelle
        row_coll = ttk.Frame(self, style="Card.TFrame")
        row_coll.pack(fill="x", pady=4)

        ttk.Label(row_coll, text="Campionario:", style="Card.TLabel").pack(side="left", padx=(0, 8))
        self.combo_collezione = ttk.Combobox(
            row_coll,
            textvariable=self.collezione_var,
            state="readonly"
        )
        self.combo_collezione.pack(side="right", fill="x", expand=True)
        self.combo_collezione.bind("<<ComboboxSelected>>", self._on_collezione_changed)

        # Selezione Colore / Codice reale
        row_col = ttk.Frame(self, style="Card.TFrame")
        row_col.pack(fill="x", pady=3)

        ttk.Label(row_col, text="Colore / Codice:", style="Card.TLabel").pack(side="left", padx=(0, 8))
        self.combo_colore = ttk.Combobox(
            row_col,
            textvariable=self.colore_var,
            state="readonly"
        )
        self.combo_colore.pack(side="right", fill="x", expand=True)

        self.set_modello(None)

    def set_modello(self, modello: dict | None):
        """Filtra i campionari e colori consentiti per il modello specifico."""
        if modello and "campionari" in modello and modello["campionari"]:
            collezioni = modello["campionari"]
        else:
            collezioni = list(CAMPIONARI_COLORI.keys())

        self.combo_collezione["values"] = collezioni
        if collezioni:
            self.combo_collezione.set(collezioni[0])
            self._on_collezione_changed()

    def _on_collezione_changed(self, event=None):
        coll_scelta = self.collezione_var.get()
        colori = CAMPIONARI_COLORI.get(coll_scelta, [])

        opzioni_colore = [f"Cod. {c['codice']} - {c['nome']}" for c in colori]
        self.combo_colore["values"] = opzioni_colore
        if opzioni_colore:
            self.combo_colore.set(opzioni_colore[0])
        else:
            self.colore_var.set("Standard")

    def get_materiale(self) -> str:
        carta = self.tipo_carta_var.get()
        coll = self.collezione_var.get()
        col = self.colore_var.get()
        return f"{carta} | {coll}: {col}"


# =============================================================================
# 4. Pannello Dati Commessa & Personalizzazione Sposi
# =============================================================================
class InfoOrdinePanel(ttk.LabelFrame):
    """Pannello per dati cliente, busta, nomi sposi per incisione e note."""

    def __init__(self, master, main_app):
        super().__init__(master, text="Dati Commessa & Personalizzazione", padding=12)
        self.main_app = main_app

        self.num_busta_var = tk.StringVar()
        self.codice_cliente_var = tk.StringVar()
        self.nome_cliente_var = tk.StringVar()
        self.nomi_sposi_var = tk.StringVar()
        self.correzione_var = tk.BooleanVar(value=False)

        config = self.main_app.config_mgr.data
        self.codice_cliente_var.set(config.get("codice_cliente", ""))
        self.num_busta_var.set(str(config.get("ultimo_num_busta", 1)))

        # Griglia dati ordine
        row1 = ttk.Frame(self, style="Card.TFrame")
        row1.pack(fill="x", pady=3)
        ttk.Label(row1, text="Busta N°:", style="Card.TLabel").pack(side="left", padx=(0, 6))
        entry_busta = ttk.Entry(row1, textvariable=self.num_busta_var, width=10, font=("Helvetica", 10, "bold"))
        entry_busta.pack(side="left")

        ttk.Label(row1, text="Cod. Fotografo:", style="Card.TLabel").pack(side="left", padx=(10, 6))
        entry_cod = ttk.Entry(row1, textvariable=self.codice_cliente_var, width=10, font=("Helvetica", 10))
        entry_cod.pack(side="left", fill="x", expand=True)

        row2 = ttk.Frame(self, style="Card.TFrame")
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Nome Cliente:", style="Card.TLabel").pack(side="left", padx=(0, 8))
        entry_nome = ttk.Entry(row2, textvariable=self.nome_cliente_var, font=("Helvetica", 10))
        entry_nome.pack(side="left", fill="x", expand=True)

        # Campo dedicato ai nomi sposi (per incisione su cofanetto o copertina)
        self.row_sposi = ttk.Frame(self, style="Card.TFrame")
        self.row_sposi.pack(fill="x", pady=4)
        ttk.Label(self.row_sposi, text="Nomi Sposi (Incisione):", style="Card.TLabel").pack(side="left", padx=(0, 8))
        entry_sposi = ttk.Entry(self.row_sposi, textvariable=self.nomi_sposi_var, font=("Helvetica", 10))
        entry_sposi.pack(side="left", fill="x", expand=True)

        # Note di laboratorio
        ttk.Label(self, text="Note di Lavorazione:", style="Card.TLabel").pack(anchor="w", pady=(6, 2))
        self.note_text = tk.Text(
            self,
            height=3,
            bg=BG_INPUT,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            font=("Helvetica", 10)
        )
        self.note_text.pack(fill="x", pady=(0, 4))

        # Checkbox correzione colore
        chk_corr = ttk.Checkbutton(
            self,
            text="Correzione colore / densità al minilab",
            variable=self.correzione_var
        )
        chk_corr.pack(anchor="w", pady=(4, 0))

    def set_modello(self, modello: dict | None):
        """Mostra o nasconde i campi personalizzati in base al modello scelto."""
        if modello and modello.get("opzioni", {}).get("nomi_sposi"):
            self.row_sposi.pack(fill="x", pady=3, before=self.note_text)
        else:
            pass  # Lasciamolo sempre disponibile per comodità

    def get_data(self) -> dict:
        return {
            "num_busta": self.num_busta_var.get().strip() or "001",
            "codice_cliente": self.codice_cliente_var.get().strip(),
            "nome_cliente": self.nome_cliente_var.get().strip(),
            "nomi_sposi": self.nomi_sposi_var.get().strip(),
            "note": self.note_text.get("1.0", "end").strip(),
            "correzione": self.correzione_var.get(),
        }

    def reset_for_new_order(self):
        self.nome_cliente_var.set("")
        self.nomi_sposi_var.set("")
        self.note_text.delete("1.0", "end")
        self.correzione_var.set(False)
        nuovo_num = self.main_app.config_mgr.genera_num_busta()
        self.num_busta_var.set(str(nuovo_num))
