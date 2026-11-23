"""
Pannelli di controllo Dark Studio: Gestione duale Stampa Album e Stampe Fotografiche Singole,
formati dinamici, carte ufficiali minilab (Lucida, Satinata, Seta), controllo conflitti busta e note ergonomiche.
"""

import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from src.core.constants import (
    FORMATI, BASE_DIR, CARTE_FOTO, CARTA_FOTO_DEFAULT, MODO_ALBUM, MODO_STAMPE
)
from src.core.catalog import MODELLI_ALBUM, CAMPIONARI_COLORI
from src.ui.theme import (
    BG_CARD, BG_INPUT, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    BORDER_COLOR, ACCENT_AMBER, SUCCESS, DANGER
)


# =============================================================================
# 1. Pannello Selezione Modello Album / Modalità Ordine
# =============================================================================
class ModelloPanel(ttk.LabelFrame):
    """Pannello in testata della colonna destra per visualizzare e scegliere il modello album o la modalità stampe."""

    def __init__(self, master, main_app):
        super().__init__(master, text="Stampa Album (Catalogo)", padding=12)
        self.main_app = main_app
        self.modello_corrente = None
        self.thumb_tk = None
        self.modalita = MODO_ALBUM

        # Riga con nome modello e tasto per sfogliare
        self.header_frame = tk.Frame(self, bg=BG_CARD)
        self.header_frame.pack(fill="x")

        self.lbl_nome = tk.Label(
            self.header_frame,
            text="Nessun modello (Clicca Catalogo)",
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            font=("Helvetica", 11, "bold"),
            anchor="w"
        )
        self.lbl_nome.pack(side="left", fill="x", expand=True)

        self.btn_browse = ttk.Button(
            self.header_frame,
            text="📖 Catalogo...",
            style="Primary.TButton",
            width=13,
            command=self.main_app.apri_catalogo
        )
        self.btn_browse.pack(side="right")

        # Dettagli del modello selezionato
        self.details_frame = tk.Frame(self, bg=BG_CARD)
        self.details_frame.pack(fill="x", pady=(8, 0))

        self.lbl_preview_img = tk.Label(self.details_frame, bg=BG_CARD)
        self.lbl_preview_img.pack(side="left", padx=(0, 10))

        self.lbl_desc = tk.Label(
            self.details_frame,
            text="Clicca su 'Catalogo...' per scegliere uno dei modelli professionali.",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=("Helvetica", 9),
            wraplength=260,
            justify="left",
            anchor="w"
        )
        self.lbl_desc.pack(side="left", fill="both", expand=True)

    def set_modalita(self, modalita: str):
        self.modalita = modalita
        if modalita == MODO_STAMPE:
            self.config(text="Modalità Commessa")
            self.btn_browse.pack_forget()
            self.lbl_nome.config(text="Stampe Fotografiche Singole", fg=PRIMARY)
            self.lbl_desc.config(
                text="Produzione foto sciolte e ingrandimenti su carta minilab.\nNessun vincolo di modello o copertina."
            )
            self.lbl_preview_img.config(image="")
            self.thumb_tk = None
        else:
            self.config(text="Stampa Album (Catalogo)")
            self.btn_browse.pack(side="right")
            if self.modello_corrente:
                self.set_modello(self.modello_corrente)
            else:
                self.lbl_nome.config(text="Nessun modello (Clicca Catalogo)", fg=TEXT_PRIMARY)
                self.lbl_desc.config(text="Clicca su 'Catalogo...' per scegliere un modello professionale.")
                self.lbl_preview_img.config(image="")
                self.thumb_tk = None

    def set_modello(self, modello: dict | None):
        self.modello_corrente = modello
        if self.modalita == MODO_STAMPE:
            return

        if not modello:
            self.lbl_nome.config(text="Nessun modello (Clicca Catalogo)", fg=TEXT_PRIMARY)
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
# 2. Pannello Formati di Stampa con Vincolo Dinamico & Applica a Tutte
# =============================================================================
class FormatiPanel(ttk.LabelFrame):
    """Pannello formati: pillole rapide, dropdown completo e assegnazione in blocco."""

    DEFAULT_FORMATS_ALBUM = ["10x15", "13x18", "15x20", "20x30", "30x30", "30x40", "40x40"]
    DEFAULT_FORMATS_STAMPE = ["10x13", "10x15", "13x18", "15x20", "20x30", "30x40"]

    def __init__(self, master, main_app):
        super().__init__(master, text="Formato di Stampa", padding=12)
        self.main_app = main_app
        self.modalita = MODO_ALBUM

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

        # Pulsanti d'azione (Rotazione e Applica a Tutte)
        actions_frame = ttk.Frame(self, style="Card.TFrame")
        actions_frame.pack(fill="x", pady=(4, 0))

        self.btn_rotate = ttk.Button(
            actions_frame,
            text="🔄 Inverti Crop (Spazio / R)",
            style="TButton",
            command=self._on_rotate_click
        )
        self.btn_rotate.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_applica_tutte = ttk.Button(
            actions_frame,
            text="⚡ Applica a Tutte",
            style="TButton",
            command=self.applica_formato_a_tutte
        )
        self.btn_applica_tutte.pack(side="right", fill="x", expand=True, padx=(3, 0))

        self.ricostruisci_pillole(self.DEFAULT_FORMATS_ALBUM)

    def set_modalita(self, modalita: str):
        self.modalita = modalita
        if modalita == MODO_STAMPE:
            self.config(text="Formato Stampe Singole")
            self.ricostruisci_pillole(self.DEFAULT_FORMATS_STAMPE)
            self.combo["values"] = list(FORMATI.keys())
        else:
            self.config(text="Formato di Stampa Album")
            if self.main_app.modello_selezionato:
                self.set_modello(self.main_app.modello_selezionato)
            else:
                self.ricostruisci_pillole(self.DEFAULT_FORMATS_ALBUM)
                self.combo["values"] = list(FORMATI.keys())

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
        if self.modalita == MODO_STAMPE:
            return

        if modello and "formati" in modello:
            formati_modello = modello["formati"]
            self.ricostruisci_pillole(formati_modello)
            self.combo["values"] = formati_modello
            if formati_modello and self.formato_var.get() not in formati_modello:
                self.set_formato(formati_modello[0])
        else:
            self.ricostruisci_pillole(self.DEFAULT_FORMATS_ALBUM)
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

    def applica_formato_a_tutte(self):
        """Applica il formato attualmente selezionato a tutte le foto caricate nell'ordine."""
        if not self.main_app.foto_list:
            messagebox.showinfo("Nessuna Foto", "Nessuna foto presente nell'ordine.")
            return

        formato_scelto = self.get_formato()
        for f in self.main_app.foto_list:
            f.formato = formato_scelto
            # Resetta il crop per ricalcolarlo automaticamente con le nuove proporzioni
            f.reset_crop()

        if hasattr(self.main_app, "editor_panel"):
            self.main_app.editor_panel._aggiorna_render()
        if hasattr(self.main_app, "miniature_panel"):
            self.main_app.miniature_panel.aggiorna_vista()

        tot = len(self.main_app.foto_list)
        messagebox.showinfo("Formato Applicato", f"Formato {formato_scelto} applicato con successo a tutte le {tot} foto.")

    def get_formato(self) -> str:
        return self.formato_var.get()


