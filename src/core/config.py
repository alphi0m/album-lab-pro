"""
Gestione della configurazione e utilità di sistema cross-platform.
"""

import json
import os
import sys
import subprocess
import re
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
            "server_url": "http://localhost:5050",
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
        num = self.trova_prossimo_num_busta()
        self.data["ultimo_num_busta"] = num + 1
        self.save()
        return num

    def is_busta_in_conflitto(self, num_busta: str | int, archivio_dir: Path = ARCHIVIO_DIR) -> bool:
        """Verifica se esiste già una commessa archiviata localmente con lo stesso numero busta."""
        s = str(num_busta).strip()
        if not s:
            return False
        safe_busta = re.sub(r'[\\/*?:"<>|]', '_', s)
        target = archivio_dir / f"ordine_{safe_busta}"
        if target.exists():
            return True

        # Se il numero busta è intero/numerico (es. 5 oppure 005), confronta numericamente
        is_num = s.isdigit()
        val_int = int(s) if is_num else None

        if archivio_dir.exists():
            for entry in archivio_dir.iterdir():
                if not entry.is_dir() or not entry.name.startswith("ordine_"):
                    continue
                if entry.name == f"ordine_{safe_busta}" or entry.name.startswith(f"ordine_{safe_busta}_"):
                    return True
                if is_num:
                    m = re.search(r"ordine_(\d+)", entry.name)
                    if m:
                        try:
                            if int(m.group(1)) == val_int:
                                return True
                        except ValueError:
                            pass
        return False

    def trova_prossimo_num_busta(self, archivio_dir: Path = ARCHIVIO_DIR) -> int:
        """
        Calcola in maniera sicura il prossimo numero busta progressivo libero,
        evitando qualsiasi conflitto con commesse già presenti nell'archivio locale.
        """
        numeri_usati = set()
        ultimo_in_cfg = self.data.get("ultimo_num_busta", 1)
        if isinstance(ultimo_in_cfg, int):
            numeri_usati.add(ultimo_in_cfg)

        if archivio_dir.exists():
            for entry in archivio_dir.iterdir():
                if entry.is_dir() and entry.name.startswith("ordine_"):
                    # Estrae eventuali cifre dal nome della cartella
                    match = re.search(r"ordine_(\d+)", entry.name)
                    if match:
                        try:
                            numeri_usati.add(int(match.group(1)))
                        except ValueError:
                            pass

        if not numeri_usati:
            return 1

        candidato = max(numeri_usati)
        # Se il massimo è già in archivio, passa subito al successivo
        while self.is_busta_in_conflitto(candidato, archivio_dir):
            candidato += 1

        return candidato
