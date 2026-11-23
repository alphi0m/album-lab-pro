"""
Pannello scorrevole delle miniature in stile Dark Studio con hover effect e gestione multi-selezione.
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from src.core.constants import FORMATI
from src.ui.theme import (
    BG_APP, BG_CARD, BG_HOVER, BG_INPUT, PRIMARY, PRIMARY_HOVER,
    TEXT_PRIMARY, TEXT_MUTED, BORDER_COLOR, ACCENT_AMBER
)


class MiniaturePanel(tk.Frame):
    """Pannello con griglia fluida di miniature fotografiche con feedback interattivo."""

    def __init__(self, master, main_app):
        super().__init__(master, bg=BG_APP, relief="flat")
        self.main_app = main_app

        self.foto_items = []
        self.selected_indices = set()
        self.active_index = None

        # ---------------- Toolbar superiore miniature ----------------
        self.toolbar = tk.Frame(self, bg=BG_APP)
        self.toolbar.pack(fill="x", padx=8, pady=(6, 8))

        self.lbl_count = tk.Label(
            self.toolbar,
            text="Foto: 0 (Copie: 0)",
            bg=BG_APP,
            fg=PRIMARY,
            font=("Helvetica", 10, "bold")
        )
        self.lbl_count.pack(side="left", padx=4)

        # Pulsanti rapidi quantità con stile Dark
        btn_plus = ttk.Button(
            self.toolbar, text="+ Copia", width=7,
            command=lambda: self.modifica_quantita_selezionate(1)
        )
        btn_plus.pack(side="right", padx=2)

        btn_minus = ttk.Button(
            self.toolbar, text="− Copia", width=7,
            command=lambda: self.modifica_quantita_selezionate(-1)
        )
        btn_minus.pack(side="right", padx=2)

        btn_set_copies = ttk.Button(
            self.toolbar, text="🔢 Copie...", width=8,
            command=self._chiedi_imposta_copie
        )
        btn_set_copies.pack(side="right", padx=2)

        btn_select_all = ttk.Button(
            self.toolbar, text="Tutto", width=5,
            command=self.seleziona_tutto
        )
        btn_select_all.pack(side="right", padx=2)

        # ---------------- Canvas con Scrollbar Dark ----------------
        self.container = tk.Frame(self, bg=BG_APP)
        self.container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.container, bg=BG_APP, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner_frame = tk.Frame(self.canvas, bg=BG_APP)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_inner_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

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

    # -------------------------------------------------------------------------
    # Aggiornamento Miniature
    # -------------------------------------------------------------------------
    def set_foto_items(self, items: list):
        self.foto_items = items
        self.selected_indices.clear()
        self.active_index = 0 if items else None
        self.aggiorna_vista()

    def aggiorna_vista(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        tot_copie = sum(f.quantita for f in self.foto_items)
        self.lbl_count.config(text=f"Foto: {len(self.foto_items)} (Tot. Stampe: {tot_copie})")

        cols = 2
        for idx, foto in enumerate(self.foto_items):
            r = idx // cols
            c = idx % cols

            card = self._crea_card_miniatura(idx, foto)
            card.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")

        for i in range(cols):
            self.inner_frame.grid_columnconfigure(i, weight=1)

        self.aggiorna_evidenza()

    def _crea_card_miniatura(self, idx: int, foto) -> tk.Frame:
        card = tk.Frame(
            self.inner_frame,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightcolor=PRIMARY,
            highlightthickness=1,
            cursor="hand2"
        )
        card.idx = idx

        thumb_img = foto.get_thumbnail(size=130)
        lbl_img = tk.Label(card, image=thumb_img, bg=BG_CARD)
        lbl_img.image = thumb_img
        lbl_img.pack(padx=4, pady=(4, 2))

        # Nome file pulito
        short_name = foto.filename if len(foto.filename) <= 18 else foto.filename[:15] + "..."
        lbl_name = tk.Label(
            card,
            text=short_name,
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=("Helvetica", 9)
        )
        lbl_name.pack(pady=(0, 2))

        # Controllo rapido copie direttamente sulla miniatura (cross-platform dark)
        bar_qty = tk.Frame(card, bg=BG_CARD)
        bar_qty.pack(fill="x", padx=4, pady=(0, 4))

        def _make_qty_btn(text, delta):
            btn = tk.Label(
                bar_qty,
                text=text,
                bg="#262930",
                fg="#FFFFFF",
                font=("Helvetica", 10, "bold"),
                width=3,
                relief="flat",
                highlightbackground="#3E424D",
                highlightthickness=1,
                cursor="hand2"
            )
            btn.bind("<Button-1>", lambda e, d=delta: self._modifica_quantita_singola(idx, d))
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=PRIMARY, fg="#FFFFFF"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#262930", fg="#FFFFFF"))
            return btn

        btn_q_min = _make_qty_btn("−", -1)
        btn_q_min.pack(side="left", padx=(2, 0))

        lbl_qty = tk.Label(
            bar_qty, text=f"{foto.quantita} cp", bg=BG_CARD,
            fg="#52A1FF" if foto.quantita > 1 else TEXT_MUTED,
            font=("Helvetica", 9, "bold")
        )
        lbl_qty.pack(side="left", fill="x", expand=True)

        btn_q_plus = _make_qty_btn("+", 1)
        btn_q_plus.pack(side="right", padx=(0, 2))

        card.lbl_name = lbl_name
        card.lbl_img = lbl_img
        card.lbl_qty = lbl_qty

        # Gestione Hover Effect (bordo si illumina delicatamente)
        def on_enter(e):
            if card.idx not in self.selected_indices and card.idx != self.active_index:
                card.config(highlightbackground="#4A5060", highlightthickness=1)

        def on_leave(e):
            if card.idx not in self.selected_indices and card.idx != self.active_index:
                card.config(highlightbackground=BORDER_COLOR, highlightthickness=1)

        for w in (card, lbl_img, lbl_name):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", lambda e, i=idx: self._on_thumb_click(e, i))
            w.bind("<Double-Button-1>", lambda e, i=idx: self._on_thumb_double_click(e, i))

        return card

    # -------------------------------------------------------------------------
    # Selezione & Evidenziazione
    # -------------------------------------------------------------------------
    def _on_thumb_click(self, event, idx: int):
        is_ctrl = (event.state & 0x0004) or (event.state & 0x0008)
        is_shift = (event.state & 0x0001)

        if is_ctrl:
            if idx in self.selected_indices:
                self.selected_indices.remove(idx)
            else:
                self.selected_indices.add(idx)
        elif is_shift and self.active_index is not None:
            start = min(self.active_index, idx)
            end = max(self.active_index, idx)
            self.selected_indices = set(range(start, end + 1))
        else:
            self.selected_indices = {idx}

        self.active_index = idx
        self.main_app.set_foto_corrente(idx)
        self.aggiorna_evidenza()

    def _on_thumb_double_click(self, event, idx: int):
        self.main_app.set_foto_corrente(idx)

    def aggiorna_evidenza(self):
        children = self.inner_frame.winfo_children()

        for card in children:
            idx = getattr(card, "idx", None)
            if idx is None or idx >= len(self.foto_items):
                continue

            foto = self.foto_items[idx]
            mismatch = self._verifica_proporzione_errata(foto)

            is_active = (idx == self.active_index)
            is_selected = (idx in self.selected_indices)

            if is_active:
                card.config(highlightbackground=PRIMARY, highlightthickness=2)
                card.lbl_name.config(fg=PRIMARY)
            elif is_selected:
                card.config(highlightbackground="#2680EB", highlightthickness=2)
                card.lbl_name.config(fg="#80BFFF")
            elif mismatch and not foto.has_custom_crop:
                card.config(highlightbackground=ACCENT_AMBER, highlightthickness=2)
                card.lbl_name.config(fg=ACCENT_AMBER)
            else:
                card.config(highlightbackground=BORDER_COLOR, highlightthickness=1)
                card.lbl_name.config(fg=TEXT_MUTED)

    def _verifica_proporzione_errata(self, foto) -> bool:
        formato_str = self.main_app.formati_panel.get_formato()
        base = formato_str.split(" ")[0].lower()

        if "x" not in base:
            return False

        try:
            fw, fh = map(float, base.split("x"))
            target_ratio = max(fw, fh) / min(fw, fh)

            w, h = foto.image_orig.size
            img_ratio = max(w, h) / min(w, h)

            return abs(img_ratio - target_ratio) > 0.03
        except Exception:
            return False

    def seleziona_tutto(self):
        self.selected_indices = set(range(len(self.foto_items)))
        self.aggiorna_evidenza()

    def deseleziona_tutto(self):
        self.selected_indices.clear()
        self.aggiorna_evidenza()

    def modifica_quantita_selezionate(self, delta: int):
        target_indices = self.selected_indices if self.selected_indices else ({self.active_index} if self.active_index is not None else set())
        for idx in target_indices:
            if 0 <= idx < len(self.foto_items):
                nuova = max(1, self.foto_items[idx].quantita + delta)
                self.foto_items[idx].quantita = nuova
                self.foto_items[idx]._thumb_cache.clear()

        self.aggiorna_vista()
        self.main_app._aggiorna_stats()
        self.main_app.editor_panel._aggiorna_info()

    def _modifica_quantita_singola(self, idx: int, delta: int):
        if 0 <= idx < len(self.foto_items):
            nuova = max(1, self.foto_items[idx].quantita + delta)
            self.foto_items[idx].quantita = nuova
            self.foto_items[idx]._thumb_cache.clear()
            self.aggiorna_vista()
            self.main_app._aggiorna_stats()
            self.main_app.editor_panel._aggiorna_info()

    def _chiedi_imposta_copie(self):
        target_indices = self.selected_indices if self.selected_indices else ({self.active_index} if self.active_index is not None else set(range(len(self.foto_items))))
        if not target_indices:
            messagebox.showinfo("Nessuna Foto", "Nessuna foto selezionata.")
            return

        quante_foto = len(target_indices)
        nuove_copie = simpledialog.askinteger(
            "Imposta Copie",
            f"Inserisci il numero di copie da assegnare a {quante_foto} foto:",
            initialvalue=1,
            minvalue=1,
            maxvalue=999,
            parent=self.winfo_toplevel()
        )
        if nuove_copie is not None:
            for idx in target_indices:
                if 0 <= idx < len(self.foto_items):
                    self.foto_items[idx].quantita = nuove_copie
                    self.foto_items[idx]._thumb_cache.clear()
            self.aggiorna_vista()
            self.main_app._aggiorna_stats()
            self.main_app.editor_panel._aggiorna_info()
