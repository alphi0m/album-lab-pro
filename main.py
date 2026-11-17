#!/usr/bin/env python3
"""
Album Lab — Software Gestionale e di Produzione per Laboratori Fotografici.
Punto di ingresso principale dell'applicazione.
"""

import sys
import os

# Assicura che la directory radice sia nel path di ricerca Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.ui.main_window import run_app


if __name__ == "__main__":
    run_app()
