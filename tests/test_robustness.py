"""
Test di Robustezza, Casi Limite e Sicurezza per Album Lab Pro:
1. Duplicazione nomi file da fotocamere diverse nello stesso ordine (DSC_0001.jpg)
2. Caratteri speciali/accentati nei nomi file e nel numero busta (es. 12/2026, caffè.jpg)
3. Validazione DPI 300 e salvataggio metadati
4. Gestione errori API server (richieste vuote, json corrotto)
5. Integrità archivio ZIP e scheda commessa
"""

import io
import os
import sys
import json
import time
import shutil
import tempfile
import zipfile
import threading
import requests
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.core.models import FotoItem
from src.core.exporter import OrderExporter
from src.core.catalog import MODELLI_ALBUM, get_modello_by_id
from src.server.app import app
from src.server.storage import ServerStorage
from src.services.network import OrderUploader

TEST_PORT = 5098
SERVER_URL = f"http://127.0.0.1:{TEST_PORT}"


def start_server():
    import werkzeug.serving
    werkzeug.serving.run_simple("127.0.0.1", TEST_PORT, app, threaded=True)


def run_all_robustness_tests():
    print("=" * 75)
    print("AVVIO TEST DI ROBUSTEZZA & CASI LIMITE — ALBUM LAB PRO")
    print("=" * 75)

    # Avvio server di test
    th = threading.Thread(target=start_server, daemon=True)
    th.start()
    time.sleep(1.0)

    temp_test_dir = Path(tempfile.mkdtemp(prefix="album_lab_test_"))

    try:
        # -------------------------------------------------------------
        # TEST 1: Collisione nomi file identici da fotocamere diverse
        # -------------------------------------------------------------
        print("\n[TEST 1] Verifica gestione foto con lo stesso nome file (es. 2 fotocamere)...")
        cam1_dir = temp_test_dir / "camera_a"
        cam2_dir = temp_test_dir / "camera_b"
        cam1_dir.mkdir()
        cam2_dir.mkdir()

        f1_path = cam1_dir / "DSC_0001.JPG"
        f2_path = cam2_dir / "DSC_0001.JPG"

        # Crea immagini test distinte
        Image.new("RGB", (800, 600), color=(255, 0, 0)).save(f1_path, "JPEG")
        Image.new("RGB", (800, 600), color=(0, 0, 255)).save(f2_path, "JPEG")

        item1 = FotoItem(str(f1_path))
        item2 = FotoItem(str(f2_path))

        order_data_1 = {
            "num_busta": "TEST_COLLISION_01",
            "codice_cliente": "CLI_100",
            "nome_cliente": "Studio Fotografico Alfa",
            "nomi_sposi": "Andrea & Chiara",
            "modello_id": "alba",
            "modello_nome": "Alba",
            "formato": "30x30",
            "materiale": "Pelle Vintage",
        }

        ok, exp_path = OrderExporter.salva_ordine(order_data_1, [item1, item2])
        assert ok, f"Esportazione fallita: {exp_path}"

        exp_folder = Path(exp_path)
        exported_files = list(exp_folder.glob("*_stampa.jpg")) + list(exp_folder.glob("*_stampa.JPG"))
        assert len(exported_files) == 2, f"Attesi 2 file esportati, trovati: {len(exported_files)}"
        file_names = {f.name for f in exported_files}
        print(f" -> OK: Nessuna sovrascrittura! File generati: {file_names}")

        # -------------------------------------------------------------
        # TEST 2: Sanificazione numero busta con caratteri vietati (/, :, *, \)
        # -------------------------------------------------------------
        print("\n[TEST 2] Verifica sanificazione cartelle con caratteri vietati...")
        order_data_2 = {
            "num_busta": "Busta 12/2026:Special*Test?",
            "nome_cliente": "Cliente Test",
            "formato": "20x30",
        }
        ok2, exp_path2 = OrderExporter.salva_ordine(order_data_2, [item1])
        assert ok2, f"Fallito export con caratteri speciali: {exp_path2}"
        p2 = Path(exp_path2)
        assert p2.exists(), "Cartella sanificata non creata"
        assert "/" not in p2.name and ":" not in p2.name and "*" not in p2.name and "?" not in p2.name
        print(f" -> OK: Cartella sanificata con successo: '{p2.name}'")
        shutil.rmtree(exp_path2, ignore_errors=True)

        # -------------------------------------------------------------
        # TEST 3: Verifica 300 DPI e profilo colore
        # -------------------------------------------------------------
        print("\n[TEST 3] Verifica metadati 300 DPI nel file di stampa generato...")
        for exp_f in exported_files:
            with Image.open(exp_f) as img:
                dpi = img.info.get("dpi")
                assert dpi == (300, 300), f"DPI errati: {dpi}"
        print(" -> OK: Tutti i file esportati presentano esattamente 300x300 DPI nativi!")
        shutil.rmtree(exp_path, ignore_errors=True)

        # -------------------------------------------------------------
        # TEST 4: Caratteri speciali e accentati nei metadati e nomi file
        # -------------------------------------------------------------
        print("\n[TEST 4] Test trasmissione con nomi accentati (caffè.jpg) e caratteri UTF-8...")
        accent_path = temp_test_dir / "taglio torta & caffè sposi.jpg"
        Image.new("RGB", (1000, 1000), color=(100, 200, 150)).save(accent_path, "JPEG")
        item_accent = FotoItem(str(accent_path))

        order_data_accent = {
            "num_busta": "ACCENTI_TEST",
            "codice_cliente": "CLI_UTF8",
            "nome_cliente": "Fotografo René & François",
            "nomi_sposi": "Éléonore & Nicolò",
            "modello_id": "charme",
            "modello_nome": "Charme",
            "formato": "35x35",
            "materiale": "Tessuto Pregiato Écru",
            "note": "Attenzione ai dettagli doré e all'album genitori in omaggio.",
        }

        ok_up, res_up = OrderUploader.upload_order(
            server_url=SERVER_URL,
            order_data=order_data_accent,
            foto_list=[item_accent],
            config={"dpi_stampa": 300, "qualita_jpeg": 98}
        )
        assert ok_up, f"Upload accentato fallito: {res_up}"
        ord_id = res_up["order_id"]
        print(f" -> OK: Ordine ricevuto con ID: {ord_id}")

        # Verifica sul server
        srv_order = ServerStorage.get_ordine(ord_id)
        assert srv_order["nomi_sposi"] == "Éléonore & Nicolò"
        assert srv_order["materiale_globale"] == "Tessuto Pregiato Écru"
        print(" -> OK: Metadati con accenti preservati al 100% nel database server!")

        # -------------------------------------------------------------
        # TEST 5: Verifica Scheda Commessa A4 e ZIP per ordine accentato
        # -------------------------------------------------------------
        print("\n[TEST 5] Verifica visualizzazione scheda commessa e download ZIP...")
        r_sch = requests.get(f"{SERVER_URL}/admin/orders/{ord_id}/scheda")
        assert r_sch.status_code == 200
        assert "Éléonore & Nicolò" in r_sch.text or "Éléonore &amp; Nicolò" in r_sch.text

        r_zip = requests.get(f"{SERVER_URL}/api/orders/{ord_id}/download")
        assert r_zip.status_code == 200
        assert r_zip.headers.get("Content-Type") == "application/zip"

        with zipfile.ZipFile(io.BytesIO(r_zip.content)) as zf:
            names = zf.namelist()
            assert "riepilogo_ordine.json" in names
            assert any("foto_stampa/" in n for n in names)
        print(" -> OK: Archivio ZIP integro e scheda commessa A4 renderizzata perfettamente!")

        # Pulizia ordine accentato
        ServerStorage.elimina_ordine(ord_id)
        # Pulizia cartella locale
        shutil.rmtree(BASE_DIR / "archivio_ordini" / "ordine_ACCENTI_TEST", ignore_errors=True)

        # -------------------------------------------------------------
        # TEST 6: Protezione API Server contro payload errati o vuoti
        # -------------------------------------------------------------
        print("\n[TEST 6] Verifica sicurezza e risposte HTTP contro richieste anomale...")
        # A. Richiesta POST /api/orders senza file
        r_nofile = requests.post(f"{SERVER_URL}/api/orders", data={"metadata": "{}"})
        assert r_nofile.status_code == 400, f"Atteso 400, ottenuto {r_nofile.status_code}"
        print(" -> OK: Respinta richiesta senza file (HTTP 400)")

        # B. Richiesta POST /api/orders con JSON corrotto
        r_badjson = requests.post(f"{SERVER_URL}/api/orders", data={"metadata": "NON_UN_JSON"})
        assert r_badjson.status_code == 400, f"Atteso 400, ottenuto {r_badjson.status_code}"
        print(" -> OK: Respinta richiesta con JSON corrotto (HTTP 400)")

        # C. Richiesta scheda per ordine inesistente
        r_noord = requests.get(f"{SERVER_URL}/admin/orders/ORD-NONESISTO/scheda")
        assert r_noord.status_code == 404
        print(" -> OK: Ordine inesistente risponde con HTTP 404")

        # -------------------------------------------------------------
        # TEST 7: Verifica catalogo e campionari
        # -------------------------------------------------------------
        print("\n[TEST 7] Verifica catalogo modelli e campionari colori...")
        assert len(MODELLI_ALBUM) == 18, f"Attesi 18 modelli, trovati {len(MODELLI_ALBUM)}"
        for m in MODELLI_ALBUM:
            assert m["id"] and m["nome"] and m["formati"] and m["campionari"]
        print(f" -> OK: Tutti i {len(MODELLI_ALBUM)} modelli della Linea Estro Wedding sono validi e completi!")

        print("\n" + "=" * 75)
        print("TUTTI I TEST DI ROBUSTEZZA E CASI LIMITE SUPERATI CON SUCCESSO! (100% PASS)")
        print("=" * 75)

    finally:
        shutil.rmtree(temp_test_dir, ignore_errors=True)


if __name__ == "__main__":
    run_all_robustness_tests()
