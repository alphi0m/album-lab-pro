"""
Test di verifica per l'evoluzione di dominio:
1. Stampe fotografiche singole (formati, copie, pipeline).
2. Carte minilab (Lucida, Satinata, Seta) con Lucida di default.
3. Box note di lavorazione.
4. Numero busta progressivo e rilevamento conflitti/duplicati.
5. Maschera ritaglio opaca/semi-trasparente (Lightroom style).
6. Ricezione server e rendering dashboard / scheda commessa.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from src.core.constants import FORMATI, CARTE_FOTO, CARTA_FOTO_DEFAULT, MODO_ALBUM, MODO_STAMPE
from src.core.config import ConfigManager
from src.core.models import FotoItem
from src.core.exporter import OrderExporter
from src.server.app import app
from src.server.storage import ServerStorage


class TestDomainEvolution(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_path = self.temp_dir / "config.json"
        self.archivio_dir = self.temp_dir / "archivio_ordini"
        self.archivio_dir.mkdir(parents=True, exist_ok=True)
        self.cfg_mgr = ConfigManager(filepath=self.config_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_formati_e_carte_minilab(self):
        """Verifica la presenza di 10x13, 15x22 e le 3 carte ufficiali minilab con Lucida di default."""
        self.assertIn("10x13", FORMATI)
        self.assertEqual(FORMATI["10x13"], (10, 13))
        self.assertIn("15x22", FORMATI)
        self.assertEqual(FORMATI["15x22"], (15, 22))

        self.assertEqual(CARTE_FOTO, ["Lucida", "Satinata", "Seta"])
        self.assertEqual(CARTA_FOTO_DEFAULT, "Lucida")
        self.assertEqual(MODO_ALBUM, "album")
        self.assertEqual(MODO_STAMPE, "stampe")

    def test_busta_progressiva_e_controllo_conflitti(self):
        """Verifica che il numero busta rilevi conflitti in tempo reale e calcoli il prossimo numero libero."""
        # Nessun ordine presente: prossimo è 1
        prossimo = self.cfg_mgr.trova_prossimo_num_busta(archivio_dir=self.archivio_dir)
        self.assertEqual(prossimo, 1)
        self.assertFalse(self.cfg_mgr.is_busta_in_conflitto("1", archivio_dir=self.archivio_dir))

        # Creiamo cartelle ordini simulate
        (self.archivio_dir / "ordine_001").mkdir()
        (self.archivio_dir / "ordine_002").mkdir()
        (self.archivio_dir / "ordine_005_rossi").mkdir()

        # Verifica conflitto
        self.assertTrue(self.cfg_mgr.is_busta_in_conflitto("001", archivio_dir=self.archivio_dir))
        self.assertTrue(self.cfg_mgr.is_busta_in_conflitto("002", archivio_dir=self.archivio_dir))
        self.assertTrue(self.cfg_mgr.is_busta_in_conflitto("005", archivio_dir=self.archivio_dir))
        self.assertFalse(self.cfg_mgr.is_busta_in_conflitto("003", archivio_dir=self.archivio_dir))

        # Prossimo libero deve essere superiore al massimo esistente (5 -> 6)
        prossimo = self.cfg_mgr.trova_prossimo_num_busta(archivio_dir=self.archivio_dir)
        self.assertEqual(prossimo, 6)

    def test_lut_dimming_crop_mask(self):
        """Verifica che la maschera di ritaglio oscuri lo sfondo (~42%) preservando i dettagli visivi."""
        # Crea immagine di test 200x200 con pixel bianchi (255, 255, 255)
        im = Image.new("RGB", (200, 200), (255, 255, 255))
        lut = [int(p * 0.42) for p in range(256)] * 3
        dimmed = im.point(lut)

        # Il pixel oscurato deve essere int(255 * 0.42) = 107
        expected_val = int(255 * 0.42)
        dimmed_pixel = dimmed.getpixel((10, 10))
        self.assertEqual(dimmed_pixel, (expected_val, expected_val, expected_val))

        # Simuliamo composizione ritaglio: centro 50,50 a 150,150 luminoso
        crop_box = (50, 50, 150, 150)
        composite = dimmed.copy()
        crop_part = im.crop(crop_box)
        composite.paste(crop_part, (50, 50))

        # Pixel esterno deve essere oscurato, pixel interno al ritaglio al 100%
        self.assertEqual(composite.getpixel((10, 10)), (expected_val, expected_val, expected_val))
        self.assertEqual(composite.getpixel((100, 100)), (255, 255, 255))

    def test_esportazione_stampe_fotografiche_singole(self):
        """Verifica l'esportazione a 300 DPI di un ordine di stampe singole con copie differenziate."""
        # Crea foto temporanee
        foto_path1 = self.temp_dir / "scatto_01.jpg"
        foto_path2 = self.temp_dir / "scatto_02.jpg"
        img1 = Image.new("RGB", (1800, 1200), (200, 100, 50))
        img2 = Image.new("RGB", (2400, 1600), (50, 100, 200))
        img1.save(str(foto_path1), "JPEG", quality=95)
        img2.save(str(foto_path2), "JPEG", quality=95)

        item1 = FotoItem(str(foto_path1))
        item1.quantita = 2
        item1.formato = "10x15"
        item1.materiale = "Lucida"

        item2 = FotoItem(str(foto_path2))
        item2.quantita = 3
        item2.formato = "15x20"
        item2.materiale = "Satinata"

        order_data = {
            "num_busta": "999",
            "codice_cliente": "FOTOTEST",
            "nome_cliente": "Studio Test",
            "tipo_servizio": "STAMPE_FOTO",
            "modello_id": "stampe_singole",
            "modello_nome": "Stampe Fotografiche Singole",
            "modello_cofanetto": "Nessuno (Stampe Sciolte)",
            "formato": "10x15",
            "materiale": "Carta Lucida",
            "note": "Tagliare con bordino 3mm su tutte le copie",
            "correzione": True,
        }

        # Sostituiamo temporaneamente ARCHIVIO_DIR con la nostra cartella temporanea
        from src.core import exporter
        old_dir = exporter.ARCHIVIO_DIR
        exporter.ARCHIVIO_DIR = self.archivio_dir
        try:
            ok, res_path = OrderExporter.salva_ordine(order_data, [item1, item2], {"dpi_stampa": 300, "qualita_jpeg": 95})
            self.assertTrue(ok)
            self.assertTrue(Path(res_path).exists())

            # Legge ordine.json
            json_file = Path(res_path) / "ordine.json"
            self.assertTrue(json_file.exists())
            with open(json_file, "r", encoding="utf-8") as f:
                saved_json = json.load(f)

            self.assertEqual(saved_json["num_busta"], "999")
            self.assertEqual(saved_json["tipo_servizio"], "STAMPE_FOTO")
            self.assertEqual(saved_json["totale_foto"], 2)
            self.assertEqual(saved_json["totale_stampe"], 5)  # 2 + 3 = 5 copie totali
            self.assertEqual(saved_json["note"], "Tagliare con bordino 3mm su tutte le copie")
            self.assertTrue(saved_json["correzione"])

            # Controlla che le immagini ritagliate abbiano DPI 300
            file_stampa_1 = Path(res_path) / saved_json["foto"][0]["file_stampa"]
            self.assertTrue(file_stampa_1.exists())
            with Image.open(file_stampa_1) as cimg:
                self.assertEqual(cimg.info.get("dpi"), (300, 300))

        finally:
            exporter.ARCHIVIO_DIR = old_dir

    def test_server_dashboard_e_scheda_stampe_singole(self):
        """Verifica che il server Flask visualizzi correttamente le stampe singole su /admin e /scheda."""
        app.config["TESTING"] = True
        client = app.test_client()

        # Prepariamo un ordine nel ServerStorage
        order_id = ServerStorage.genera_order_id()
        metadata = {
            "order_id": order_id,
            "num_busta": "888",
            "codice_cliente": "CLI01",
            "nome_cliente": "Cliente Stampe",
            "tipo_servizio": "STAMPE_FOTO",
            "modello_id": "stampe_singole",
            "modello_nome": "Stampe Fotografiche Singole",
            "modello_cofanetto": "Nessuno (Stampe Sciolte)",
            "formato_globale": "10x15",
            "materiale_globale": "Carta Lucida",
            "note": "Finitura lucida minilab",
            "correzione": False,
        }

        # Salviamo l'ordine simulato
        ServerStorage.salva_ordine(order_id, metadata, [])

        # 1. Dashboard /admin
        resp_admin = client.get("/admin")
        self.assertEqual(resp_admin.status_code, 200)
        html_admin = resp_admin.data.decode("utf-8")
        self.assertIn("Stampe Singole", html_admin)
        self.assertIn("888", html_admin)
        self.assertIn("Carta Lucida", html_admin)

        # 2. Scheda Commessa /admin/orders/<id>/scheda
        resp_scheda = client.get(f"/admin/orders/{order_id}/scheda")
        self.assertEqual(resp_scheda.status_code, 200)
        html_scheda = resp_scheda.data.decode("utf-8")
        self.assertIn("SCHEDA COMMESSA DI PRODUZIONE", html_scheda)
        self.assertIn("Stampe Fotografiche Singole", html_scheda)
        self.assertIn("Supporto Carta Minilab", html_scheda)
        self.assertIn("Controllo Taglio & Confezionamento Busta", html_scheda)

    def test_bordino_bianco_e_rendering(self):
        """Verifica la persistenza e l'esportazione con bordino bianco 3mm su canvas 300 DPI."""
        foto_path = self.temp_dir / "bordino_test.jpg"
        img = Image.new("RGB", (1200, 800), (255, 0, 0)) # Immagine rossa pura
        img.save(str(foto_path), "JPEG", quality=95)

        item = FotoItem(str(foto_path))
        item.bordino_bianco = True
        item.formato = "10x15"

        # Verifica to_dict e from_dict
        d = item.to_dict()
        self.assertTrue(d.get("bordino_bianco"))
        item_restored = FotoItem.from_dict(d)
        self.assertTrue(item_restored.bordino_bianco)

        # Esportazione
        order_data = {
            "num_busta": "777",
            "codice_cliente": "CLI01",
            "nome_cliente": "Studio Bordino",
            "tipo_servizio": "STAMPE_FOTO",
            "modello_id": "stampe_singole",
            "modello_nome": "Stampe con Bordino",
            "modello_cofanetto": "Nessuno",
            "formato": "10x15",
            "materiale": "Carta Lucida",
            "note": "Test bordo",
            "bordino_bianco": True,
            "correzione": False,
        }

        from src.core import exporter
        old_dir = exporter.ARCHIVIO_DIR
        exporter.ARCHIVIO_DIR = self.archivio_dir
        try:
            ok, res_path = OrderExporter.salva_ordine(order_data, [item], {"dpi_stampa": 300, "qualita_jpeg": 95})
            self.assertTrue(ok)
            json_file = Path(res_path) / "ordine.json"
            with open(json_file, "r", encoding="utf-8") as f:
                saved = json.load(f)

            self.assertTrue(saved.get("bordino_bianco"))
            self.assertTrue(saved["foto"][0]["bordino_bianco"])

            # Controlla l'immagine salvata: gli angoli/bordi esterni devono essere bianchi (255, 255, 255)
            # e l'area interna deve avere il colore originale (rosso 255, 0, 0)
            file_stampa = Path(res_path) / saved["foto"][0]["file_stampa"]
            with Image.open(file_stampa) as out_img:
                w, h = out_img.size
                # Bordo (pixel 5, 5) deve essere bianco (o quasi bianco per quantizzazione JPEG)
                bp = out_img.getpixel((5, 5))
                self.assertGreater(bp[0], 250)
                self.assertGreater(bp[1], 250)
                self.assertGreater(bp[2], 250)
                # Centro deve essere rosso
                cp = out_img.getpixel((w // 2, h // 2))
                self.assertGreater(cp[0], 250)
                self.assertLess(cp[1], 10)
                self.assertLess(cp[2], 10)
        finally:
            exporter.ARCHIVIO_DIR = old_dir

    def test_autenticazione_studio_e_storico_ordini(self):
        """Verifica l'autenticazione fotografo con PIN e l'endpoint di storico ordini protetto."""
        from src.server import storage

        # Configura cartella temporanea per i clienti e gli ordini del server
        old_clients_file = storage.SERVER_CLIENTS_FILE
        old_orders_dir = storage.SERVER_ORDERS_DIR
        storage.SERVER_CLIENTS_FILE = self.temp_dir / "clients.json"
        storage.SERVER_ORDERS_DIR = self.temp_dir / "orders"
        try:
            # Registra un fotografo di test
            ServerStorage.salva_cliente("201", "Studio Fantasia", "9876", "info@fantasia.it")

            # Verifica corretta
            ok, info = ServerStorage.verifica_cliente("201", "9876")
            self.assertTrue(ok)
            self.assertEqual(info["nome_studio"], "Studio Fantasia")

            # Verifica errata (PIN errato)
            ok_err, info_err = ServerStorage.verifica_cliente("201", "0000")
            self.assertFalse(ok_err)
            self.assertIsNone(info_err)

            # Test API Flask
            app.config["TESTING"] = True
            client = app.test_client()

            # POST /api/auth/verify OK
            res_auth = client.post("/api/auth/verify", json={"codice": "201", "pin": "9876"})
            self.assertEqual(res_auth.status_code, 200)
            data_auth = res_auth.get_json()
            self.assertTrue(data_auth["success"])
            self.assertEqual(data_auth["nome_studio"], "Studio Fantasia")

            # POST /api/auth/verify KO
            res_auth_ko = client.post("/api/auth/verify", json={"codice": "201", "pin": "wrong"})
            self.assertEqual(res_auth_ko.status_code, 401)
            self.assertFalse(res_auth_ko.get_json()["success"])

            # Aggiungiamo ordini appartenenti a 201 e a un altro cliente
            order_id_1 = ServerStorage.genera_order_id()
            ServerStorage.salva_ordine(order_id_1, {
                "order_id": order_id_1,
                "codice_cliente": "201",
                "nome_cliente": "Studio Fantasia",
                "num_busta": "1001",
                "tipo_servizio": "STAMPE_FOTO",
                "totale_foto": 10,
                "bordino_bianco": True,
            }, [])

            order_id_2 = ServerStorage.genera_order_id()
            ServerStorage.salva_ordine(order_id_2, {
                "order_id": order_id_2,
                "codice_cliente": "999", # Altro cliente
                "nome_cliente": "Altro Studio",
                "num_busta": "1002",
                "tipo_servizio": "ALBUM",
                "totale_foto": 50,
                "bordino_bianco": False,
            }, [])

            # GET /api/orders/history protetto
            res_hist = client.get("/api/orders/history?codice=201&pin=9876")
            self.assertEqual(res_hist.status_code, 200)
            hist_data = res_hist.get_json()
            self.assertTrue(hist_data["success"])
            self.assertEqual(len(hist_data["ordini"]), 1)
            self.assertEqual(hist_data["ordini"][0]["num_busta"], "1001")
            self.assertTrue(hist_data["ordini"][0]["bordino_bianco"])

            # Accesso con PIN errato a /api/orders/history deve fallire
            res_hist_ko = client.get("/api/orders/history?codice=201&pin=0000")
            self.assertEqual(res_hist_ko.status_code, 401)
        finally:
            storage.SERVER_CLIENTS_FILE = old_clients_file
            storage.SERVER_ORDERS_DIR = old_orders_dir


if __name__ == "__main__":
    unittest.main()
