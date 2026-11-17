# 📸 ALBUM LAB PRO — Photography Studio & Lab Management System

<p align="center">
  <img src="assets/icon.png" width="128" height="128" alt="Album Lab Pro Icon" style="border-radius: 24px; box-shadow: 0 8px 24px rgba(0,0,0,0.5);">
</p>

<p align="center">
  <strong>Piattaforma Desktop & Server per la gestione della produzione fotografica di alta gamma, cataloghi album nozze, ritaglio calibrato a 300 DPI con gestione profili ICC e trasmissione ordini in tempo reale.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Architecture-Client%20%2F%20Server-0078FF?style=for-the-badge" alt="Client-Server">
  <img src="https://img.shields.io/badge/GUI-Dark%20Studio%20HiDPI-22242A?style=for-the-badge" alt="Dark Studio GUI">
  <img src="https://img.shields.io/badge/Print%20Engine-300%20DPI%20%2B%20ICC-2ECC71?style=for-the-badge" alt="300 DPI + ICC">
  <img src="https://img.shields.io/badge/Testing-E2E%20100%25%20Pass-brightgreen?style=for-the-badge" alt="Tests 100% Pass">
  <img src="https://img.shields.io/badge/License-Proprietary%20%2F%20Portfolio-red?style=for-the-badge" alt="Proprietary License">
</p>

---

## 🎯 Il Problema & La Soluzione

Nel settore dei laboratori fotografici e della legatoria artigianale di album matrimoniali, la comunicazione tra fotografo e stampatore è storicamente problematica:
- Invio di file tramite servizi esterni (WeTransfer, Drive) senza specifiche tecniche formattate.
- Disallineamento dei formati e tagli errati delle teste degli sposi o dei dettagli critici.
- Alterazioni cromatiche causate dalla perdita dei profili colore originali durante la compressione.
- Errori umani nella trascrizione dei nomi degli sposi per l'incisione e nella scelta dei campionari di tessuto o pelle della copertina.

**Album Lab Pro** risolve questi problemi unificando il flusso in due componenti sincronizzate:
1. **Client Desktop per il Fotografo:** applicazione grafica *Dark Studio* per comporre l'ordine, selezionare il modello dal catalogo vincolando materiali e formati consentiti, ritagliare le immagini a 300 DPI preservando lo spazio colore nativo e trasmettere la commessa via streaming.
2. **Server & Dashboard Web per il Laboratorio:** server centralizzato che riceve l'ordine in streaming, visualizza i lavori in arrivo su una dashboard aggiornata in tempo reale, genera la **Scheda Commessa A4 stampabile con codice a barre** e compila automaticamente l'archivio ZIP pronto per i minilab di stampa.

---

## 🏛️ Architettura di Sistema

```
┌────────────────────────────────────────┐                 ┌────────────────────────────────────────┐
│         CLIENT FOTOGRAFO               │                 │         SERVER LABORATORIO             │
│       (Album Lab Pro Desktop)          │                 │     (Flask API & Web Dashboard)        │
│                                        │                 │                                        │
│  • Galleria Catalogo (18 Modelli)      │  HTTP POST      │  • Storage Commesse (server_data/)     │
│  • Motore Vincoli Formati & Materiali  │  Multipart      │  • Dashboard Produzione (/admin)       │
│  • Editor Ritagli (300 DPI + ICC)      │  Streaming      │  • Scheda Commessa A4 con Barcode      │
│  • Dati Sposi, Busta e Note Tecniche   │ ──────────────> │  • Generatore ZIP Stampe per Minilab   │
│  • Modale Upload con Monitoraggio MB/% │  (Chunked)      │  • Macchina a Stati (Attesa->Pronto)   │
└────────────────────────────────────────┘                 └────────────────────────────────────────┘
```

---

## 💡 Punti Chiave di Ingegneria Software

### 1. Elaborazione Immagini Non Distruttiva & Profilo Colore ICC
- **Calibrazione a 300 DPI:** I ritagli non scalano l'immagine visibile a schermo, ma mappano le coordinate relative normalizzate sulla matrice dell'immagine nativa ad alta risoluzione (24-50+ MP).
- **Integrità Cromatica ICC:** Preservazione trasparente del payload binario del profilo colore nativo (sRGB, Adobe RGB 1998, ProPhoto RGB) durante la scrittura JPEG, prevenendo qualsiasi "color-shift" nei plotter professionali e nei minilab a ioduro d'argento.
- **Normalizzazione Aspect Ratio:** Algoritmo per rilevare e avvisare in caso di disallineamento geometrico tra il sensore fotografico (es. 3:2) e il formato di stampa selezionato (es. 4:5 o quadrato 1:1).

