"""
Gestione della configurazione e utilità di sistema cross-platform.
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from src.core.constants import CONFIG_FILE, ARCHIVIO_DIR


def resource_path(relative_path: str) -> str:
    """Restituisce il percorso assoluto delle risorse, compatibile sia in dev che con PyInstaller."""
    base_path = getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent.parent)
    return str(Path(base_path) / relative_path)


def open_folder(path_to_open: str | Path):
    """Apre una cartella nel file manager del sistema operativo (macOS, Windows, Linux)."""
    p = str(path_to_open)
    if not os.path.exists(p):
        return False
    try:
        if sys.platform == "win32":
            os.startfile(p)
        elif sys.platform == "darwin":
            subprocess.run(["open", p], check=False)
        else:
            subprocess.run(["xdg-open", p], check=False)
        return True
    except Exception as e:
        print(f"Errore apertura cartella {p}: {e}")
        return False


class ConfigManager:
    """Carica, salva e gestisce le impostazioni utente e il contatore ordini."""

    def __init__(self, filepath: Path = CONFIG_FILE):
        self.filepath = filepath
        self.data = self.load()

    def load(self) -> dict:
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Errore lettura config: {e}")
        
        default_config = {
            "codice_cliente": "",
            "ultimo_num_busta": 1,
            "dpi_stampa": 300,
            "qualita_jpeg": 98,
        }
        self.save(default_config)
        return default_config

    def save(self, data: dict = None):
        if data is not None:
            self.data = data
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Errore salvataggio config: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def genera_num_busta(self) -> int:
        num = self.data.get("ultimo_num_busta", 1)
        self.data["ultimo_num_busta"] = num + 1
        self.save()
        return num
