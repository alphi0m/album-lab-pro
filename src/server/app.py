"""
Server API & Dashboard Web per il Laboratorio Fotografico (Album Lab Server).
Fornisce le API REST per la ricezione degli ordini e la dashboard di produzione per il laboratorio.
"""

import json
from pathlib import Path
from flask import Flask, request, jsonify, send_file, send_from_directory, render_template_string, redirect, url_for
from src.core.catalog import MODELLI_ALBUM, CAMPIONARI_COLORI
from src.server.storage import ServerStorage, SERVER_ORDERS_DIR

app = Flask(__name__)
# Limite upload file (fino a 2 GB per ordini fotografici pesanti)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024


# =============================================================================
# TEMPLATE HTML5: DASHBOARD WEB LABORATORIO (STILE DARK STUDIO)
# =============================================================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Album Lab — Dashboard Laboratorio</title>
    <style>
        :root {
            --bg-dark: #121316;
            --bg-app: #18191C;
            --bg-card: #22242A;
            --bg-hover: #2D3038;
            --primary: #0078FF;
            --success: #2ECC71;
            --warning: #F39C12;
            --purple: #9B59B6;
            --text-main: #EDEDED;
            --text-muted: #8F96A0;
            --border: #2F323A;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg-app); color: var(--text-main); min-height: 100vh; }
        
        /* Header */
        header { background: var(--bg-card); border-bottom: 1px solid var(--border); padding: 14px 24px; display: flex; justify-content: space-between; align-items: center; }
        .brand { display: flex; align-items: center; gap: 10px; }
        .brand h1 { font-size: 1.15rem; font-weight: 700; color: #fff; letter-spacing: 0.5px; }
        .brand-badge { background: var(--primary); color: #fff; font-size: 0.7rem; font-weight: 800; padding: 2px 7px; border-radius: 4px; }
        .live-status { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--text-muted); }
        .pulse-dot { width: 8px; height: 8px; background: var(--success); border-radius: 50%; box-shadow: 0 0 8px var(--success); }

        /* Container */
        .container { max-width: 1300px; margin: 0 auto; padding: 24px; }
        .top-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .stat-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 18px; }
        .stat-card h3 { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px; }
        .stat-card .val { font-size: 1.8rem; font-weight: 700; color: #fff; }

        /* Table */
        .card-table { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
        .table-header { padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .table-header h2 { font-size: 1rem; font-weight: 600; }
        .btn-refresh { background: var(--bg-hover); color: var(--text-main); border: 1px solid var(--border); padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }
        .btn-refresh:hover { background: #383C46; }

        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }
        th { background: #1C1E23; padding: 12px 18px; color: var(--text-muted); font-size: 0.78rem; text-transform: uppercase; border-bottom: 1px solid var(--border); }
        td { padding: 14px 18px; border-bottom: 1px solid var(--border); vertical-align: middle; }
        tr:hover { background: rgba(255,255,255,0.02); }

        /* Badges */
        .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; }
        .badge-attesa { background: rgba(243, 156, 18, 0.15); color: #F39C12; border: 1px solid rgba(243, 156, 18, 0.4); }
        .badge-stampa { background: rgba(0, 120, 255, 0.15); color: #0078FF; border: 1px solid rgba(0, 120, 255, 0.4); }
        .badge-legatoria { background: rgba(155, 89, 182, 0.15); color: #9B59B6; border: 1px solid rgba(155, 89, 182, 0.4); }
        .badge-pronto { background: rgba(46, 204, 113, 0.15); color: #2ECC71; border: 1px solid rgba(46, 204, 113, 0.4); }

        /* Action Buttons */
        .btn-group { display: flex; gap: 8px; }
        .btn-action { text-decoration: none; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; cursor: pointer; border: none; display: inline-flex; align-items: center; gap: 5px; }
        .btn-download { background: var(--primary); color: #fff; }
        .btn-download:hover { background: #0060CC; }
        .btn-scheda { background: #2A2D35; color: #fff; border: 1px solid var(--border); }
        .btn-scheda:hover { background: #383C46; }
        .btn-danger { background: rgba(231, 76, 60, 0.2); color: #E74C3C; border: 1px solid rgba(231, 76, 60, 0.4); }
        .btn-danger:hover { background: #E74C3C; color: #fff; }

        select.status-select { background: #18191C; color: var(--text-main); border: 1px solid var(--border); padding: 5px 8px; border-radius: 5px; font-size: 0.8rem; cursor: pointer; transition: border-color 0.2s; }
        .toast-msg {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #2ECC71;
            color: #fff;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            display: none;
            z-index: 9999;
        }
    </style>
</head>
<body>
    <div id="toast" class="toast-msg"></div>

    <header>
        <div class="brand">
            <h1>ALBUM LAB</h1>
            <span class="brand-badge">LABORATORIO</span>
        </div>
        <div class="live-status">
            <span class="pulse-dot"></span>
            <span>Server di Produzione Attivo (Porta {{ port }})</span>
        </div>
    </header>

    <div class="container">
        <div class="top-stats">
            <div class="stat-card">
                <h3>Commesse Ricevute</h3>
                <div class="val">{{ ordini|length }}</div>
            </div>
            <div class="stat-card">
                <h3>In Attesa di Stampa</h3>
                <div class="val">{{ ordini|selectattr('stato', 'equalto', 'IN ATTESA')|list|length }}</div>
            </div>
            <div class="stat-card">
                <h3>In Lavorazione</h3>
                <div class="val">{{ ordini|selectattr('stato', 'equalto', 'IN STAMPA')|list|length + ordini|selectattr('stato', 'equalto', 'IN LEGATORIA')|list|length }}</div>
            </div>
            <div class="stat-card">
                <h3>Completati / Pronti</h3>
                <div class="val" style="color: var(--success);">{{ ordini|selectattr('stato', 'equalto', 'PRONTO')|list|length }}</div>
            </div>
        </div>

        <div class="card-table">
            <div class="table-header">
                <h2>📥 Elenco Ordini di Produzione in Tempo Reale</h2>
                <button class="btn-refresh" onclick="location.reload()">🔄 Aggiorna Lista</button>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID Ordine</th>
                        <th>Data Ricezione</th>
                        <th>Fotografo / Cliente</th>
                        <th>Modello Album & Formato</th>
                        <th>Materiale Copertina</th>
                        <th>Foto HD</th>
                        <th>Stato Commessa</th>
                        <th>Azioni di Produzione</th>
                    </tr>
                </thead>
                <tbody>
                    {% for o in ordini %}
                    <tr>
                        <td>
                            <strong>{{ o.order_id }}</strong><br>
                            <small style="color: var(--text-muted);">Busta: {{ o.num_busta }}</small>
                        </td>
                        <td>{{ o.data_ricezione }}</td>
                        <td>
                            <strong>{{ o.nome_cliente or '—' }}</strong><br>
                            <small style="color: var(--text-muted);">Cod: {{ o.codice_cliente or '—' }}</small>
                            {% if o.nomi_sposi %}
                            <br><small style="color: #66B2FF;">💍 Sposi: {{ o.nomi_sposi }}</small>
                            {% endif %}
                        </td>
                        <td>
                            <strong style="color: #66B2FF;">{{ o.modello_nome or 'Stampe Sfuse' }}</strong><br>
                            <small>{{ o.formato_globale }}</small>
                        </td>
                        <td>
                            <small>{{ o.materiale_globale }}</small>
                        </td>
                        <td>
                            <strong>{{ o.totale_file }} foto</strong>
                        </td>
                        <td>
                            <select class="status-select" data-current="{{ o.stato }}" onchange="aggiornaStato(this, '{{ o.order_id }}')">
                                <option value="IN ATTESA" {% if o.stato|upper|trim == 'IN ATTESA' %}selected{% endif %}>🟡 In Attesa</option>
                                <option value="IN STAMPA" {% if o.stato|upper|trim == 'IN STAMPA' %}selected{% endif %}>🔵 In Stampa</option>
                                <option value="IN LEGATORIA" {% if o.stato|upper|trim == 'IN LEGATORIA' %}selected{% endif %}>🟣 In Legatoria</option>
                                <option value="PRONTO" {% if o.stato|upper|trim == 'PRONTO' %}selected{% endif %}>🟢 Pronto / Spedito</option>
                            </select>
                        </td>
                        <td>
                            <div class="btn-group">
                                <a href="/api/orders/{{ o.order_id }}/download" class="btn-action btn-download" title="Scarica file ritagliati a 300 DPI">
                                    📥 ZIP
                                </a>
                                <a href="/admin/orders/{{ o.order_id }}/scheda" target="_blank" class="btn-action btn-scheda" title="Stampa scheda commessa A4 con barcode">
                                    🖨️ Scheda
                                </a>
                                <button onclick="eliminaOrdine('{{ o.order_id }}')" class="btn-action btn-danger" title="Elimina commessa">
                                    🗑️
                                </button>
                            </div>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="8" style="text-align: center; padding: 40px; color: var(--text-muted);">
                            Nessun ordine ricevuto al momento. Invia un ordine dall'applicazione fotografo per vederlo comparire qui!
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let reloadTimer = null;
        function resetReloadTimer() {
            if (reloadTimer) clearTimeout(reloadTimer);
            reloadTimer = setTimeout(() => location.reload(), 15000);
        }
        resetReloadTimer();

        function showToast(text, isError = false) {
            const toast = document.getElementById('toast');
            toast.textContent = text;
            toast.style.background = isError ? '#E74C3C' : '#2ECC71';
            toast.style.display = 'block';
            setTimeout(() => { toast.style.display = 'none'; }, 2500);
        }

        function aggiornaStato(selectElem, orderId) {
            const vecchioStato = selectElem.getAttribute('data-current') || selectElem.value;
            const nuovoStato = selectElem.value;
            selectElem.disabled = true;
            resetReloadTimer();

            fetch(`/api/orders/${orderId}/status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ stato: nuovoStato })
            })
            .then(res => res.json())
            .then(data => {
                selectElem.disabled = false;
                if(data.success) {
                    selectElem.setAttribute('data-current', nuovoStato);
                    selectElem.style.borderColor = '#2ECC71';
                    showToast(`✓ Stato aggiornato: ${nuovoStato}`);
                    setTimeout(() => { selectElem.style.borderColor = ''; }, 2000);
                } else {
                    selectElem.value = vecchioStato;
                    showToast('Errore durante il salvataggio!', true);
                }
            })
            .catch(err => {
                selectElem.disabled = false;
                selectElem.value = vecchioStato;
                showToast('Errore di connessione!', true);
            });
        }

        function eliminaOrdine(orderId) {
            if (confirm('Sei sicuro di voler eliminare la commessa ' + orderId + '?\nQuesta operazione rimuoverà definitivamente anche le foto archiviate sul server.')) {
                fetch('/api/orders/' + orderId, { method: 'DELETE' })
                    .then(res => res.json())
                    .then(data => {
                        if(data.success) {
                            location.reload();
                        } else {
                            alert('Errore eliminazione commessa');
                        }
                    });
            }
        }
    </script>
</body>
</html>
"""


# =============================================================================
# TEMPLATE SCHEDA COMMESSA DA STAMPARE (FOGLIO A4 CON BARCODE)
# =============================================================================
SCHEDA_COMMESSA_HTML = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Scheda Commessa — {{ ordine.order_id }}</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 30px; color: #111; max-width: 800px; margin: auto; }
        .header { display: flex; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 20px; }
        .title h1 { font-size: 22px; margin: 0; }
        .title p { margin: 4px 0 0; color: #555; font-size: 12px; }
        .barcode { text-align: right; font-family: monospace; font-size: 16px; font-weight: bold; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .box { border: 1px solid #ccc; padding: 12px; border-radius: 4px; }
        .box h3 { font-size: 12px; text-transform: uppercase; color: #666; margin: 0 0 6px; }
        .box p { font-size: 14px; margin: 0; font-weight: bold; }
        .box-highlight { border: 2px solid #000; background: #f9f9f9; }
        .notes { border: 1px dashed #666; padding: 12px; margin-bottom: 20px; min-height: 60px; }
        .signatures { display: flex; justify-content: space-between; margin-top: 40px; }
        .sign-box { width: 45%; border-top: 1px solid #000; padding-top: 6px; text-align: center; font-size: 12px; }
        @media print {
            body { padding: 0; }
            .btn-print { display: none; }
        }
    </style>
</head>
<body>
    <button class="btn-print" onclick="window.print()" style="padding: 10px 20px; background: #0078FF; color: #fff; border: none; border-radius: 5px; cursor: pointer; margin-bottom: 20px; font-weight: bold;">
        🖨️ Stampa Scheda Commessa (A4)
    </button>

    <div class="header">
        <div class="title">
            <h1>SCHEDA COMMESSA DI PRODUZIONE</h1>
            <p>Laboratorio Fotografico & Legatoria Artigianale</p>
        </div>
        <div class="barcode">
            ||| |||| || |||||||| |||||<br>
            {{ ordine.order_id }}<br>
            <span style="font-size: 12px; color: #444;">Busta: N° {{ ordine.num_busta }}</span>
        </div>
    </div>

    <div class="grid">
        <div class="box">
            <h3>Fotografo / Committente</h3>
            <p>{{ ordine.nome_cliente or '—' }} (Cod. {{ ordine.codice_cliente or '—' }})</p>
        </div>
        <div class="box">
            <h3>Data Ricezione</h3>
            <p>{{ ordine.data_ricezione }}</p>
        </div>
        <div class="box box-highlight">
            <h3>Modello Album da Costruire</h3>
            <p style="font-size: 16px; color: #0066cc;">{{ ordine.modello_nome or 'Stampe Fotografiche' }}</p>
            <p style="font-size: 12px; font-weight: normal; margin-top: 4px;">Formato: <strong>{{ ordine.formato_globale }}</strong></p>
        </div>
        <div class="box box-highlight">
            <h3>Materiale & Colore Copertina</h3>
            <p style="font-size: 15px;">{{ ordine.materiale_globale }}</p>
            {% if ordine.modello_cofanetto %}
            <p style="font-size: 12px; font-weight: normal; margin-top: 4px;">Cofanetto: {{ ordine.modello_cofanetto }}</p>
            {% endif %}
        </div>
    </div>

    {% if ordine.nomi_sposi %}
    <div class="box" style="margin-bottom: 20px; background: #fffbf0; border-color: #f1c40f;">
        <h3 style="color: #b78103;">💍 Incisione Nomi Sposi (su copertina / cofanetto)</h3>
        <p style="font-size: 18px; letter-spacing: 1px;">{{ ordine.nomi_sposi }}</p>
    </div>
    {% endif %}

    <div class="box" style="margin-bottom: 20px;">
        <h3>Dettagli di Stampa & Risoluzione</h3>
        <p>Totale File Fotografici: <strong>{{ ordine.totale_file }} scatti</strong> (Qualità 300 DPI con profilo colore ICC)</p>
        <p style="font-size: 12px; font-weight: normal; margin-top: 4px;">Correzione Minilab: <strong>{{ 'ATTIVA' if ordine.correzione else 'DISATTIVA' }}</strong></p>
    </div>

    <div class="notes">
        <h3 style="font-size: 11px; text-transform: uppercase; color: #666; margin: 0 0 4px;">Note e Istruzioni Operative:</h3>
        <p style="font-size: 13px; font-weight: normal;">{{ ordine.note or 'Nessuna annotazione particolare.' }}</p>
    </div>

    <div class="signatures">
        <div class="sign-box">Controllo Stampa Minilab (Firma)</div>
        <div class="sign-box">Controllo Legatoria & Confezionamento (Firma)</div>
    </div>
</body>
</html>
"""


# =============================================================================
# ROTTE SERVER API & DASHBOARD
# =============================================================================

@app.route("/")
def index():
    return redirect(url_for("admin_dashboard"))


@app.route("/admin")
def admin_dashboard():
    """Dashboard visuale web per l'amico del laboratorio."""
    ordini = ServerStorage.get_tutti_ordini()
    port = app.config.get("SERVER_PORT", 5050)
    return render_template_string(DASHBOARD_HTML, ordini=ordini, port=port)


@app.route("/admin/orders/<order_id>/scheda")
def scheda_commessa(order_id):
    """Genera la scheda commessa A4 pronta per la stampa con barcode."""
    ordine = ServerStorage.get_ordine(order_id)
    if not ordine:
        return "Ordine non trovato", 404
    return render_template_string(SCHEDA_COMMESSA_HTML, ordine=ordine)


@app.route("/api/catalog", methods=["GET"])
def api_catalog():
    """Restituisce il catalogo ufficiale e i campionari per la sincronizzazione dei client."""
    return jsonify({
        "success": True,
        "modelli": MODELLI_ALBUM,
        "campionari": CAMPIONARI_COLORI
    })


@app.route("/api/orders", methods=["GET"])
def api_get_orders():
    """Elenco di tutti gli ordini ricevuti."""
    ordini = ServerStorage.get_tutti_ordini()
    return jsonify({"success": True, "ordini": ordini})


@app.route("/api/orders", methods=["POST"])
def api_post_order():
    """
    Riceve un nuovo ordine dal fotografo (Client).
    Accetta un payload multipart contenente i metadati JSON e i file fotografici ad alta risoluzione.
    """
    try:
        # Preleva i metadati JSON inviati nel campo 'metadata'
        metadata_str = request.form.get("metadata", "{}")
        try:
            metadata = json.loads(metadata_str)
        except Exception:
            return jsonify({"success": False, "error": "Formato metadati JSON non valido."}), 400

        # Preleva tutti i file fotografici inviati
        uploaded_files = request.files.getlist("photos")
        if not uploaded_files:
            return jsonify({"success": False, "error": "Nessun file fotografico allegato all'ordine."}), 400

        # Genera un ID commessa univoco
        order_id = ServerStorage.genera_order_id()

        # Salva ordine e foto
        folder = ServerStorage.salva_ordine(order_id, metadata, uploaded_files)

        return jsonify({
            "success": True,
            "order_id": order_id,
            "message": "Ordine ricevuto e archiviato con successo nel laboratorio!",
            "totale_file": len(uploaded_files)
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/orders/<order_id>/status", methods=["POST"])
def api_update_status(order_id):
    """Aggiorna lo stato di lavorazione dell'ordine (IN STAMPA, IN LEGATORIA, PRONTO)."""
    data = request.get_json() or {}
    nuovo_stato = data.get("stato", "")
    ok = ServerStorage.aggiorna_stato(order_id, nuovo_stato)
    return jsonify({"success": ok})


@app.route("/api/orders/<order_id>/download", methods=["GET"])
def api_download_print_zip(order_id):
    """Permette al laboratorio di scaricare l'archivio ZIP con tutti i file pronti per la stampa."""
    zip_path = ServerStorage.crea_zip_stampa(order_id)
    if not zip_path or not zip_path.exists():
        return jsonify({"success": False, "error": "File non trovato"}), 404

    return send_file(
        str(zip_path),
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"ORDINE_{order_id}_STAMPA.zip"
    )


@app.route("/admin/orders/<order_id>/photos/<path:filename>")
def admin_order_photo(order_id, filename):
    """Serve una foto specifica della commessa per anteprima."""
    folder = SERVER_ORDERS_DIR / order_id / "photos"
    return send_from_directory(str(folder), filename)


@app.route("/api/orders/<order_id>", methods=["DELETE"])
def api_delete_order(order_id):
    """Elimina definitivamente una commessa dal server del laboratorio."""
    ok = ServerStorage.elimina_ordine(order_id)
    return jsonify({"success": ok})


def start_server(host="0.0.0.0", port=5050):
    """Avvia il server Flask verificando la disponibilità della porta."""
    import socket
    def is_port_free(p):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", p)) != 0

    target_port = port
    while not is_port_free(target_port) and target_port < port + 20:
        target_port += 1

    app.config["SERVER_PORT"] = target_port
    print(f"\n🚀 Server Album Lab avviato su http://localhost:{target_port}/admin")
    app.run(host=host, port=target_port, debug=False)


if __name__ == "__main__":
    start_server()