### 2. Motore Dinamico del Catalogo Prodotti (18 Modelli)
- Implementazione del dataset completo della linea ufficiale con vincoli condizionali rigidi:
  - Formati ammessi dipendenti dal modello (quadrati, panoramici, verticali).
  - Tipi di carta interna compatibili (*Lucide, Satinate, Velvet HD, Tela Fine Art*).
  - Campionari colore abbinati (*Vellutino, Canapina, Tacto, Wood, Tweed, Zebrano, Spigato, Coagulato*).
  - Supporto per campi personalizzati dedicati (es. incisione a caldo dei nomi degli sposi e finitura cofanetto).

### 3. Pipeline di Rete con Streaming Multipart e Monitoraggio Byte-by-Byte
- Modulo di trasmissione (`src/services/network.py`) basato su `requests-toolbelt`:
  - Streaming a blocchi per commesse fotografiche pesanti (fino a centinaia di megabyte o gigabyte) evitando l'esaurimento della memoria RAM.
  - Callback di monitoraggio che aggiorna in tempo reale la percentuale e i megabyte trasferiti (`X MB / Y MB`).
  - Threading asincrono disaccoppiato dall'interfaccia utente con supporto per l'interruzione pulita (*cancellation token*).

### 4. Interfaccia Grafica Dark Studio HiDPI / Retina
- Palette cromatica professionale (`#121316`, `#18191C`, `#0078FF`) studiata per evitare l'affaticamento visivo e non alterare la percezione dei colori fotografici.
- Calcolo automatico della scala DPI (`tk scaling`) per garantire pulsanti generosi (36-38px) e tipografia nitida sia su schermi Apple Retina che su monitor PC 1080p/2K/4K.

---

## 🛠️ Stack Tecnologico

| Componente | Tecnologia | Ruolo & Funzione |
|---|---|---|
| **Linguaggio** | Python 3.10+ | Linguaggio principale dell'intero stack |
| **Interfaccia Desktop** | Tkinter / TTK + Pillow | Canvas fotografico interattivo, gallerie responsive |
| **Backend & API** | Flask | Endpoint RESTful e rendering server-side dashboard |
| **Image Processing** | PIL / Pillow | Decodifica EXIF, rotazione senza perdita, salvataggio 300 DPI + ICC |
| **Network Streaming** | Requests & Requests-Toolbelt | Upload multipart streaming ad alte prestazioni |
| **Packaging** | PyInstaller | Compilazione standalone macOS (.app/.dmg) e Windows (.exe) |
| **Test Automation** | Python Standard / Requests | Test suite end-to-end con simulazione server/client reale |

---

## 📁 Struttura della Codebase

```
album-lab/
├── main.py                     # Entry point applicazione Desktop Fotografo (Client)
├── server.py                   # Entry point Server Laboratorio & Dashboard Web
├── requirements.txt            # Dipendenze Python
├── build_mac.sh                # Script di compilazione per macOS (.app e .dmg)
├── build_windows.bat           # Script di compilazione per Windows (.exe)
├── GUIDA_CLIENT_SERVER.md      # Manuale operativo di collaudo locale e remoto
├── LICENSE                     # Licenza d'uso proprietaria (Showcase)
│
├── assets/                     # Icone native multi-risoluzione (.icns, .ico, .png)
│
├── src/
│   ├── core/                   # Logica di dominio, catalogo e math di ritaglio
│   │   ├── catalog.py          # Definizione modelli, campionari e vincoli
│   │   ├── config.py           # Gestione configurazioni cross-platform
│   │   ├── constants.py        # Tabella formati stampa e risoluzione percorsi
│   │   ├── exporter.py         # Esportazione ad alta risoluzione 300 DPI + ICC
│   │   └── models.py           # Modello FotoItem (EXIF auto-rotate, crop box normalizzato)
│   │
│   ├── server/                 # Backend del laboratorio e interfaccia di produzione
│   │   ├── app.py              # API REST, Dashboard Web Dark Studio e Scheda A4
│   │   └── storage.py          # Archiviazione commesse, aggiornamento stati, generatore ZIP
│   │
│   ├── services/               # Comunicazione telematica
│   │   └── network.py          # Streaming multipart e monitoraggio upload progressivo
│   │
│   └── ui/                     # Componenti visuali Desktop
│       ├── archive.py          # Consultazione e ricerca archivio ordini locale
│       ├── catalog_dialog.py   # Galleria visuale con schede prodotto e anteprime
│       ├── editor.py           # Canvas con griglia dei terzi e rotazione orientamento
│       ├── main_window.py      # Finestra principale Album Lab Pro
│       ├── panels.py           # Pannelli laterali dinamici vincolati al catalogo
│       ├── theme.py            # Tema Dark Studio con calcolo automatico HiDPI
│       ├── thumbnails.py       # Griglia miniature fluida con badge quantità e warning
│       └── upload_dialog.py    # Modale di trasmissione con progress bar e test server
│
├── media/                      # Asset grafici e foto del catalogo prodotti
│   └── models/                 # Immagini ufficiali dei modelli album
│
└── tests/                      # Suite di test automatizzati
    └── test_e2e_orders.py      # Test E2E del flusso Client -> Server -> ZIP -> Scheda A4
```

