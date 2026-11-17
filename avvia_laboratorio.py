"""
Avviatore All-in-One per il Laboratorio Fotografico (Album Lab Pro).
1. Avvia il server locale di produzione sulla porta 5050.
2. Avvia automaticamente il tunnel Cloudflare sicuro verso Internet.
3. Se cloudflared non è presente, lo scarica in automatico in pochi secondi.
4. Salva il link pubblico in 'LINK_PER_I_FOTOGRAFI.txt' pronto da inviare.
5. Apre la Dashboard di produzione nel browser predefinito.
"""

import os
import sys
import time
import re
import shutil
import platform
import subprocess
import webbrowser
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TOOLS_DIR = BASE_DIR / "tools"
PORT = 5050


def download_cloudflared() -> Path | None:
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    os_name = platform.system().lower()
    machine = platform.machine().lower()

    if os_name == "windows":
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        dest = TOOLS_DIR / "cloudflared.exe"
    elif os_name == "darwin":
        if "arm" in machine or "m1" in machine or "m2" in machine or "m3" in machine or "m4" in machine:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64"
        else:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64"
        dest = TOOLS_DIR / "cloudflared"
    else:
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        dest = TOOLS_DIR / "cloudflared"

    if dest.exists():
        return dest

    print("Scarico il componente di rete Cloudflare Tunnel (richiesto solo al primo avvio)...")
    try:
        urllib.request.urlretrieve(url, str(dest))
        if os_name != "windows":
            dest.chmod(0o755)
        print("Componente installato con successo!")
        return dest
    except Exception as e:
        print(f"Errore download automatico: {e}")
        return None


def find_cloudflared() -> str | None:
    # 1. Controlla se è nel PATH di sistema
    system_path = shutil.which("cloudflared")
    if system_path:
        return system_path

    # 2. Controlla nella cartella tools/
    os_name = platform.system().lower()
    local_bin = TOOLS_DIR / ("cloudflared.exe" if os_name == "windows" else "cloudflared")
    if local_bin.exists():
        return str(local_bin)

    # 3. Prova a scaricarlo
    downloaded = download_cloudflared()
    if downloaded and downloaded.exists():
        return str(downloaded)

    return None


def main():
    print("=" * 72)
    print("      ALBUM LAB PRO — AVVIO SISTEMA LABORATORIO (CLOUD & LOCALE)")
    print("=" * 72)
    print("\n[1/3] Avvio del server di produzione...")

    # Individua l'eseguibile Python
    py_exec = sys.executable

    # Avvia il server Flask in background
    server_process = subprocess.Popen(
        [py_exec, "server.py"],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    time.sleep(1.5)

    print("\n[2/3] Connessione al Cloudflare Tunnel per accesso via Internet...")
    cf_bin = find_cloudflared()

    public_url = None
    tunnel_process = None

    if cf_bin:
        try:
            tunnel_process = subprocess.Popen(
                [cf_bin, "tunnel", "--url", f"http://localhost:{PORT}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Cerca il link generato nei log di cloudflared
            start_time = time.time()
            while time.time() - start_time < 15:
                line = tunnel_process.stdout.readline()
                if not line:
                    continue
                # Cerca pattern tipo: https://....trycloudflare.com
                match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if match:
                    public_url = match.group(0)
                    break
        except Exception as e:
            print(f"Nota: Impossibile avviare il tunnel automatico: {e}")
    else:
        print("Tunnel non disponibile al momento. Il server è comunque attivo in locale.")

    # [3/3] Mostra schermata riassuntiva
    print("\n" + "=" * 72)
    print("  🚀 LABORATORIO ATTIVO E PRONTO A RICEVERE ORDINI!")
    print("=" * 72)

    if public_url:
        print("\n👉 INDIRIZZO SERVER PER L'APP DEI FOTOGRAFI:")
        print(f"   \033[1;32m{public_url}\033[0m")
        print("   (Questo indirizzo serve all'app desktop del fotografo per sapere dove inviare i file)")

        # Salva su file TXT per comodità
        link_file = BASE_DIR / "INDIRIZZO_SERVER_PER_FOTOGRAFI.txt"
        with open(link_file, "w", encoding="utf-8") as f:
            f.write(
                f"INDIRIZZO SERVER LABORATORIO (ALBUM LAB PRO):\n\n"
                f"{public_url}\n\n"
                f"Come usarlo nell'App Fotografo:\n"
                f"1. Apri l'app desktop Album Lab Pro (non serve aprire il browser!).\n"
                f"2. Prepara l'album e clicca sul pulsante 'Invia al Laboratorio'.\n"
                f"3. Incolla questo indirizzo nel campo 'Indirizzo Server Laboratorio' (l'app lo memorizza automaticamente).\n"
                f"4. Clicca su 'Trasmetti Ordine Ora' e i file voleranno direttamente al laboratorio!\n"
            )
        print(f"\n   [✓] L'indirizzo e le istruzioni sono stati salvati in: {link_file.name}")
    else:
        print(f"\n👉 INDIRIZZO LOCALE (Stesso Wi-Fi): http://localhost:{PORT}")

    print(f"\n👉 LA TUA DASHBOARD DI PRODUZIONE: http://localhost:{PORT}/admin")
    print("   (Apertura automatica nel browser in corso...)")
    print("=" * 72)
    print("\nPremi CTRL+C per arrestare il server quando hai finito.")

    # Apre la dashboard nel browser
    webbrowser.open(f"http://localhost:{PORT}/admin")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArresto del server e del tunnel in corso...")
        if tunnel_process:
            tunnel_process.terminate()
        server_process.terminate()
        print("Tutto arrestato con successo. A presto!")


if __name__ == "__main__":
    main()
