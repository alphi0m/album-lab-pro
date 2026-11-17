"""
Punto di ingresso per il Server e la Dashboard Web del Laboratorio Fotografico (Album Lab Server).
Avvia il server di ricezione ordini e la dashboard di produzione su http://localhost:5050/admin.
"""

from src.server.app import start_server

if __name__ == "__main__":
    start_server(host="0.0.0.0", port=5050)
