# 📸 Album Lab Pro — Guida Architettura Client / Server & Collaudo

Questa guida spiega nel dettaglio il funzionamento del sistema **Client / Server** di **Album Lab Pro**, come avviarlo, come testarlo in locale o a distanza con il laboratorio (l'amico committente), e come sono strutturati i pacchetti eseguibili (.dmg per macOS e .exe per Windows).

---

## 🏛️ 1. Architettura del Sistema

Il sistema è suddiviso in due componenti indipendenti ma perfettamente sincronizzate:

```
┌─────────────────────────────────┐                 ┌─────────────────────────────────┐
│     CLIENT FOTOGRAFO            │                 │     SERVER LABORATORIO          │
│   (Album Lab Pro Desktop)       │                 │   (Album Lab Server & Web)      │
│                                 │                 │                                 │
│ • Sfoglia Catalogo Ufficiale    │                 │ • Ricezione streaming ordini    │
│ • Vincoli Formati & Campionari  │  POST /api/...  │ • Web Dashboard (/admin)        │
│ • Editor Ritagli 300 DPI + ICC  │ ──────────────> │ • Generazione ZIP per Minilab   │
│ • Dati Sposi, Busta, Cliente    │  HTTP Streaming │ • Scheda Commessa A4 (Barcode)  │
│ • Dialogo Invio con Progress %  │                 │ • Gestione Stati di Produzione  │
└─────────────────────────────────┘                 └─────────────────────────────────┘
```

---

## 🚀 2. Come Avviare e Testare il Sistema (Test Locale)

### Passo 1: Avviare il Server del Laboratorio
Sul computer del laboratorio (o su una finestra del terminale):
```bash
python server.py
```
*(Oppure cliccando sull'eseguibile `AlbumLabServer`)*

Il server si avvierà sulla porta `5050` (evitando conflitti con AirPlay su Mac).
Puoi aprire immediatamente il browser su:
👉 **`http://localhost:5050/admin`**

Vedrai la **Dashboard di Produzione Dark Studio**:
- Contatori in tempo reale: *Commesse Ricevute*, *In Attesa*, *In Lavorazione*, *Completati*.
- Tabella ordini auto-aggiornante ogni 15 secondi.

---

### Passo 2: Avviare l'Applicazione del Fotografo (Client)
Apri una seconda finestra o clicca su `AlbumLabPro.app` (oppure da terminale):
```bash
python main.py
```

1. Clicca su **"📖 Sfoglia Catalogo Album"**:
   - Scegli uno dei 18 modelli ufficiali della Linea Estro Wedding (es. *Estro Butterfly Lumina* o *EVO*).
   - I formati compatibili e le collezioni colore (Vellutino, Canapina, Tacto, Wood, Tweed, Zebrano, Spigato, Coagulato) si configureranno automaticamente in base al modello.
2. Clicca su **"📂 Carica Foto"**:
   - Carica le foto del servizio fotografico.
   - Posiziona il ritaglio con la griglia dei terzi e orienta con `Spazio` o `R`.
3. Nel pannello a destra inserisci:
   - **Busta N°** e **Codice / Nome Fotografo**.
   - **Nomi Sposi** (es. *Federico & Beatrice*) per l'incisione su copertina.
4. Clicca sul pulsante **"🚀 INVIA AL LABORATORIO"** nella barra superiore:
   - Si aprirà la finestra di dialogo di trasmissione.
   - Il client verifica istantaneamente la raggiungibilità del server (`🟢 Server Online`).
   - Clicca su **"🚀 Invia Commessa Adesso"**:
     - *Fase 1:* Esporta i ritagli a **piena risoluzione 300 DPI preservando il profilo colore ICC originale**.
     - *Fase 2:* Trasmette in streaming multipart i file fotografici e i metadati con barra di avanzamento reale `XX MB / YY MB (ZZ%)`.
     - *Fase 3:* Assegna il codice univoco commessa (es. `ORD-20261116_224500-123`).

---

### Passo 3: Ricezione e Lavorazione nel Laboratorio
Torna sulla pagina Web del laboratorio (`http://localhost:5050/admin`):
1. **Nuovo Ordine Visibile:** L'ordine compare subito in tabella con badge colorato 🟡 `IN ATTESA`.
2. **Scheda Commessa A4:** Clicca sul pulsante **"🖨️ Scheda"** per aprire e stampare il foglio di lavoro pronto per il banco di legatoria, con codice a barre, nomi degli sposi in evidenza, modello album, copertina e firme di controllo.
3. **Download ZIP Minilab:** Clicca su **"📥 ZIP"** per scaricare l'archivio contenente tutte le foto già ritagliate a 300 DPI + il file JSON riepilogativo.
4. **Avanzamento Lavorazione:** Cambia il menu a tendina da `IN ATTESA` ➔ `IN STAMPA` ➔ `IN LEGATORIA` ➔ `PRONTO`.

---

## 🌐 3. Come Testare a Distanza (Fotografo a casa, Laboratorio in sede)

Se tu e il tuo amico siete su due computer diversi e non sulla stessa rete Wi-Fi:

### Metodo A: Con Cloudflare Tunnel (Gratuito, Sicuro, Nessuna configurazione router)
Sul computer del laboratorio (dove gira `python server.py`):
1. Scarica [Cloudflare Tunnel (cloudflared)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/).
2. Esegui semplicemente:
   ```bash
   cloudflared tunnel --url http://localhost:5050
   ```
3. Il terminale genererà un link pubblico sicuro del tipo:
   `https://random-subdomain.trycloudflare.com`
4. Il tuo amico apre quel link per vedere la Dashboard, e tu nel Client inserisci quell'indirizzo nel campo *"Indirizzo Server Laboratorio"*. Fatto! Tutti gli ordini voleranno da casa tua al suo computer via Internet!

### Metodo B: Con Ngrok
```bash
ngrok http 5050
```
Fornisce un link pubblico `https://...ngrok-free.app` da inserire nel client.

---

## 📦 4. Pacchetti Eseguibili Standalone (.dmg e .exe)

### Per macOS (Apple Silicon & Intel)
Abbiamo già compilato e creato il pacchetto disco nativo:
- **`dist/AlbumLabPro.dmg`** (67 MB): contiene l'app completa `AlbumLabPro.app`.
- **`dist/AlbumLabServer/AlbumLabServer`**: eseguibile del server per il laboratorio.
- Per ricompilare in qualsiasi momento su Mac basta eseguire:
  ```bash
  ./build_mac.sh
  ```

### Per Windows (.exe)
Per compilare la versione per Windows:
1. Copia la cartella del progetto su un computer Windows (o macchina virtuale).
2. Fai doppio clic sul file già pronto:
   👉 **`build_windows.bat`**
3. Lo script installerà automaticamente i requisiti e genererà in `dist/`:
   - `AlbumLabPro.exe` (App Client per i fotografi)
   - `AlbumLabServer.exe` (Server per il laboratorio)
