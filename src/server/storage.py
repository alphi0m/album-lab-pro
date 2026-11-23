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
SERVER_CLIENTS_FILE = SERVER_DATA_DIR / "clients.json"


class ServerStorage:
    """Gestisce l'archiviazione e il recupero degli ordini ricevuti dal cloud."""

    @staticmethod
    def init():
        SERVER_ORDERS_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def genera_order_id() -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import random
        rand_suffix = random.randint(1000, 9999)
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

        # Salva i file fotografici sanificando i nomi ed evitando collisioni
        saved_files_info = []
        for file_storage in files:
            raw_filename = Path(file_storage.filename or "foto.jpg").name
            dest_name = raw_filename
            counter = 2
            p_stem = Path(raw_filename).stem
            p_ext = Path(raw_filename).suffix
            while (photos_folder / dest_name).exists():
                dest_name = f"{p_stem}_{counter}{p_ext}"
                counter += 1

            dest_path = photos_folder / dest_name
            file_storage.save(str(dest_path))
            saved_files_info.append(dest_name)

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
                        data["order_id"] = data.get("order_id") or folder.name
                        data["stato"] = str(data.get("stato") or "IN ATTESA").strip().upper()
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
        clean_status = str(nuovo_stato).strip().upper()
        if not clean_status:
            return False

        ordine = cls.get_ordine(order_id)
        if not ordine:
            return False

        ordine["stato"] = clean_status
        ordine["ultimo_aggiornamento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cls.init()
        order_folder = SERVER_ORDERS_DIR / order_id
        json_path = order_folder / "order.json"
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

    # =========================================================================
    # Gestione Anagrafica Fotografi & PIN Sicuro
    # =========================================================================
    @classmethod
    def get_tutti_clienti(cls) -> dict:
        """Restituisce il dizionario di tutti i fotografi registrati."""
        cls.init()
        if SERVER_CLIENTS_FILE.exists():
            try:
                with open(SERVER_CLIENTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Errore lettura clients.json: {e}")

        # Account demo predefiniti per test immediato
        default_clients = {
            "101": {
                "codice": "101",
                "nome_studio": "Foto Studio Demo",
                "pin": "1234",
                "titolare": "Marco Rossi",
                "telefono": "333 1234567",
                "data_registrazione": "2026-11-23",
                "attivo": True
            }
        }
        try:
            with open(SERVER_CLIENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(default_clients, f, indent=4, ensure_ascii=False)
        except Exception:
            pass
        return default_clients

    @classmethod
    def salva_cliente(cls, codice: str, nome_studio: str, pin: str, titolare: str = "", telefono: str = "") -> bool:
        """Aggiunge o aggiorna un fotografo partner con il suo codice e PIN univoco."""
        clean_cod = str(codice).strip()
        clean_pin = str(pin).strip()
        clean_nome = str(nome_studio).strip()
        if not clean_cod or not clean_pin or not clean_nome:
            return False

        clienti = cls.get_tutti_clienti()
        clienti[clean_cod] = {
            "codice": clean_cod,
            "nome_studio": clean_nome,
            "pin": clean_pin,
            "titolare": titolare.strip(),
            "telefono": telefono.strip(),
            "data_registrazione": datetime.now().strftime("%Y-%m-%d"),
            "attivo": True
        }

        try:
            with open(SERVER_CLIENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(clienti, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Errore salvataggio clienti: {e}")
            return False

    @classmethod
    def elimina_cliente(cls, codice: str) -> bool:
        clienti = cls.get_tutti_clienti()
        clean_cod = str(codice).strip()
        if clean_cod in clienti:
            del clienti[clean_cod]
            try:
                with open(SERVER_CLIENTS_FILE, "w", encoding="utf-8") as f:
                    json.dump(clienti, f, indent=4, ensure_ascii=False)
                return True
            except Exception:
                return False
        return False

    @classmethod
    def verifica_cliente(cls, codice: str, pin: str) -> tuple[bool, dict | None]:
        """Verifica se il codice fotografo e il PIN corrispondono a uno studio attivo."""
        clienti = cls.get_tutti_clienti()
        clean_cod = str(codice).strip()
        clean_pin = str(pin).strip()

        if clean_cod in clienti:
            info = clienti[clean_cod]
            if str(info.get("pin")).strip() == clean_pin and info.get("attivo", True):
                return True, info
        return False, None

    @classmethod
    def get_ordini_per_cliente(cls, codice: str) -> list:
        """Restituisce tutti gli ordini appartenenti al fotografo specificato."""
        tutti = cls.get_tutti_ordini()
        clean_cod = str(codice).strip()
        if not clean_cod:
            return []
        # Corrispondenza su codice_cliente (es. "101" o numerico)
        return [o for o in tutti if str(o.get("codice_cliente", "")).strip() == clean_cod]

