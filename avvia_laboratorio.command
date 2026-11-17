#!/usr/bin/env bash
cd "$(dirname "$0")"
PY_BIN=$(which python3 2>/dev/null || which python 2>/dev/null || echo "/opt/anaconda3/bin/python")
"$PY_BIN" avvia_laboratorio.py
