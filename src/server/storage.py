"""
Gestione dello storage degli ordini ricevuti sul server del laboratorio.
"""

import json
import os
import shutil
import zipfile
from datetime import datetime
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    exe_dir = Path(sys.executable).parent
    if "Contents/MacOS" in str(exe_dir):
        SERVER_DATA_DIR = exe_dir.parent.parent.parent / "server_data"
    else:
        SERVER_DATA_DIR = exe_dir / "server_data"
else:
    SERVER_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "server_data"

SERVER_ORDERS_DIR = SERVER_DATA_DIR / "orders"


class ServerStorage:
    """Gestisce l'archiviazione e il recupero degli ordini ricevuti dal cloud."""

    @staticmethod
    def init():
        SERVER_ORDERS_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def genera_order_id() -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import random
        rand_suffix = random.randint(100, 999)
        return f"ORD-{timestamp}-{rand_suffix}"

    @classmethod
    def salva_ordine(cls, order_id: str, metadata: dict, files: list) -> Path:
        """
        Salva metadati e file fotografici nella cartella dedicata server_data/orders/{order_id}/.
        """
        cls.init()
        order_folder = SERVER_ORDERS_DIR / order_id
        order_folder.mkdir(parents=True, exist_ok=True)
        photos_folder = order_folder / "photos"
        photos_folder.mkdir(parents=True, exist_ok=True)

        # Salva i file fotografici
        saved_files_info = []
        for file_storage in files:
            filename = file_storage.filename
            dest_path = photos_folder / filename
            file_storage.save(str(dest_path))
            saved_files_info.append(filename)

        # Metadati completi con stato iniziale
        metadata["order_id"] = order_id
        metadata["data_ricezione"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata["stato"] = "IN ATTESA"
        metadata["file_ricevuti"] = saved_files_info

        json_path = order_folder / "order.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)

        return order_folder

    @classmethod
    def get_tutti_ordini(cls) -> list:
        cls.init()
        ordini = []
        for folder in SERVER_ORDERS_DIR.iterdir():
            if not folder.is_dir():
                continue
            json_path = folder / "order.json"
            if json_path.exists():
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data["_folder"] = str(folder)
                        data["totale_file"] = len(data.get("file_ricevuti", []))
                        ordini.append(data)
                except Exception as e:
                    print(f"Errore lettura {json_path}: {e}")

        # Ordina per data di ricezione più recente
        ordini.sort(key=lambda x: x.get("data_ricezione", ""), reverse=True)
        return ordini

    @classmethod
    def get_ordine(cls, order_id: str) -> dict | None:
        cls.init()
        order_folder = SERVER_ORDERS_DIR / order_id
        json_path = order_folder / "order.json"
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["_folder"] = str(order_folder)
                    return data
            except Exception as e:
                print(f"Errore lettura ordine {order_id}: {e}")
        return None

    @classmethod
    def aggiorna_stato(cls, order_id: str, nuovo_stato: str) -> bool:
        ordine = cls.get_ordine(order_id)
        if not ordine:
            return False

        ordine["stato"] = nuovo_stato.upper()
        ordine["ultimo_aggiornamento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        json_path = Path(ordine["_folder"]) / "order.json"
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(ordine, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Errore aggiornamento stato {order_id}: {e}")
            return False

    @classmethod
    def crea_zip_stampa(cls, order_id: str) -> Path | None:
        """Crea un file .ZIP pronto con tutte le foto e il foglio istruzioni."""
        ordine = cls.get_ordine(order_id)
        if not ordine:
            return None

        order_folder = Path(ordine["_folder"])
        photos_folder = order_folder / "photos"
        zip_path = order_folder / f"{order_id}_stampa_completa.zip"

        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zipf:
            if photos_folder.exists():
                for p_file in photos_folder.iterdir():
                    if p_file.is_file():
                        zipf.write(str(p_file), arcname=f"foto_stampa/{p_file.name}")
            
            json_path = order_folder / "order.json"
            if json_path.exists():
                zipf.write(str(json_path), arcname="riepilogo_ordine.json")

        return zip_path

    @classmethod
    def elimina_ordine(cls, order_id: str) -> bool:
        """Elimina la cartella della commessa dal server."""
        cls.init()
        order_folder = SERVER_ORDERS_DIR / order_id
        if order_folder.exists() and order_folder.is_dir():
            try:
                shutil.rmtree(order_folder)
                return True
            except Exception as e:
                print(f"Errore eliminazione ordine {order_id}: {e}")
                return False
        return False

