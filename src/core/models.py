"""
Modello dati per la gestione delle immagini fotografiche e dei ritagli.
Genera miniature moderne con pillole di quantità in stile iOS e indicatori di ritaglio.
"""

from pathlib import Path
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageFont
import os


class FotoItem:
    """Rappresenta una singola foto caricata nell'ordine."""

    def __init__(self, path: str):
        self.path = str(path)
        self.filename = os.path.basename(self.path)

        # Carica immagine originale e preserva orientamento EXIF
        raw_img = Image.open(self.path)
        self.image_orig = ImageOps.exif_transpose(raw_img).convert("RGB")
        
        # Conserva il profilo colore ICC originale (fondamentale per la stampa)
        self.icc_profile = raw_img.info.get("icc_profile")

        # Quantità di copie
        self.quantita = 1

        # Specifiche opzionali della foto (possono ereditare da quelle globali dell'ordine)
        self.formato = ""
        self.materiale = ""
        self.bordino_bianco = False

        # Coordinate del crop nell'immagine originale: (x1, y1, x2, y2) in pixel
        w, h = self.image_orig.size
        self.crop_box = (0, 0, w, h)
        self.has_custom_crop = False

        # Cache per le miniature Tkinter
        self._thumb_cache = {}

    @property
    def width(self):
        return self.image_orig.size[0]

    @property
    def height(self):
        return self.image_orig.size[1]

    @property
    def aspect_ratio(self):
        """Restituisce il rapporto d'aspetto (larghezza / altezza)."""
        w, h = self.image_orig.size
        return w / h if h != 0 else 1.0

    def get_cropped_image(self) -> Image.Image:
        """Restituisce l'immagine ritagliata alla massima risoluzione originale."""
        w, h = self.image_orig.size
        x1, y1, x2, y2 = self.crop_box

        x1 = max(0, min(w, int(round(x1))))
        y1 = max(0, min(h, int(round(y1))))
        x2 = max(0, min(w, int(round(x2))))
        y2 = max(0, min(h, int(round(y2))))

        if x2 <= x1 or y2 <= y1:
            return self.image_orig.copy()

        return self.image_orig.crop((x1, y1, x2, y2))

    def set_crop_box(self, x1, y1, x2, y2, custom: bool = True):
        w, h = self.image_orig.size
        self.crop_box = (
            max(0, min(w, x1)),
            max(0, min(h, y1)),
            max(0, min(w, x2)),
            max(0, min(h, y2))
        )
        self.has_custom_crop = custom
        self._thumb_cache.clear()

    def reset_crop(self):
        w, h = self.image_orig.size
        self.crop_box = (0, 0, w, h)
        self.has_custom_crop = False
        self._thumb_cache.clear()

    def get_thumbnail(self, size: int = 110) -> ImageTk.PhotoImage:
        """Genera una miniatura quadrata scura con pillole moderne di quantità e stato crop."""
        cache_key = (size, self.quantita, self.has_custom_crop, self.bordino_bianco)
        if cache_key in self._thumb_cache:
            return self._thumb_cache[cache_key]

        # Base quadrata con tonalità grafite scura
        thumb = Image.new("RGB", (size, size), (24, 25, 28))

        # Ridimensiona l'immagine mantenendo le proporzioni
        w, h = self.image_orig.size
        scale = (size - 12) / max(w, h)
        nw = max(1, int(w * scale))
        nh = max(1, int(h * scale))

        resized = self.image_orig.resize((nw, nh), Image.Resampling.LANCZOS)
        x_offset = (size - nw) // 2
        y_offset = (size - nh) // 2
        thumb.paste(resized, (x_offset, y_offset))

        draw = ImageDraw.Draw(thumb)

        # Se bordino bianco attivo, disegna una sottile cornice bianca elegante attorno alla foto
        if self.bordino_bianco:
            draw.rectangle(
                [x_offset, y_offset, x_offset + nw - 1, y_offset + nh - 1],
                outline=(255, 255, 255),
                width=2
            )

        # ---------------- 1. Badge Quantità a Pillola (in alto a destra) ----------------
        badge_text = f"x{self.quantita}"
        badge_w = 28 if len(badge_text) <= 2 else 36
        badge_h = 18
        bx1 = size - badge_w - 5
        by1 = 5
        bx2 = size - 5
        by2 = by1 + badge_h

        # Pillola blu elettrico se > 1 copia, altrimenti pillola grafite elegante
        if self.quantita > 1:
            pill_bg = (0, 120, 255)
            pill_border = (100, 180, 255)
        else:
            pill_bg = (40, 44, 52)
            pill_border = (65, 70, 80)

        draw.rounded_rectangle([bx1, by1, bx2, by2], radius=7, fill=pill_bg, outline=pill_border, width=1)
        draw.text((bx1 + 5, by1 + 2), badge_text, fill=(255, 255, 255))

        # ---------------- 2. Badge Stato Crop Personalizzato o Bordino (in basso a sinistra) ----------------
        if self.has_custom_crop:
            cx1, cy1 = 5, size - 22
            cx2, cy2 = cx1 + 34, cy1 + 16
            draw.rounded_rectangle([cx1, cy1, cx2, cy2], radius=6, fill=(39, 174, 96), outline=(46, 204, 113), width=1)
            draw.text((cx1 + 4, cy1 + 2), "CROP", fill=(255, 255, 255))
        elif self.bordino_bianco:
            cx1, cy1 = 5, size - 22
            cx2, cy2 = cx1 + 38, cy1 + 16
            draw.rounded_rectangle([cx1, cy1, cx2, cy2], radius=6, fill=(50, 54, 65), outline=(200, 200, 200), width=1)
            draw.text((cx1 + 4, cy1 + 2), "BORDO", fill=(255, 255, 255))

        tk_img = ImageTk.PhotoImage(thumb)
        self._thumb_cache[cache_key] = tk_img
        return tk_img

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "quantita": self.quantita,
            "formato": self.formato,
            "materiale": self.materiale,
            "bordino_bianco": self.bordino_bianco,
            "crop_box": list(self.crop_box),
            "has_custom_crop": self.has_custom_crop,
        }

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls(data["path"])
        obj.quantita = data.get("quantita", 1)
        obj.formato = data.get("formato", "")
        obj.materiale = data.get("materiale", "")
        obj.bordino_bianco = data.get("bordino_bianco", False)
        if "crop_box" in data and len(data["crop_box"]) == 4:
            obj.crop_box = tuple(data["crop_box"])
            obj.has_custom_crop = data.get("has_custom_crop", False)
        return obj