---

## ⚡ Avvio & Utilizzo Rapido

### 1. Avvio dell'Applicazione Client (Fotografo)
```bash
python main.py
```
- Sfoglia il catalogo cliccando su **"📖 Sfoglia Catalogo Album"**.
- Carica le foto con **"📂 Carica Foto (Ctrl+O)"** o trascinale nell'editor.
- Inserisci i dati della busta e i nomi degli sposi.
- Clicca su **"🚀 INVIA AL LABORATORIO"** per trasmettere la commessa.

### 2. Avvio del Server del Laboratorio (Stampatore)
```bash
python server.py
```
Accedi dal browser alla Dashboard di produzione:
👉 **`http://localhost:5050/admin`**
- Visualizza gli ordini in tempo reale.
- Clicca su **"🖨️ Scheda"** per stampare il foglio di lavoro A4 con barcode per il banco di legatoria.
- Clicca su **"📥 ZIP"** per scaricare tutte le foto già ritagliate a 300 DPI.
- Aggiorna lo stato di lavorazione da `IN ATTESA` a `IN STAMPA`, `IN LEGATORIA`, `PRONTO`.

---

## 🧪 Qualità del Codice & Test Automatizzati

La codebase include una suite di test end-to-end che valida l'intera pipeline di produzione (connessione, calibrazione file 300 DPI, streaming multipart, persistenza JSON, generazione ZIP e scheda A4):

```bash
python tests/test_e2e_orders.py
```

Output:
```text
======================================================================
AVVIO TEST END-TO-END CLIENT-SERVER ALBUM LAB PRO
======================================================================
[STEP 1] Verifica connettività server...           -> OK: Server Online
[STEP 2] Caricamento e ritaglio immagini test...   -> OK: Caricate 2 foto
[STEP 3] Trasmissione commessa in streaming...     -> OK: Ricevuta (ORD-20261117_...)
[STEP 4] Verifica dati salvati nello storage...    -> OK: Metadati e file HD archiviati
[STEP 5] Verifica Dashboard Web Laboratorio...     -> OK: Mostrata in tempo reale
[STEP 6] Verifica Scheda Commessa A4...            -> OK: Generata con barcode
[STEP 7] Verifica Download ZIP Stampa...           -> OK: ZIP valido con foto 300 DPI
[STEP 8] Aggiornamento stato commessa...           -> OK: IN STAMPA -> PRONTO
[STEP 9] Pulizia commessa di test...               -> OK: Eliminata
======================================================================
TUTTI I TEST END-TO-END COMPLETATI CON SUCCESSO! (100% PASS)
======================================================================
```

---

## 📜 Licenza & Diritti

Questo repository è pubblicato **esclusivamente a scopo dimostrativo e di portfolio personale**. Tutti i diritti di proprietà intellettuale, design e codice sorgente appartengono all'autore. È espressamente vietata la riproduzione commerciale, la redistribuzione di binari compilati e l'impiego non autorizzato in ambienti di produzione. Consultare il file `LICENSE` per maggiori dettagli.
