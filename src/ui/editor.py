"""
Pannello Canvas per la visualizzazione e ritaglio interattivo in stile Dark Studio.
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from src.ui.theme import (
    BG_DARKEST, BG_APP, BG_CARD, PRIMARY, TEXT_PRIMARY, TEXT_MUTED, BORDER_COLOR
)


class EditorPanel(tk.Frame):
    """Area centrale dell'editor fotografico con canvas interattivo e griglia di ritaglio."""

    def __init__(self, master, main_app):
        super().__init__(master, bg=BG_DARKEST)
        self.main_app = main_app

        # Stato editor
        self.current_foto = None
        self.tk_image = None
        self.img_scale = 1.0
        self.img_x = 0
        self.img_y = 0
        self.display_w = 0
        self.display_h = 0

        # Stato ritaglio (coordinate canvas)
        self.crop_coords = None  # (x1, y1, x2, y2)
        self.dragging = False
        self.moving = False
        self.start_x = 0
        self.start_y = 0
        self.move_offset_x = 0
        self.move_offset_y = 0

        # Orientamento forzato: None (auto), 'landscape', 'portrait'
        self.crop_orientation_override = None

        # Creazione Canvas
        self.canvas = tk.Canvas(self, bg=BG_DARKEST, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Barra di stato inferiore in stile Lightroom / Studio
        self.info_bar = tk.Frame(self, bg=BG_APP, height=34, highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.info_bar.pack(fill="x", side="bottom")

        self.lbl_info = tk.Label(
            self.info_bar,
            text="Nessuna foto selezionata",
            bg=BG_APP,
            fg=TEXT_PRIMARY,
            font=("Helvetica", 9, "bold")
        )
        self.lbl_info.pack(side="left", padx=14, pady=6)

        self.lbl_shortcut = tk.Label(
            self.info_bar,
            text="Tasti: [Spazio / R] Ruota Crop  |  [← / →] Sfoglia  |  [+ / -] Copie  |  [Ctrl+S] Salva",
            bg=BG_APP,
            fg=TEXT_MUTED,
            font=("Helvetica", 9)
        )
        self.lbl_shortcut.pack(side="right", padx=14, pady=6)

        # Eventi mouse e ridimensionamento
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<Motion>", self._on_mouse_hover)

    # -------------------------------------------------------------------------
    # Visualizzazione Foto
    # -------------------------------------------------------------------------
    def clear(self):
        self.current_foto = None
        self.crop_coords = None
        self.canvas.delete("all")
        self.lbl_info.config(text="Nessuna foto selezionata")

    def mostra_foto(self, foto_item):
        if not foto_item:
            self.clear()
            return

        self.current_foto = foto_item
        self._aggiorna_render()

    def _on_resize(self, event):
        if self.current_foto:
            self._aggiorna_render()

    def _aggiorna_render(self):
        """Ricalcola le dimensioni dell'immagine e la centra nel canvas scuro."""
        if not self.current_foto:
            return

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        if canvas_w <= 20 or canvas_h <= 20:
            return

        orig_w = self.current_foto.width
        orig_h = self.current_foto.height

        margin = 35
        avail_w = max(10, canvas_w - (margin * 2))
        avail_h = max(10, canvas_h - (margin * 2))

        scale_w = avail_w / orig_w
        scale_h = avail_h / orig_h
        self.img_scale = min(scale_w, scale_h)

        self.display_w = max(1, int(orig_w * self.img_scale))
        self.display_h = max(1, int(orig_h * self.img_scale))

        self.img_x = (canvas_w - self.display_w) // 2
        self.img_y = (canvas_h - self.display_h) // 2

        resized = self.current_foto.image_orig.resize(
            (self.display_w, self.display_h),
            Image.Resampling.BILINEAR
        )
        self.tk_image = ImageTk.PhotoImage(resized)

        self.canvas.delete("all")

        # Disegna ombra leggera attorno alla foto
        shadow_offset = 4
        self.canvas.create_rectangle(
            self.img_x + shadow_offset, self.img_y + shadow_offset,
            self.img_x + self.display_w + shadow_offset, self.img_y + self.display_h + shadow_offset,
            fill="#08090A", width=0, tags="shadow"
        )

        self.canvas.create_image(
            self.img_x, self.img_y,
            anchor="nw",
            image=self.tk_image,
            tags="foto"
        )

        # Coordinate canvas
        ox1, oy1, ox2, oy2 = self.current_foto.crop_box
        cx1 = self.img_x + (ox1 * self.img_scale)
        cy1 = self.img_y + (oy1 * self.img_scale)
        cx2 = self.img_x + (ox2 * self.img_scale)
        cy2 = self.img_y + (oy2 * self.img_scale)

        self.crop_coords = (cx1, cy1, cx2, cy2)
        self._draw_crop_overlay()
        self._aggiorna_info()

    # -------------------------------------------------------------------------
    # Rapporto di Ritaglio (Ratio)
    # -------------------------------------------------------------------------
    def get_target_ratio(self) -> float:
        w_cm, h_cm = self.main_app.get_crop_size()
        base_ratio = w_cm / h_cm if h_cm != 0 else 1.0

        if self.crop_orientation_override == "landscape":
            return max(base_ratio, 1.0 / base_ratio)
        elif self.crop_orientation_override == "portrait":
            return min(base_ratio, 1.0 / base_ratio)

        if self.current_foto:
            foto_is_landscape = self.current_foto.width >= self.current_foto.height
            if foto_is_landscape:
                return max(base_ratio, 1.0 / base_ratio)
            else:
                return min(base_ratio, 1.0 / base_ratio)

        return base_ratio

    def flip_crop_orientation(self):
        current_ratio = self.get_target_ratio()
        if current_ratio >= 1.0:
            self.crop_orientation_override = "portrait"
        else:
            self.crop_orientation_override = "landscape"

        if self.current_foto and self.crop_coords:
            cx1, cy1, cx2, cy2 = self.crop_coords
            center_x = (cx1 + cx2) / 2
            center_y = (cy1 + cy2) / 2
            curr_w = abs(cx2 - cx1)
            new_ratio = self.get_target_ratio()

            new_w = curr_w
            new_h = new_w / new_ratio if new_ratio != 0 else new_w

            max_w = self.display_w
            max_h = self.display_h
            if new_h > max_h:
                new_h = max_h
                new_w = new_h * new_ratio
            if new_w > max_w:
                new_w = max_w
                new_h = new_w / new_ratio

            nx1 = max(self.img_x, min(self.img_x + self.display_w - new_w, center_x - (new_w / 2)))
            ny1 = max(self.img_y, min(self.img_y + self.display_h - new_h, center_y - (new_h / 2)))
            nx2 = nx1 + new_w
            ny2 = ny1 + new_h

            self.crop_coords = (nx1, ny1, nx2, ny2)
            self._salva_crop_in_foto()
            self._draw_crop_overlay()
            self._aggiorna_info()

    # -------------------------------------------------------------------------
    # Disegno Sovrimpressione Crop
    # -------------------------------------------------------------------------
    def _draw_crop_overlay(self):
        self.canvas.delete("overlay")

        if not self.crop_coords:
            return

        x1, y1, x2, y2 = self.crop_coords
        ix, iy = self.img_x, self.img_y
        iw, ih = self.display_w, self.display_h

        # Maschera oscurata esterna
        mask_color = "#000000"
        stipple = "gray50"

        if y1 > iy:
            self.canvas.create_rectangle(ix, iy, ix + iw, y1, fill=mask_color, stipple=stipple, width=0, tags="overlay")
        if y2 < iy + ih:
            self.canvas.create_rectangle(ix, y2, ix + iw, iy + ih, fill=mask_color, stipple=stipple, width=0, tags="overlay")
        if x1 > ix:
            self.canvas.create_rectangle(ix, max(iy, y1), x1, min(iy + ih, y2), fill=mask_color, stipple=stipple, width=0, tags="overlay")
        if x2 < ix + iw:
            self.canvas.create_rectangle(x2, max(iy, y1), ix + iw, min(iy + ih, y2), fill=mask_color, stipple=stipple, width=0, tags="overlay")

        # Bordo ritaglio nitido con doppio contorno
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="#0078FF", width=2, tags="overlay")

        # Regola dei Terzi (linee tratteggiate bianche sottili)
        cw = x2 - x1
        ch = y2 - y1
        if cw > 40 and ch > 40:
            grid_color = "#FFFFFF"
            self.canvas.create_line(x1 + cw / 3, y1, x1 + cw / 3, y2, fill=grid_color, dash=(2, 4), tags="overlay")
            self.canvas.create_line(x1 + (2 * cw / 3), y1, x1 + (2 * cw / 3), y2, fill=grid_color, dash=(2, 4), tags="overlay")
            self.canvas.create_line(x1, y1 + ch / 3, x2, y1 + ch / 3, fill=grid_color, dash=(2, 4), tags="overlay")
            self.canvas.create_line(x1, y1 + (2 * ch / 3), x2, y1 + (2 * ch / 3), fill=grid_color, dash=(2, 4), tags="overlay")

        # Maniglie angolari visibili
        handle_size = 5
        for hx, hy in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
            self.canvas.create_rectangle(
                hx - handle_size, hy - handle_size,
                hx + handle_size, hy + handle_size,
                fill="#0078FF", outline="#FFFFFF", width=1, tags="overlay"
            )

    # -------------------------------------------------------------------------
    # Interazione Mouse
    # -------------------------------------------------------------------------
    def _is_inside_crop(self, x, y) -> bool:
        if not self.crop_coords:
            return False
        x1, y1, x2, y2 = self.crop_coords
        return x1 <= x <= x2 and y1 <= y <= y2

    def _on_mouse_down(self, event):
        if not self.current_foto:
            return

        x, y = event.x, event.y

        if self._is_inside_crop(x, y):
            self.moving = True
            self.dragging = False
            self.move_offset_x = x - self.crop_coords[0]
            self.move_offset_y = y - self.crop_coords[1]
        else:
            self.dragging = True
            self.moving = False
            self.start_x = max(self.img_x, min(self.img_x + self.display_w, x))
            self.start_y = max(self.img_y, min(self.img_y + self.display_h, y))
            self.crop_coords = (self.start_x, self.start_y, self.start_x, self.start_y)
            self._draw_crop_overlay()

    def _on_mouse_drag(self, event):
        if not self.current_foto:
            return

        x = max(self.img_x, min(self.img_x + self.display_w, event.x))
        y = max(self.img_y, min(self.img_y + self.display_h, event.y))

        if self.moving and self.crop_coords:
            x1, y1, x2, y2 = self.crop_coords
            w = x2 - x1
            h = y2 - y1

            nx1 = x - self.move_offset_x
            ny1 = y - self.move_offset_y

            nx1 = max(self.img_x, min(self.img_x + self.display_w - w, nx1))
            ny1 = max(self.img_y, min(self.img_y + self.display_h - h, ny1))
            nx2 = nx1 + w
            ny2 = ny1 + h

            self.crop_coords = (nx1, ny1, nx2, ny2)
            self._draw_crop_overlay()
            return

        if self.dragging:
            x1, y1 = self.start_x, self.start_y
            ratio = self.get_target_ratio()

            dx = x - x1
            dy = y - y1

            dir_x = 1 if dx >= 0 else -1
            dir_y = 1 if dy >= 0 else -1

            abs_dx = abs(dx)
            abs_dy = abs(dy)

            if abs_dy == 0 or abs_dx > abs_dy * ratio:
                width = abs_dx
                height = width / ratio if ratio != 0 else width
            else:
                height = abs_dy
                width = height * ratio

            x2 = x1 + (width * dir_x)
            y2 = y1 + (height * dir_y)

            rx1 = max(self.img_x, min(self.img_x + self.display_w, min(x1, x2)))
            ry1 = max(self.img_y, min(self.img_y + self.display_h, min(y1, y2)))
            rx2 = max(self.img_x, min(self.img_x + self.display_w, max(x1, x2)))
            ry2 = max(self.img_y, min(self.img_y + self.display_h, max(y1, y2)))

            self.crop_coords = (rx1, ry1, rx2, ry2)
            self._draw_crop_overlay()

    def _on_mouse_up(self, event):
        self.dragging = False
        self.moving = False
        self._salva_crop_in_foto()
        self._aggiorna_info()

    def _on_mouse_hover(self, event):
        if not self.current_foto:
            self.canvas.config(cursor="")
            return

        if self._is_inside_crop(event.x, event.y):
            self.canvas.config(cursor="fleur")
        else:
            self.canvas.config(cursor="crosshair")

    def _salva_crop_in_foto(self):
        if not self.current_foto or not self.crop_coords:
            return

        cx1, cy1, cx2, cy2 = self.crop_coords
        if self.img_scale <= 0:
            return

        ox1 = (cx1 - self.img_x) / self.img_scale
        oy1 = (cy1 - self.img_y) / self.img_scale
        ox2 = (cx2 - self.img_x) / self.img_scale
        oy2 = (cy2 - self.img_y) / self.img_scale

        self.current_foto.set_crop_box(ox1, oy1, ox2, oy2, custom=True)
        self.main_app.miniature_panel.aggiorna_evidenza()

    def _aggiorna_info(self):
        if not self.current_foto:
            self.lbl_info.config(text="Nessuna foto selezionata")
            return

        w_cm, h_cm = self.main_app.get_crop_size()
        ow, oh = self.current_foto.width, self.current_foto.height
        cropped = self.current_foto.get_cropped_image()
        cw, ch = cropped.size

        orient_str = "Orizzontale" if cw >= ch else "Verticale"
        info_text = (
            f"📷 {self.current_foto.filename}   |   "
            f"Originale: {ow}x{oh} px   |   "
            f"Ritaglio: {cw}x{ch} px ({orient_str} {w_cm}x{h_cm} cm)   |   "
            f"Copie: {self.current_foto.quantita}"
        )
        self.lbl_info.config(text=info_text)
