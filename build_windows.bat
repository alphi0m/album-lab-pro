@echo off
echo ========================================================
echo  ALBUM LAB PRO - COMPILAZIONE ESEGUIBILI WINDOWS (.EXE)
echo ========================================================
echo.
echo 1. Installazione dipendenze richieste...
pip install -r requirements.txt
echo.
echo 2. Compilazione Client Fotografo (AlbumLabPro.exe)...
pyinstaller --noconfirm AlbumLab_Client.spec
echo.
echo 3. Compilazione Server Laboratorio (AlbumLabServer.exe)...
pyinstaller --noconfirm AlbumLab_Server.spec
echo.
echo ========================================================
echo  COMPILAZIONE COMPLETATA CON SUCCESSO!
echo  Troverai gli eseguibili .exe nella cartella 'dist'
echo ========================================================
pause
