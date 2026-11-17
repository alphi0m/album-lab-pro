#!/usr/bin/env bash
set -e

echo "========================================================"
echo " ALBUM LAB PRO - COMPILAZIONE ESEGUIBILI MACOS (.APP / .DMG)"
echo "========================================================"

PYINSTALLER=$(which pyinstaller 2>/dev/null || echo "/opt/anaconda3/bin/pyinstaller")

echo ""
echo "1. Compilazione Server Laboratorio..."
$PYINSTALLER --noconfirm AlbumLab_Server.spec

echo ""
echo "2. Compilazione Client Fotografo..."
$PYINSTALLER --noconfirm AlbumLab_Client.spec

echo ""
echo "3. Creazione immagine disco macOS (.dmg)..."
rm -f dist/AlbumLabPro.dmg
hdiutil create -volname "AlbumLabPro" -srcfolder dist/AlbumLabPro.app -ov -format UDZO dist/AlbumLabPro.dmg

echo ""
echo "========================================================"
echo " COMPILAZIONE COMPLETATA CON SUCCESSO!"
echo " DMG pronto: dist/AlbumLabPro.dmg"
echo " Server pronto: dist/AlbumLabServer/AlbumLabServer"
echo "========================================================"
