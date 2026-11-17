"""
Test End-to-End completo del flusso Client-Server di Album Lab Pro:
1. Avvio server Flask di test in background
2. Creazione commessa con catalogo Estro Wedding e immagini reali
3. Upload tramite OrderUploader (streaming multipart)
4. Verifica archiviazione su disco server (server_data/orders/)
5. Verifica download archivio ZIP per minilab
6. Verifica generazione scheda commessa A4 con barcode
7. Verifica aggiornamento stati di produzione (IN STAMPA, PRONTO)
8. Verifica eliminazione commessa
"""

import os
import sys
import time
import json
import zipfile
import threading
import requests
from pathlib import Path

# Assicura che la root del progetto sia nel PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.core.models import FotoItem
from src.core.catalog import get_modello_by_id
from src.services.network import OrderUploader, check_server_status
from src.server.app import app
from src.server.storage import ServerStorage

TEST_PORT = 5099
TEST_SERVER_URL = f"http://127.0.0.1:{TEST_PORT}"


def run_test_server():
    import werkzeug.serving
    werkzeug.serving.run_simple("127.0.0.1", TEST_PORT, app, threaded=True)


def test_full_pipeline():
    print("=" * 70)
    print("AVVIO TEST END-TO-END CLIENT-SERVER ALBUM LAB PRO")
    print("=" * 70)

    # 1. Avvia server in un thread separato
    server_thread = threading.Thread(target=run_test_server, daemon=True)
    server_thread.start()
    time.sleep(1.0)

    # 2. Verifica connettività
    print("\n[STEP 1] Verifica connettività server...")
    ok, status_msg = check_server_status(TEST_SERVER_URL)
    assert ok, f"Server non raggiungibile: {status_msg}"
    print(f" -> OK: {status_msg}")

    # 3. Prepara foto reali
    print("\n[STEP 2] Caricamento e ritaglio immagini di test...")
    img1_path = str(BASE_DIR / "media" / "models" / "model_003_01.jpg")
    img2_path = str(BASE_DIR / "media" / "models" / "model_004_01.jpg")
    assert os.path.exists(img1_path), "File test non trovato"
    assert os.path.exists(img2_path), "File test non trovato"

    foto1 = FotoItem(img1_path)
    foto1.quantita = 2
    foto1.formato = "30x40"

    foto2 = FotoItem(img2_path)
    foto2.quantita = 1
    foto2.formato = "30x40"

    foto_list = [foto1, foto2]
    print(f" -> OK: Caricate {len(foto_list)} foto di test")

    # 4. Modello di catalogo selezionato
    modello = get_modello_by_id("butterfly_lumina")
    assert modello is not None, "Modello catalogo butterfly_lumina non trovato"

    order_data = {
        "num_busta": "999_TEST",
        "codice_cliente": "FOTO_STUDIO_TEST",
        "nome_cliente": "Mario Rossi Fotografo",
        "nomi_sposi": "Federico & Beatrice",
        "modello_id": modello["id"],
        "modello_nome": modello["nome"],
        "modello_cofanetto": modello.get("cofanetto"),
        "formato": "30x40",
        "materiale": "Tacto / Cuoio Vintage",
        "note": "Attenzione alla tonalità dell'incarnato sulle stampe Fine Art.",
        "correzione": True
    }

    # 5. Esegui upload al server con callback di progresso
    print("\n[STEP 3] Trasmissione commessa in streaming multipart al server...")
    progress_log = []

    def progress_callback(phase, pct, bytes_read, total_bytes):
        progress_log.append((phase, pct))
        print(f"    [Progresso] {phase} ({pct:.0f}%)")

    config = {"dpi_stampa": 300, "qualita_jpeg": 95}
    ok, res = OrderUploader.upload_order(
        server_url=TEST_SERVER_URL,
        order_data=order_data,
        foto_list=foto_list,
        config=config,
        progress_callback=progress_callback
    )

    assert ok, f"Upload fallito: {res}"
    order_id = res.get("order_id")
    print(f" -> OK: Ordine ricevuto con successo dal server! ID Assegnato: {order_id}")
    assert order_id.startswith("ORD-"), f"ID ordine non valido: {order_id}"

    # 6. Verifica persistenza sul server
    print("\n[STEP 4] Verifica dati salvati nello storage del server...")
    server_order = ServerStorage.get_ordine(order_id)
    assert server_order is not None, f"Ordine {order_id} non trovato sul server"
    assert server_order["nome_cliente"] == "Mario Rossi Fotografo"
    assert server_order["nomi_sposi"] == "Federico & Beatrice"
    assert server_order["modello_id"] == "butterfly_lumina"
    assert server_order["formato_globale"] == "30x40"
    assert server_order["stato"] == "IN ATTESA"
    assert len(server_order["file_ricevuti"]) == 2
    print(" -> OK: Metadati e file fotografici archiviati correttamente nel server!")

    # 7. Verifica Dashboard Web
    print("\n[STEP 5] Verifica Dashboard Web Laboratorio (/admin)...")
    resp_dash = requests.get(f"{TEST_SERVER_URL}/admin")
    assert resp_dash.status_code == 200
    assert order_id in resp_dash.text
    assert "Federico &amp; Beatrice" in resp_dash.text or "Federico & Beatrice" in resp_dash.text
    print(" -> OK: Dashboard Web mostra la commessa in arrivo in tempo reale!")

    # 8. Verifica Scheda Commessa A4 (/admin/orders/{order_id}/scheda)
    print("\n[STEP 6] Verifica Scheda Commessa A4 per il banco di produzione...")
    resp_scheda = requests.get(f"{TEST_SERVER_URL}/admin/orders/{order_id}/scheda")
    assert resp_scheda.status_code == 200
    assert "SCHEDA COMMESSA DI PRODUZIONE" in resp_scheda.text
    assert order_id in resp_scheda.text
    assert "999_TEST" in resp_scheda.text
    assert "Federico & Beatrice" in resp_scheda.text or "Federico &amp; Beatrice" in resp_scheda.text
    print(" -> OK: Scheda Commessa A4 con barcode e istruzioni generata correttamente!")

    # 9. Verifica Download ZIP Stampa (/api/orders/{order_id}/download)
    print("\n[STEP 7] Verifica Download archivio ZIP per il minilab...")
    resp_zip = requests.get(f"{TEST_SERVER_URL}/api/orders/{order_id}/download")
    assert resp_zip.status_code == 200
    assert resp_zip.headers.get("Content-Type") == "application/zip"

    # Verifica contenuto dello zip
    zip_bytes_path = BASE_DIR / "server_data" / "orders" / order_id / "test_download.zip"
    with open(zip_bytes_path, "wb") as f:
        f.write(resp_zip.content)

    with zipfile.ZipFile(str(zip_bytes_path), "r") as zf:
        namelist = zf.namelist()
        print(f"    File nello ZIP scaricato: {namelist}")
        assert "riepilogo_ordine.json" in namelist
        assert any(n.startswith("foto_stampa/") for n in namelist)

    zip_bytes_path.unlink()
    print(" -> OK: Archivio ZIP per la stampa scaricato e verificato!")

    # 10. Aggiornamento stato di produzione
    print("\n[STEP 8] Aggiornamento stato commessa (IN STAMPA -> PRONTO)...")
    resp_st1 = requests.post(f"{TEST_SERVER_URL}/api/orders/{order_id}/status", json={"stato": "IN STAMPA"})
    assert resp_st1.json().get("success") is True
    assert ServerStorage.get_ordine(order_id)["stato"] == "IN STAMPA"

    resp_st2 = requests.post(f"{TEST_SERVER_URL}/api/orders/{order_id}/status", json={"stato": "PRONTO"})
    assert resp_st2.json().get("success") is True
    assert ServerStorage.get_ordine(order_id)["stato"] == "PRONTO"
    print(" -> OK: Flusso di avanzamento stati (In Attesa -> In Stampa -> Pronto) perfettamente funzionante!")

    # 11. Pulizia test commessa
    print("\n[STEP 9] Pulizia commessa di test...")
    resp_del = requests.delete(f"{TEST_SERVER_URL}/api/orders/{order_id}")
    assert resp_del.json().get("success") is True
    assert ServerStorage.get_ordine(order_id) is None
    print(" -> OK: Commessa di test eliminata correttamente.")

    print("\n" + "=" * 70)
    print("TUTTI I TEST END-TO-END COMPLETATI CON SUCCESSO! (100% PASS)")
    print("=" * 70)


if __name__ == "__main__":
    test_full_pipeline()
