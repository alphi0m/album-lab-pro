@echo off
cd /d "%~dp0"
python avvia_laboratorio.py
if errorlevel 1 (
    echo.
    echo ========================================================
    echo  Errore di avvio!
    echo  Assicurati che Python sia installato sul sistema.
    echo ========================================================
    pause
)