# =============================================================================
# 3. Pannello Materiali & Carte Minilab (Lucida, Satinata, Seta)
# =============================================================================
class MaterialiPanel(ttk.LabelFrame):
    """Pannello carte e materiali: gestisce carte minilab per stampe sciolte e campionari colore per album."""

    def __init__(self, master, main_app):
        super().__init__(master, text="Carta & Campionario Colori", padding=12)
        self.main_app = main_app
        self.modalita = MODO_ALBUM

        # Variabili album (Limitate alle carte fisiche di laboratorio: Lucida, Satinata, Seta)
        self.tipo_carta_album_var = tk.StringVar(value=CARTA_FOTO_DEFAULT)
        self.collezione_var = tk.StringVar()
        self.colore_var = tk.StringVar()

        # Variabile carta stampe singole (Standard ufficiale minilab: Lucida)
        self.carta_minilab_var = tk.StringVar(value=CARTA_FOTO_DEFAULT)

        # ---------------- SOTTOPANNELLO 1: STAMPA ALBUM ----------------
        self.frame_album = ttk.Frame(self, style="Card.TFrame")
        self.frame_album.pack(fill="x")

        # Tipo carta interna
        row_carta = ttk.Frame(self.frame_album, style="Card.TFrame")
        row_carta.pack(fill="x", pady=3)

        ttk.Label(row_carta, text="Carta Interna:", style="Card.TLabel").pack(side="left", padx=(0, 8))
        combo_carta = ttk.Combobox(
            row_carta,
            textvariable=self.tipo_carta_album_var,
            values=CARTE_FOTO,
            state="readonly"
        )
        combo_carta.pack(side="right", fill="x", expand=True)

        # Selezione Collezione Tessuto / Pelle
        row_coll = ttk.Frame(self.frame_album, style="Card.TFrame")
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
        row_col = ttk.Frame(self.frame_album, style="Card.TFrame")
        row_col.pack(fill="x", pady=3)

        ttk.Label(row_col, text="Colore / Codice:", style="Card.TLabel").pack(side="left", padx=(0, 8))
        self.combo_colore = ttk.Combobox(
            row_col,
            textvariable=self.colore_var,
            state="readonly"
        )
        self.combo_colore.pack(side="right", fill="x", expand=True)

        # ---------------- SOTTOPANNELLO 2: STAMPE SINGOLE ----------------
        self.frame_stampe = ttk.Frame(self, style="Card.TFrame")
        # Inizialmente non visibile, mostrato in MODO_STAMPE

        ttk.Label(
            self.frame_stampe,
            text="Supporto Carta Minilab:",
            style="Card.TLabel",
            font=("Helvetica", 9, "bold")
        ).pack(anchor="w", pady=(0, 6))

        # Pillole / Radio per le 3 carte ufficiali minilab (Lucida, Satinata, Seta)
        self.pills_carta_frame = ttk.Frame(self.frame_stampe, style="Card.TFrame")
        self.pills_carta_frame.pack(fill="x", pady=(0, 6))
        self.carta_buttons = {}

        cols = 3
        for idx, carta in enumerate(CARTE_FOTO):
            btn = ttk.Button(
                self.pills_carta_frame,
                text=carta,
                style="PillActive.TButton" if carta == CARTA_FOTO_DEFAULT else "Pill.TButton",
                command=lambda c=carta: self.set_carta_minilab(c)
            )
            btn.grid(row=0, column=idx, padx=3, pady=2, sticky="nsew")
            self.carta_buttons[carta] = btn
            self.pills_carta_frame.grid_columnconfigure(idx, weight=1)

        self.btn_applica_carta = ttk.Button(
            self.frame_stampe,
            text="⚡ Applica Carta a Tutte",
            style="TButton",
            command=self.applica_carta_a_tutte
        )
        self.btn_applica_carta.pack(fill="x", pady=(4, 0))

        self.set_modello(None)

    def set_modalita(self, modalita: str):
        self.modalita = modalita
        if modalita == MODO_STAMPE:
            self.config(text="Carta Fotografica (Minilab)")
            self.frame_album.pack_forget()
            self.frame_stampe.pack(fill="x")
        else:
            self.config(text="Carta & Campionario Colori Album")
            self.frame_stampe.pack_forget()
            self.frame_album.pack(fill="x")

    def set_carta_minilab(self, carta: str):
        self.carta_minilab_var.set(carta)
        for c, btn in self.carta_buttons.items():
            if c == carta:
                btn.config(style="PillActive.TButton")
            else:
                btn.config(style="Pill.TButton")

    def applica_carta_a_tutte(self):
        """Assegna la carta minilab selezionata a tutte le foto caricate nell'ordine."""
        if not self.main_app.foto_list:
            messagebox.showinfo("Nessuna Foto", "Nessuna foto presente nell'ordine.")
            return

        carta_scelta = self.carta_minilab_var.get()
        for f in self.main_app.foto_list:
            f.materiale = carta_scelta

        tot = len(self.main_app.foto_list)
        messagebox.showinfo("Carta Minilab", f"Carta '{carta_scelta}' applicata con successo a tutte le {tot} foto.")

    def set_modello(self, modello: dict | None):
        """Filtra i campionari e colori consentiti per il modello specifico."""
        if self.modalita == MODO_STAMPE:
            return

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
        if self.modalita == MODO_STAMPE:
            return f"Carta {self.carta_minilab_var.get()}"
        else:
            carta = self.tipo_carta_album_var.get()
            coll = self.collezione_var.get()
            col = self.colore_var.get()
            return f"{carta} | {coll}: {col}"


