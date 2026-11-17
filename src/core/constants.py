"""
Costanti globali e configurazioni predefinite per Album Lab.
"""

import sys
import os
from pathlib import Path

# Formati di stampa standard (larghezza in cm, altezza in cm)
FORMATI = {
    "10x15": (10, 15),
    "13x18": (13, 18),
    "15x20": (15, 20),
    "20x25": (20, 25),
    "20x30": (20, 30),
    "24x30": (24, 30),
    "25x25": (25, 25),
    "25x35": (25, 35),
    "30x20": (30, 20),
    "30x30": (30, 30),
    "30x40": (30, 40),
    "40x30": (40, 30),
    "30x45": (30, 45),
    "35x25": (35, 25),
    "35x45": (35, 45),
    "40x40": (40, 40),
    "40x50": (40, 50),
    "40x60": (40, 60),
    "50x70": (50, 70),
    "60x80": (60, 80),
    "70x100": (70, 100),
}

# Gestione percorsi compatibile sia con ambiente di sviluppo che con eseguibili pacchettizzati (PyInstaller)
if getattr(sys, "frozen", False):
    # Eseguibile PyInstaller
    BUNDLE_DIR = Path(sys._MEIPASS)
    # Se su macOS dentro .app/Contents/MacOS, mettiamo i dati accanto alla .app
    exe_dir = Path(sys.executable).parent
    if "Contents/MacOS" in str(exe_dir):
        APP_DIR = exe_dir.parent.parent.parent
    else:
        APP_DIR = exe_dir
else:
    BUNDLE_DIR = Path(__file__).resolve().parent.parent.parent
    APP_DIR = BUNDLE_DIR

BASE_DIR = BUNDLE_DIR
ARCHIVIO_DIR = APP_DIR / "archivio_ordini"
CONFIG_FILE = APP_DIR / "config.json"
CATALOG_FILE = BUNDLE_DIR / "catalog.json"

# Impostazioni di stampa predefinite
DEFAULT_DPI = 300
DEFAULT_JPEG_QUALITY = 98

# Tipi file supportati per il caricamento foto
FILETYPES_FOTO = [
    ("Immagini fotografiche", "*.jpg *.jpeg *.png *.webp *.tif *.tiff"),
    ("Tutti i file", "*.*"),
]
