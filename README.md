# 📸 ALBUM LAB PRO — Studio & Lab Management System

Sistema professionale completo per fotografi e laboratori di stampa fotografica artigianale.
Include il catalogo ufficiale **Officine dei Ricordi — Linea Estro Wedding** (18 modelli), editor di ritaglio a 300 DPI con preservazione del profilo colore ICC, trasmissione telematica degli ordini e dashboard web di produzione.

---

## 📁 Struttura del Progetto

```
album-lab/
├── main.py                     # Entry point applicazione Desktop Fotografo (Client)
├── server.py                   # Entry point Server Laboratorio & Dashboard Web
├── requirements.txt            # Dipendenze Python
├── build_mac.sh                # Script compilazione macOS (.app e .dmg)
├── build_windows.bat           # Script compilazione Windows (.exe)
├── GUIDA_CLIENT_SERVER.md      # Guida completa architettura, test e collaudo
│
├── src/
│   ├── core/                   # Modelli di business, catalogo e logica di esportazione
│   │   ├── catalog.py          # Definizione 18 modelli Estro Wedding e campionari
│   │   ├── config.py           # Gestione configurazioni cross-platform
│   │   ├── constants.py        # Formati stampa e percorsi compatibili PyInstaller
│   │   ├── exporter.py         # Esportazione 300 DPI con profilo ICC e JSON
│   │   └── models.py           # FotoItem (EXIF auto-rotate, crop box, coordinate)
│   │
│   ├── server/                 # Server Flask e Dashboard di produzione
│   │   ├── app.py              # API REST, Dashboard Web Dark Studio e Scheda A4
│   │   └── storage.py          # Gestione commesse ricevute e generazione ZIP
│   │
│   ├── services/               # Comunicazione di rete
│   │   └── network.py          # Streaming multipart byte-by-byte e monitor upload
│   │
│   └── ui/                     # Interfaccia grafica Desktop (Dark Studio Style)
│       ├── archive.py          # Gestione archivio locale ordini passati
│       ├── catalog_dialog.py   # Galleria visuale catalogo con filtri di ricerca
│       ├── editor.py           # Canvas fotografico con griglia terzi e crop box
│       ├── main_window.py      # Finestra principale Album Lab Pro
│       ├── panels.py           # Pannelli laterali dinamici (Modello, Formati, Materiali, Dati)
│       ├── theme.py            # Tavolozza colori Photoshop / Lightroom Dark Studio
│       ├── thumbnails.py       # Griglia miniature responsive con badge di stato
│       └── upload_dialog.py    # Modale invio ordine con progress bar e test server
│
├── media/                      # Immagini di catalogo e campionari estratti
│   └── models/                 # 323 immagini estratte dal catalogo PDF
│
├── tests/                      # Suite di test automatizzati
│   └── test_e2e_orders.py      # Test E2E trasmissione, ZIP, scheda A4 e stati
│
├── assets/                     # Icone e risorse grafiche dell'applicazione
├── LICENSE                     # Licenza d'uso proprietaria a scopo portfolio
└── requirements.txt            # Dipendenze Python
```

---

## 💡 Punti Chiave di Ingegneria Software

- **Elaborazione Immagini a 300 DPI con ICC Profile:** Il motore di ritaglio non ricampiona distruttivamente l'immagine, ma applica le coordinate normalizzate sulla risoluzione nativa e conserva inalterato il profilo colore ICC originale (sRGB, Adobe RGB, ProPhoto).
- **Architettura Client-Server in Streaming:** Upload multipart progressivo con calcolo in tempo reale di throughput e percentuale di avanzamento (`requests-toolbelt`).
- **Dashboard Web in Tempo Reale:** Backend Flask integrato per il laboratorio con foglio commessa A4 stampabile (barcode generato dinamicamente, specifiche sposi e firme di conformità).
- **Interfaccia Dark Studio HiDPI:** UI reattiva con calcolo dinamico della scala DPI per schermi Retina e 4K, ispirata ai flussi di lavoro di Photoshop e Lightroom.

---

## ⚡ Avvio Rapido

### 1. Avvio Client Fotografo
```bash
python main.py
```

### 2. Avvio Server Laboratorio
```bash
python server.py
```
Accedi alla Dashboard di gestione su: `http://localhost:5000/admin`

---

## 🧪 Esecuzione Test Automatizzati
Per eseguire il test di integrazione end-to-end completo:
```bash
python tests/test_e2e_orders.py
```

---

## 📜 Licenza
Questo progetto è distribuito a scopo dimostrativo e di portfolio personale. Tutti i diritti sono riservati. Consultare il file `LICENSE` per maggiori dettagli.
