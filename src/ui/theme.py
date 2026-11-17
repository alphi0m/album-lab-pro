"""
Tema Dark Studio (in stile Photoshop / Lightroom) per Album Lab.
Palette professionale scura ottimizzata per l'elaborazione fotografica e il lavoro al banco.
"""

import tkinter as tk
from tkinter import ttk

# =============================================================================
# PALETTE COLORI "DARK STUDIO"
# =============================================================================
BG_DARKEST = "#121316"   # Sfondo Canvas editor fotografico
BG_APP = "#18191C"       # Sfondo generale finestra e barre principali
BG_CARD = "#22242A"      # Sfondo pannelli, card e contenitori
BG_HOVER = "#2D3038"     # Sfondo elementi al passaggio del mouse
BG_INPUT = "#1A1B1F"     # Sfondo caselle di testo e input

TEXT_PRIMARY = "#EDEDED" # Testo principale (bianco nitido)
TEXT_SECONDARY = "#A0AAB5" # Testo secondario / etichette
TEXT_MUTED = "#6C757D"   # Testo attenuato / scorciatoie

PRIMARY = "#0078FF"      # Blu elettrico azioni primarie
PRIMARY_HOVER = "#2693FF"# Blu al passaggio del mouse
PRIMARY_ACTIVE = "#005ECC"

ACCENT_GREEN = "#2ECC71" # Verde smeraldo per salvataggio ed esiti positivi
ACCENT_GREEN_HOVER = "#27AE60"
SUCCESS = ACCENT_GREEN

ACCENT_AMBER = "#F39C12" # Ambra per avvisi proporzioni e ritagli
WARNING = ACCENT_AMBER

ACCENT_RED = "#E74C3C"   # Rosso rubino per eliminazione
DANGER = ACCENT_RED

BORDER_COLOR = "#2F323A" # Bordo sottile di separazione
BORDER_ACTIVE = "#0078FF"# Bordo di selezione attiva