# =============================================================================
# 4. Pannello Dati Commessa, Numero Busta Progressivo & Note Ergonomiche
# =============================================================================
class InfoOrdinePanel(ttk.LabelFrame):
    """Pannello dati cliente, numero busta progressivo con controllo conflitti e note ben visibili."""

    PLACEHOLDER_NOTE = "Inserisci qui note di laboratorio (es. bordino bianco 3mm, dettagli taglio, richieste particolari)..."

    def __init__(self, master, main_app):
        super().__init__(master, text="Dati Commessa & Produzione", padding=12)
        self.main_app = main_app
        self.modalita = MODO_ALBUM

        self.num_busta_var = tk.StringVar()
        self.codice_cliente_var = tk.StringVar()
        self.nome_cliente_var = tk.StringVar()
        self.nomi_sposi_var = tk.StringVar()
        self.correzione_var = tk.BooleanVar(value=False)
        self._has_placeholder = True

        config = self.main_app.config_mgr.data
        self.codice_cliente_var.set(config.get("codice_cliente", ""))

        # Genera il primo numero busta libero
        prossimo_num = self.main_app.config_mgr.trova_prossimo_num_busta()
        self.num_busta_var.set(str(prossimo_num))

        # --- Riga 1: Busta N° con controllo conflitti e tasto Prossimo Libero ---
        row1 = ttk.Frame(self, style="Card.TFrame")
        row1.pack(fill="x", pady=3)

        ttk.Label(row1, text="Busta N°:", style="Card.TLabel").pack(side="left", padx=(0, 6))
        self.entry_busta = ttk.Entry(row1, textvariable=self.num_busta_var, width=8, font=("Helvetica", 10, "bold"))
        self.entry_busta.pack(side="left")

        btn_auto_busta = ttk.Button(
            row1,
            text="+ Libero",
            width=7,
            style="TButton",
            command=self._imposta_prossimo_libero
        )
        btn_auto_busta.pack(side="left", padx=(4, 6))

        # Indicatore visivo di conflitto numero busta
        self.lbl_busta_status = tk.Label(
            row1,
            text="✓ Libero",
            bg=BG_CARD,
            fg=SUCCESS,
            font=("Helvetica", 9, "bold")
        )
        self.lbl_busta_status.pack(side="left", padx=(2, 6))

        # Codice Fotografo
        ttk.Label(row1, text="Cod:", style="Card.TLabel").pack(side="left", padx=(6, 4))
        entry_cod = ttk.Entry(row1, textvariable=self.codice_cliente_var, width=8, font=("Helvetica", 10))
        entry_cod.pack(side="left", fill="x", expand=True)

        # Ascolta le modifiche al numero busta per rilevare conflitti in tempo reale
        self.num_busta_var.trace_add("write", self._on_busta_changed)

        # --- Riga 2: Nome Cliente / Riferimento ---
        row2 = ttk.Frame(self, style="Card.TFrame")
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Nome Cliente:", style="Card.TLabel").pack(side="left", padx=(0, 8))
        entry_nome = ttk.Entry(row2, textvariable=self.nome_cliente_var, font=("Helvetica", 10))
        entry_nome.pack(side="left", fill="x", expand=True)

        # --- Riga 3: Nomi Sposi (Incisione Album) ---
        self.row_sposi = ttk.Frame(self, style="Card.TFrame")
        self.row_sposi.pack(fill="x", pady=(4, 6))
        ttk.Label(self.row_sposi, text="Nomi Sposi (Incisione):", style="Card.TLabel").pack(side="left", padx=(0, 8))
        entry_sposi = ttk.Entry(self.row_sposi, textvariable=self.nomi_sposi_var, font=("Helvetica", 10))
        entry_sposi.pack(side="left", fill="x", expand=True)

        # --- Box Note di Lavorazione (Migliorato graficamente, alto e spazioso) ---
        self.box_note_container = tk.Frame(self, bg=BG_CARD)
        self.box_note_container.pack(fill="x", pady=(8, 4))

        hdr_note = tk.Frame(self.box_note_container, bg=BG_CARD)
        hdr_note.pack(fill="x", pady=(0, 4))

        ttk.Label(
            hdr_note,
            text="📝 Note di Lavorazione (Laboratorio):",
            style="Card.TLabel",
            font=("Helvetica", 9, "bold")
        ).pack(side="left")

        lbl_note_sub = tk.Label(
            hdr_note,
            text="(richieste speciali, finiture)",
            bg=BG_CARD,
            fg="#9AA0B0",
            font=("Helvetica", 8)
        )
        lbl_note_sub.pack(side="left", padx=(5, 0))

        # Area di testo con bordo visibile e scrollbar ergonomica
        notes_input_frame = tk.Frame(
            self.box_note_container,
            bg="#181A20",
            highlightbackground="#4A5263",
            highlightcolor=PRIMARY,
            highlightthickness=1,
            bd=0
        )
        notes_input_frame.pack(fill="x", pady=(2, 0))

        self.note_scrollbar = ttk.Scrollbar(notes_input_frame, orient="vertical")
        self.note_text = tk.Text(
            notes_input_frame,
            height=4,
            bg="#181A20",
            fg="#A0A6B8",
            insertbackground="#FFFFFF",
            relief="flat",
            wrap="word",
            font=("Helvetica", 10),
            yscrollcommand=self.note_scrollbar.set
        )
        self.note_scrollbar.config(command=self.note_text.yview)

        self.note_scrollbar.pack(side="right", fill="y")
        self.note_text.pack(side="left", fill="both", expand=True, padx=8, pady=6)

        self.note_text.insert("1.0", self.PLACEHOLDER_NOTE)
        self.note_text.bind("<FocusIn>", self._on_note_focus_in)
        self.note_text.bind("<FocusOut>", self._on_note_focus_out)

        # Checkbox correzione colore
        chk_corr = ttk.Checkbutton(
            self,
            text="Correzione colore / densità al minilab",
            variable=self.correzione_var
        )
        chk_corr.pack(anchor="w", pady=(4, 0))

        # Verifica iniziale stato busta
        self._on_busta_changed()

    def set_modalita(self, modalita: str):
        self.modalita = modalita
        if modalita == MODO_STAMPE:
            self.config(text="Dati Commessa Stampe")
            self.row_sposi.pack_forget()
        else:
            self.config(text="Dati Commessa Album")
            self.row_sposi.pack(fill="x", pady=4, before=self.box_note_container)

    def _imposta_prossimo_libero(self):
        prossimo = self.main_app.config_mgr.trova_prossimo_num_busta()
        self.num_busta_var.set(str(prossimo))

    def _on_busta_changed(self, *args):
        val = self.num_busta_var.get().strip()
        if not val:
            self.lbl_busta_status.config(text="⚠️ Vuoto", fg=ACCENT_AMBER)
            return

        in_conflitto = self.main_app.config_mgr.is_busta_in_conflitto(val)
        if in_conflitto:
            self.lbl_busta_status.config(text="⚠️ Già in uso", fg=ACCENT_AMBER)
        else:
            self.lbl_busta_status.config(text="✓ Libero", fg=SUCCESS)

    def _on_note_focus_in(self, event):
        if self._has_placeholder:
            self.note_text.delete("1.0", "end")
            self.note_text.config(fg="#FFFFFF")
            self._has_placeholder = False

    def _on_note_focus_out(self, event):
        content = self.note_text.get("1.0", "end").strip()
        if not content:
            self.note_text.delete("1.0", "end")
            self.note_text.insert("1.0", self.PLACEHOLDER_NOTE)
            self.note_text.config(fg="#A0A6B8")
            self._has_placeholder = True

    def set_modello(self, modello: dict | None):
        if self.modalita == MODO_STAMPE:
            self.row_sposi.pack_forget()
        else:
            self.row_sposi.pack(fill="x", pady=4, before=self.box_note_container)

    def get_data(self) -> dict:
        note_content = "" if self._has_placeholder else self.note_text.get("1.0", "end").strip()
        return {
            "num_busta": self.num_busta_var.get().strip() or "001",
            "codice_cliente": self.codice_cliente_var.get().strip(),
            "nome_cliente": self.nome_cliente_var.get().strip(),
            "nomi_sposi": self.nomi_sposi_var.get().strip() if self.modalita == MODO_ALBUM else "",
            "note": note_content,
            "correzione": self.correzione_var.get(),
            "modalita": self.modalita,
        }

    def reset_for_new_order(self):
        self.nome_cliente_var.set("")
        self.nomi_sposi_var.set("")
        self.note_text.delete("1.0", "end")
        self.note_text.insert("1.0", self.PLACEHOLDER_NOTE)
        self.note_text.config(fg="#A0A6B8")
        self._has_placeholder = True
        self.correzione_var.set(False)

        nuovo_num = self.main_app.config_mgr.trova_prossimo_num_busta()
        self.num_busta_var.set(str(nuovo_num))
