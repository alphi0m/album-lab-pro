"""
Finestra modale interattiva per sfogliare e selezionare i modelli dal catalogo visuale.
"""

import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from src.core.constants import BASE_DIR
from src.core.catalog import MODELLI_ALBUM
from src.ui.theme import (
    BG_APP, BG_CARD, BG_INPUT, PRIMARY, PRIMARY_HOVER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_COLOR, ACCENT_GREEN
)


class CatalogGalleryWindow(tk.Toplevel):
    """Galleria visuale con schede di tutti i 18 modelli album del catalogo."""

    def __init__(self, master, on_select_callback):
        super().__init__(master)
        self.on_select_callback = on_select_callback
        self.title("Catalogo Album — Selezione Modello")
        self.geometry("1180x800")
        self.minsize(900, 600)
        self.configure(bg=BG_APP)

        self.thumb_refs = []  # Per evitare garbage collection delle immagini

        # ---------------- Barra Superiore: Ricerca e Filtri ----------------
        top_bar = tk.Frame(self, bg=BG_APP, height=56, highlightbackground=BORDER_COLOR, highlightthickness=1)
        top_bar.pack(fill="x", side="top", padx=12, pady=(12, 8))

        tk.Label(
            top_bar,
            text="CATALOGO MODELLI",
            bg=BG_APP,
            fg=PRIMARY,
            font=("Helvetica", 13, "bold")
        ).pack(side="left", padx=14, pady=12)

        tk.Label(
            top_bar,
            text="Cerca:",
            bg=BG_APP,
            fg=TEXT_SECONDARY,
            font=("Helvetica", 10)
        ).pack(side="left", padx=(12, 6))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filtra_modelli())
        entry_search = ttk.Entry(top_bar, textvariable=self.search_var, width=32, font=("Helvetica", 10))
        entry_search.pack(side="left", padx=6)

        self.lbl_risultati = tk.Label(
            top_bar,
            text=f"{len(MODELLI_ALBUM)} modelli disponibili",
            bg=BG_APP,
            fg=TEXT_MUTED,
            font=("Helvetica", 10)
        )
        self.lbl_risultati.pack(side="right", padx=14, pady=12)

        # ---------------- Area Scorrevole con Griglia Modelli ----------------
        container = tk.Frame(self, bg=BG_APP)
        container.pack(fill="both", expand=True, padx=10, pady=4)

        self.canvas = tk.Canvas(container, bg=BG_APP, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner_frame = tk.Frame(self.canvas, bg=BG_APP)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        # Associa lo scroll con rotella in modo sicuro solo quando il mouse è sopra la finestra
        self.bind("<Enter>", lambda e: self.bind_all("<MouseWheel>", self._on_mousewheel))
        self.bind("<Leave>", lambda e: self.unbind_all("<MouseWheel>"))
        self.bind("<Destroy>", lambda e: self.unbind_all("<MouseWheel>"))

        self.filtra_modelli()

    def _on_mousewheel(self, event):
        try:
            if not self.winfo_exists() or not self.canvas.winfo_exists():
                return
            if event.num == 5 or event.delta < 0:
                self.canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta > 0:
                self.canvas.yview_scroll(-1, "units")
        except Exception:
            pass

    def filtra_modelli(self):
        query = self.search_var.get().strip().lower()

        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.thumb_refs.clear()

        modelli_filtrati = []
        for m in MODELLI_ALBUM:
            testo = f"{m['nome']} {m['sottotitolo']} {m['descrizione']} {' '.join(m['formati'])} {' '.join(m['campionari'])}".lower()
            if not query or query in testo:
                modelli_filtrati.append(m)

        self.lbl_risultati.config(text=f"{len(modelli_filtrati)} modelli trovati")

        # Visualizza schede a griglia (2 colonne)
        cols = 2
        for idx, m in enumerate(modelli_filtrati):
            r = idx // cols
            c = idx % cols

            card = self._crea_card_modello(m)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")

        for c in range(cols):
            self.inner_frame.grid_columnconfigure(c, weight=1)

    def _crea_card_modello(self, modello: dict) -> tk.Frame:
        card = tk.Frame(
            self.inner_frame,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=10,
            pady=10
        )

        # Immagine anteprima modello
        img_path = BASE_DIR / modello["immagine"]
        tk_img = None
        if img_path.exists():
            try:
                pil_img = Image.open(str(img_path))
                pil_img.thumbnail((200, 140), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(pil_img)
                self.thumb_refs.append(tk_img)
            except Exception as e:
                print(f"Errore caricamento immagine {img_path}: {e}")

        # Layout orizzontale della card: Immagine a sinistra, dettagli a destra
        img_frame = tk.Frame(card, bg=BG_CARD, width=200, height=140)
        img_frame.pack_propagate(False)
        img_frame.pack(side="left", padx=(0, 12))

        if tk_img:
            lbl_img = tk.Label(img_frame, image=tk_img, bg=BG_CARD)
            lbl_img.pack(expand=True)
        else:
            lbl_img = tk.Label(img_frame, text="Foto non disponibile", bg="#1A1B1F", fg=TEXT_MUTED)
            lbl_img.pack(fill="both", expand=True)

        # Dettagli del modello
        details_frame = tk.Frame(card, bg=BG_CARD)
        details_frame.pack(side="left", fill="both", expand=True)

        lbl_titolo = tk.Label(
            details_frame,
            text=modello["nome"],
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            font=("Helvetica", 12, "bold"),
            anchor="w"
        )
        lbl_titolo.pack(fill="x")

        lbl_sub = tk.Label(
            details_frame,
            text=modello["sottotitolo"],
            bg=BG_CARD,
            fg=PRIMARY,
            font=("Helvetica", 9, "italic"),
            anchor="w"
        )
        lbl_sub.pack(fill="x", pady=(2, 4))

        lbl_desc = tk.Label(
            details_frame,
            text=modello["descrizione"],
            bg=BG_CARD,
            fg=TEXT_SECONDARY,
            font=("Helvetica", 9),
            wraplength=320,
            justify="left",
            anchor="w"
        )
        lbl_desc.pack(fill="x", pady=(0, 6))

        # Tag Formati disponibili
        tags_frame = tk.Frame(details_frame, bg=BG_CARD)
        tags_frame.pack(fill="x", pady=(0, 6))

        formati_str = "  ".join(f"[{f}]" for f in modello["formati"])
        tk.Label(
            tags_frame,
            text=f"Formati: {formati_str}",
            bg=BG_CARD,
            fg="#2ECC71",
            font=("Helvetica", 9, "bold")
        ).pack(side="left")

        # Pulsante selezione modello
        btn_select = ttk.Button(
            details_frame,
            text="✓ Seleziona Questo Modello",
            style="Primary.TButton",
            command=lambda m=modello: self._seleziona(m)
        )
        btn_select.pack(anchor="w", pady=(6, 0))

        return card

    def _seleziona(self, modello: dict):
        if self.on_select_callback:
            self.on_select_callback(modello)
        self.destroy()