def apply_dark_studio_theme(root: tk.Tk):
    """Applica la configurazione TTK completa in stile Dark Studio con scala DPI ottimizzata."""
    # Ottimizzazione scala DPI per display ad alta risoluzione (Mac Retina, 2K/4K)
    try:
        current_scaling = float(root.tk.call('tk', 'scaling'))
        if current_scaling < 1.25:
            root.tk.call('tk', 'scaling', 1.33)
    except Exception:
        pass

    style = ttk.Style(root)
    
    available_themes = style.theme_names()
    if "clam" in available_themes:
        style.theme_use("clam")

    # Finestra principale
    root.configure(bg=BG_APP)

    # ---------------- Frame e Card ----------------
    style.configure("TFrame", background=BG_APP)
    style.configure("Card.TFrame", background=BG_CARD)
    style.configure("Darkest.TFrame", background=BG_DARKEST)

    # ---------------- LabelFrame ----------------
    style.configure(
        "TLabelframe",
        background=BG_CARD,
        foreground=TEXT_PRIMARY,
        relief="solid",
        borderwidth=1,
        bordercolor=BORDER_COLOR
    )
    style.configure(
        "TLabelframe.Label",
        background=BG_CARD,
        foreground=PRIMARY,
        font=("Helvetica", 11, "bold")
    )

    # ---------------- Etichette (TLabel) ----------------
    style.configure("TLabel", background=BG_APP, foreground=TEXT_PRIMARY, font=("Helvetica", 10))
    style.configure("Card.TLabel", background=BG_CARD, foreground=TEXT_PRIMARY, font=("Helvetica", 10))
    style.configure("Muted.TLabel", background=BG_CARD, foreground=TEXT_MUTED, font=("Helvetica", 9))
    style.configure("Header.TLabel", background=BG_APP, foreground=TEXT_PRIMARY, font=("Helvetica", 12, "bold"))
    style.configure("Brand.TLabel", background=BG_APP, foreground=PRIMARY, font=("Helvetica", 13, "bold"))

    # ---------------- Pulsanti Standard (TButton) ----------------
    style.configure(
        "TButton",
        background=BG_HOVER,
        foreground=TEXT_PRIMARY,
        font=("Helvetica", 10),
        borderwidth=1,
        bordercolor=BORDER_COLOR,
        relief="flat",
        padding=(14, 8)
    )
    style.map(
        "TButton",
        background=[("pressed", BG_INPUT), ("active", "#363A44")],
        bordercolor=[("active", PRIMARY)]
    )

    # ---------------- Pulsante Primario (Azione Principale) ----------------
    style.configure(
        "Primary.TButton",
        background=PRIMARY,
        foreground="#FFFFFF",
        font=("Helvetica", 10, "bold"),
        borderwidth=0,
        relief="flat",
        padding=(16, 9)
    )
    style.map(
        "Primary.TButton",
        background=[("pressed", PRIMARY_ACTIVE), ("active", PRIMARY_HOVER)]
    )

    # ---------------- Pulsante Salva Ordine (Verde) ----------------
    style.configure(
        "Success.TButton",
        background=ACCENT_GREEN,
        foreground="#FFFFFF",
        font=("Helvetica", 10, "bold"),
        borderwidth=0,
        relief="flat",
        padding=(16, 9)
    )
    style.map(
        "Success.TButton",
        background=[("pressed", "#219653"), ("active", ACCENT_GREEN_HOVER)]
    )

    # ---------------- Pulsanti Pillola Formati (Normale vs Selezionato) ----------------
    style.configure(
        "Pill.TButton",
        background="#2A2D35",
        foreground=TEXT_SECONDARY,
        font=("Helvetica", 10, "bold"),
        borderwidth=1,
        bordercolor=BORDER_COLOR,
        relief="flat",
        padding=(10, 8)
    )
    style.map(
        "Pill.TButton",
        background=[("active", "#363A44")],
        foreground=[("active", TEXT_PRIMARY)]
    )

    style.configure(
        "PillActive.TButton",
        background=PRIMARY,
        foreground="#FFFFFF",
        font=("Helvetica", 10, "bold"),
        borderwidth=1,
        bordercolor=PRIMARY_HOVER,
        relief="flat",
        padding=(10, 8)
    )
    style.map(
        "PillActive.TButton",
        background=[("active", PRIMARY_HOVER)],
        foreground=[("active", "#FFFFFF")]
    )

    # ---------------- Entry e Combobox Scuri ----------------
    style.configure(
        "TEntry",
        fieldbackground=BG_INPUT,
        background=BG_INPUT,
        foreground=TEXT_PRIMARY,
        insertcolor=TEXT_PRIMARY,
        bordercolor=BORDER_COLOR,
        font=("Helvetica", 10),
        padding=(8, 6)
    )

    style.configure(
        "TCombobox",
        fieldbackground=BG_INPUT,
        background=BG_HOVER,
        foreground=TEXT_PRIMARY,
        selectbackground=PRIMARY,
        selectforeground="#FFFFFF",
        bordercolor=BORDER_COLOR,
        font=("Helvetica", 10),
        padding=(8, 6)
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", BG_INPUT)],
        selectbackground=[("readonly", BG_INPUT)],
        selectforeground=[("readonly", TEXT_PRIMARY)]
    )

    # ---------------- Checkbutton ----------------
    style.configure(
        "TCheckbutton",
        background=BG_CARD,
        foreground=TEXT_PRIMARY,
        font=("Helvetica", 10)
    )
    style.map(
        "TCheckbutton",
        background=[("active", BG_CARD)]
    )

    # ---------------- Separator ----------------
    style.configure("TSeparator", background=BORDER_COLOR)

    # ---------------- Treeview (Tabella Archivio) ----------------
    style.configure(
        "Treeview",
        background=BG_CARD,
        foreground=TEXT_PRIMARY,
        fieldbackground=BG_CARD,
        rowheight=34,
        font=("Helvetica", 10),
        borderwidth=0
    )
    style.configure(
        "Treeview.Heading",
        background="#1C1E23",
        foreground=TEXT_PRIMARY,
        font=("Helvetica", 10, "bold"),
        relief="flat",
        padding=(8, 8)
    )
    style.map(
        "Treeview",
        background=[("selected", "#1A3B66")],
        foreground=[("selected", "#FFFFFF")]
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#282A31")]
    )
