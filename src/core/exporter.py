"""
Modulo di esportazione degli ordini e preparazione file per la stampa ad alta risoluzione.
"""

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from PIL import Image
from src.core.constants import ARCHIVIO_DIR, DEFAULT_DPI, DEFAULT_JPEG_QUALITY


class OrderExporter:
    """Gestisce il salvataggio degli ordini, l'esportazione dei ritagli a 300 DPI e la persistenza JSON."""

    @staticmethod
    def salva_ordine(order_data: dict, foto_list: list, config: dict = None) -> tuple[bool, str]:
        """
        Salva l'ordine nella cartella archivio_ordini/ordine_{num_busta}/.
        Genera i file ritagliati a risoluzione piena con DPI e profilo colore.
        """
        try:
            dpi_val = config.get("dpi_stampa", DEFAULT_DPI) if config else DEFAULT_DPI
            quality_val = config.get("qualita_jpeg", DEFAULT_JPEG_QUALITY) if config else DEFAULT_JPEG_QUALITY
            
            num_busta = str(order_data.get("num_busta", "senza_numero")).strip()
            # Sanifica il numero busta per evitare caratteri non validi nei percorsi file (es. /, \, :, *)
            safe_busta = re.sub(r'[\\/*?:"<>|]', '_', num_busta) or "senza_numero"
            folder_name = f"ordine_{safe_busta}"
            cartella_ordine = ARCHIVIO_DIR / folder_name
            cartella_ordine.mkdir(parents=True, exist_ok=True)

            foto_json_list = []
            used_filenames = set()

            for idx, foto in enumerate(foto_list, start=1):
                ext = Path(foto.path).suffix.lower()
                if ext not in [".jpg", ".jpeg"]:
                    ext = ".jpg"
                
                base_name = Path(foto.path).stem
                # Evita collisioni se più foto hanno lo stesso nome file (es. DSC_0001 da fotocamere diverse)
                out_filename = f"{base_name}_stampa{ext}"
                counter = 2
                while out_filename in used_filenames:
                    out_filename = f"{base_name}_{counter}_stampa{ext}"
                    counter += 1
                used_filenames.add(out_filename)

                out_path = cartella_ordine / out_filename

                # Ottieni l'immagine ritagliata alla risoluzione nativa
                cropped_img = foto.get_cropped_image()

                save_kwargs = {
                    "format": "JPEG",
                    "quality": quality_val,
                    "optimize": True,
                    "dpi": (dpi_val, dpi_val),
                }

                # Preserva il profilo ICC se presente nell'originale
                if getattr(foto, "icc_profile", None):
                    save_kwargs["icc_profile"] = foto.icc_profile

                cropped_img.save(str(out_path), **save_kwargs)

                foto_json_list.append({
                    "file_stampa": out_filename,
                    "path_originale": foto.path,
                    "quantita": foto.quantita,
                    "formato": foto.formato or order_data.get("formato", ""),
                    "materiale": foto.materiale or order_data.get("materiale", ""),
                    "risoluzione_px": [cropped_img.width, cropped_img.height],
                    "dpi": dpi_val,
                    "crop_box": list(foto.crop_box),
                    "has_custom_crop": foto.has_custom_crop,
                })

            # Metadati complessivi dell'ordine
            ordine_full = {
                "num_busta": num_busta,
                "codice_cliente": order_data.get("codice_cliente", ""),
                "nome_cliente": order_data.get("nome_cliente", ""),
                "nomi_sposi": order_data.get("nomi_sposi", ""),
                "modello_id": order_data.get("modello_id", ""),
                "modello_nome": order_data.get("modello_nome", ""),
                "modello_cofanetto": order_data.get("modello_cofanetto", ""),
                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "cartella": str(cartella_ordine),
                "note": order_data.get("note", ""),
                "formato_globale": order_data.get("formato", ""),
                "materiale_globale": order_data.get("materiale", ""),
                "correzione": order_data.get("correzione", False),
                "stato": "SALVATO",
                "totale_foto": len(foto_list),
                "totale_stampe": sum(f.quantita for f in foto_list),
                "foto": foto_json_list,
            }

            json_path = cartella_ordine / "ordine.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(ordine_full, f, indent=4, ensure_ascii=False)

            return True, str(cartella_ordine)

        except Exception as e:
            return False, str(e)
