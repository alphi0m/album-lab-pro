"""
Modulo di trasmissione ordini e sincronizzazione via rete (Client -> Server Laboratorio).
Utilizza upload multipart in streaming con monitoraggio dell'avanzamento byte-per-byte.
"""

import json
import os
import threading
from pathlib import Path
from typing import Callable, Optional
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor
from src.core.exporter import OrderExporter


def check_server_status(server_url: str, timeout: float = 3.0) -> tuple[bool, str]:
    """
    Verifica se il server del laboratorio è raggiungibile e attivo.
    Ritorna (True, 'Server Online') oppure (False, 'Messaggio di errore').
    """
    clean_url = server_url.rstrip("/")
    if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        clean_url = f"http://{clean_url}"

    try:
        url = f"{clean_url}/api/catalog"
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            return True, "Server Laboratorio Online e Raggiungibile"
        return False, f"Server ha risposto con codice HTTP {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Connessione rifiutata: assicurati che il server del laboratorio sia avviato."
    except requests.exceptions.Timeout:
        return False, "Timeout: il server non ha risposto in tempo utile."
    except Exception as e:
        return False, f"Errore di connessione: {e}"


class OrderUploader:
    """
    Gestisce l'esportazione a 300 DPI e la trasmissione in streaming
    dell'ordine verso il server del laboratorio.
    """

    @classmethod
    def upload_order(
        cls,
        server_url: str,
        order_data: dict,
        foto_list: list,
        config: dict,
        progress_callback: Optional[Callable[[str, float, int, int], None]] = None,
        cancel_event: Optional[threading.Event] = None
    ) -> tuple[bool, dict]:
        """
        1. Esporta le foto a 300 DPI con profilo colore nella cartella locale dell'ordine.
        2. Carica in streaming multipart tutti i file e i metadati al server.
        3. Aggiorna lo stato locale dell'ordine con l'ID commessa assegnato dal server.

        :param server_url: URL base del server (es. http://localhost:5000)
        :param order_data: Dizionario con i dati della commessa (busta, cliente, modello, ecc.)
        :param foto_list: Lista di oggetti FotoItem
        :param config: Dizionario di configurazione (DPI, qualità, ecc.)
        :param progress_callback: Callback fn(fase: str, percent: float, bytes_read: int, total_bytes: int)
        :param cancel_event: threading.Event per annullare l'invio
        :return: (True/False, dati_risposta_o_errore)
        """
        clean_url = server_url.rstrip("/")
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = f"http://{clean_url}"

        # -------------------------------------------------------------
        # FASE 1: Esportazione ad alta risoluzione 300 DPI locale
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback("Preparazione ed esportazione stampe a 300 DPI...", 5.0, 0, 0)

        ok_exp, cartella_str = OrderExporter.salva_ordine(order_data, foto_list, config)
        if not ok_exp:
            return False, {"error": f"Errore durante l'esportazione locale delle foto: {cartella_str}"}

        if cancel_event and cancel_event.is_set():
            return False, {"error": "Operazione annullata dall'utente."}

        cartella_ordine = Path(cartella_str)
        json_path = cartella_ordine / "ordine.json"

        # Legge i metadati generati dall'esportazione
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as e:
            return False, {"error": f"Impossibile leggere i metadati dell'ordine esportato: {e}"}

        # -------------------------------------------------------------
        # FASE 2: Preparazione file per l'upload in streaming
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback("Connessione al server del laboratorio...", 15.0, 0, 0)

        # Raccoglie i file di stampa generati
        photo_files = []
        for foto_meta in metadata.get("foto", []):
            filename = foto_meta.get("file_stampa")
            if filename:
                fpath = cartella_ordine / filename
                if fpath.exists():
                    photo_files.append((filename, fpath))

        if not photo_files:
            return False, {"error": "Nessun file fotografico trovato da inviare."}

        opened_file_handles = []
        try:
            fields = [
                ("metadata", json.dumps(metadata, ensure_ascii=False))
            ]

            for filename, fpath in photo_files:
                fh = open(fpath, "rb")
                opened_file_handles.append(fh)
                fields.append(("photos", (filename, fh, "image/jpeg")))

            # Costruisce l'encoder multipart in streaming
            encoder = MultipartEncoder(fields=fields)
            total_bytes = encoder.len

            def monitor_callback(monitor):
                if cancel_event and cancel_event.is_set():
                    raise InterruptedError("Trasmissione annullata dall'utente.")

                pct = 20.0 + (monitor.bytes_read / total_bytes) * 75.0
                mb_read = monitor.bytes_read / (1024 * 1024)
                mb_tot = total_bytes / (1024 * 1024)
                msg = f"Caricamento in corso: {mb_read:.1f} MB / {mb_tot:.1f} MB ({pct:.0f}%)"
                if progress_callback:
                    progress_callback(msg, pct, monitor.bytes_read, total_bytes)

            monitor = MultipartEncoderMonitor(encoder, monitor_callback)

            # Esegue la chiamata POST HTTP
            upload_url = f"{clean_url}/api/orders"
            headers = {"Content-Type": monitor.content_type}

            resp = requests.post(upload_url, data=monitor, headers=headers, timeout=600)

            if resp.status_code in [200, 201]:
                res_data = resp.json()
                order_id = res_data.get("order_id", "")

                # Aggiorna il file ordine.json locale con il tracking server
                metadata["order_id_server"] = order_id
                metadata["stato_trasmissione"] = "INVIATO AL LABORATORIO"
                metadata["data_invio_server"] = res_data.get("data_ricezione", "")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=4, ensure_ascii=False)

                if progress_callback:
                    progress_callback("Completato con successo!", 100.0, total_bytes, total_bytes)

                return True, res_data
            else:
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", resp.text)
                except Exception:
                    err_msg = resp.text
                return False, {"error": f"Errore HTTP {resp.status_code}: {err_msg}"}

        except InterruptedError:
            return False, {"error": "Trasmissione annullata dall'utente."}
        except requests.exceptions.ConnectionError:
            return False, {"error": f"Impossibile collegarsi a {clean_url}. Verifica che il server sia attivo."}
        except requests.exceptions.Timeout:
            return False, {"error": "Timeout durante l'invio dei file fotografici."}
        except Exception as e:
            return False, {"error": f"Errore imprevisto durante l'upload: {e}"}
        finally:
            # Chiude tutti gli handle dei file aperti
            for fh in opened_file_handles:
                try:
                    fh.close()
                except Exception:
                    pass
