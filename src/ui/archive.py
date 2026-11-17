"""
Finestra dell'Archivio Ordini in stile Dark Studio con ricerca e gestione commesse.
"""

import json
import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from src.core.constants import ARCHIVIO_DIR
from src.core.config import open_folder
from src.core.models import FotoItem
from src.ui.theme import (
    BG_APP, BG_CARD, BG_INPUT, PRIMARY, TEXT_PRIMARY, TEXT_MUTED, BORDER_COLOR
)


class ArchivioOrdiniWindow(tk.Toplevel):
    """Finestra di consultazione e gestione dell'archivio ordini in stile Dark Studio."""

    def __init__(self, master, main_app):
        super().__init__(master)
        self.main_app = main_app
        self.title("Album Lab Pro — Archivio Ordini")
        self.geometry("1080x660")
        self.minsize(800, 480)
        self.configure(bg=BG_APP)

        # Barra superiore: Ricerca e contatore
        top_bar = tk.Frame(self, bg=BG_APP, height=50, highlightbackground=BORDER_COLOR, highlightthickness=1)
        top_bar.pack(fill="x", padx=10, pady=(10, 6))

        tk.Label(top_bar, text="🔍 Cerca Commessa:", bg=BG_APP, fg=TEXT_PRIMARY, font=("Helvetica", 10, "bold")).pack(side="left", padx=(12, 8), pady=10)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filtra_ordini())
        entry_search = ttk.Entry(top_bar, textvariable=self.search_var, width=32, font=("Helvetica", 10))
        entry_search.pack(side="left", pady=10)

        self.lbl_totale = tk.Label(top_bar, text="", bg=BG_APP, fg=PRIMARY, font=("Helvetica", 10, "bold"))
        self.lbl_totale.pack(side="right", padx=16, pady=10)

        # Tabella ordini (Treeview scuro)
        table_frame = tk.Frame(self, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1)
        table_frame.pack(fill="both", expand=True, padx=8, pady=4)

        columns = ("busta", "modello", "cliente", "data", "formato", "stampe", "note", "cartella")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("busta", text="Busta N°")
        self.tree.heading("modello", text="Modello Album")
        self.tree.heading("cliente", text="Nome Cliente")
        self.tree.heading("data", text="Data e Ora")
        self.tree.heading("formato", text="Formato")
        self.tree.heading("stampe", text="Stampe Totali")
        self.tree.heading("note", text="Note")
        self.tree.heading("cartella", text="Percorso Cartella")

        self.tree.column("busta", width=80, anchor="center")
        self.tree.column("modello", width=150, anchor="w")
        self.tree.column("cliente", width=150, anchor="w")
        self.tree.column("data", width=140, anchor="center")
        self.tree.column("formato", width=90, anchor="center")
        self.tree.column("stampe", width=90, anchor="center")
        self.tree.column("note", width=150, anchor="w")
        self.tree.column("cartella", width=200, anchor="w")

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Barra inferiore pulsanti
        btn_bar = tk.Frame(self, bg=BG_APP, height=44)
        btn_bar.pack(fill="x", padx=8, pady=8)

        ttk.Button(btn_bar, text="📂 Apri Cartella", style="TButton", command=self.apri_cartella_selezionata).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="📥 Carica nell'Editor", style="Primary.TButton", command=self.carica_ordine_selezionato).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="🗑️ Elimina Ordine", style="TButton", command=self.elimina_ordine_selezionato).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="🔄 Ricarica", style="TButton", command=self.carica_lista_ordini).pack(side="left", padx=4)

        ttk.Button(btn_bar, text="Chiudi", style="TButton", command=self.destroy).pack(side="right", padx=4)

        self.ordini_cache = []
        self.carica_lista_ordini()

    def carica_lista_ordini(self):
        self.ordini_cache.clear()
        ARCHIVIO_DIR.mkdir(parents=True, exist_ok=True)

        for folder in ARCHIVIO_DIR.iterdir():
            if not folder.is_dir():
                continue
            json_file = folder / "ordine.json"
            if not json_file.exists():
                continue

            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    ordine = json.load(f)
                    ordine["_folder_path"] = str(folder)
                    self.ordini_cache.append(ordine)
            except Exception as e:
                print(f"Errore lettura {json_file}: {e}")

        self.ordini_cache.sort(key=lambda x: x.get("data", ""), reverse=True)
        self.filtra_ordini()

    def filtra_ordini(self):
        query = self.search_var.get().strip().lower()

        for item in self.tree.get_children():
            self.tree.delete(item)

        count = 0
        for ord_data in self.ordini_cache:
            busta = str(ord_data.get("num_busta", ""))
            cliente = str(ord_data.get("nome_cliente", ""))
            note = str(ord_data.get("note", ""))

            modello = str(ord_data.get("modello_nome", "—"))

            if query and (query not in busta.lower() and query not in cliente.lower() and query not in note.lower() and query not in modello.lower()):
                continue

            count += 1
            self.tree.insert("", "end", values=(
                f"Busta {busta}",
                modello or "—",
                cliente or "—",
                ord_data.get("data", "—"),
                ord_data.get("formato_globale", "—"),
                ord_data.get("totale_stampe", len(ord_data.get("foto", []))),
                note or "—",
                ord_data.get("_folder_path", "")
            ))

        self.lbl_totale.config(text=f"Totale commesse: {count}")

    def _get_selected_order(self) -> dict | None:
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Attenzione", "Seleziona prima un ordine dalla lista.")
            return None

        vals = self.tree.item(selected_item[0], "values")
        folder_path = vals[-1]

        for o in self.ordini_cache:
            if o.get("_folder_path") == folder_path:
                return o
        return None

    def apri_cartella_selezionata(self):
        ordine = self._get_selected_order()
        if ordine:
            open_folder(ordine["_folder_path"])

    def carica_ordine_selezionato(self):
        ordine = self._get_selected_order()
        if not ordine:
            return

        self.main_app.info_panel.num_busta_var.set(ordine.get("num_busta", ""))
        self.main_app.info_panel.codice_cliente_var.set(ordine.get("codice_cliente", ""))
        self.main_app.info_panel.nome_cliente_var.set(ordine.get("nome_cliente", ""))
        self.main_app.info_panel.nomi_sposi_var.set(ordine.get("nomi_sposi", ""))
        self.main_app.info_panel.note_text.delete("1.0", "end")
        self.main_app.info_panel.note_text.insert("1.0", ordine.get("note", ""))
        self.main_app.info_panel.correzione_var.set(ordine.get("correzione", False))

        # Ripristina Modello dal Catalogo se presente
        mod_id = ordine.get("modello_id")
        if mod_id:
            from src.core.catalog import get_modello_by_id
            mod_obj = get_modello_by_id(mod_id)
            if mod_obj:
                self.main_app.imposta_modello_scelto(mod_obj)

        if ordine.get("formato_globale"):
            self.main_app.formati_panel.set_formato(ordine["formato_globale"])

        new_foto_list = []
        for f_data in ordine.get("foto", []):
            path_file = f_data.get("path_originale")
            if not path_file or not os.path.exists(path_file):
                local_path = os.path.join(ordine["_folder_path"], f_data.get("file_stampa", ""))
                if os.path.exists(local_path):
                    path_file = local_path

            if path_file and os.path.exists(path_file):
                try:
                    item = FotoItem(path_file)
                    item.quantita = f_data.get("quantita", 1)
                    item.formato = f_data.get("formato", "")
                    item.materiale = f_data.get("materiale", "")
                    if "crop_box" in f_data:
                        item.crop_box = tuple(f_data["crop_box"])
                        item.has_custom_crop = f_data.get("has_custom_crop", False)
                    new_foto_list.append(item)
                except Exception as e:
                    print(f"Errore ripristino foto {path_file}: {e}")

        self.main_app.foto_list = new_foto_list
        self.main_app.miniature_panel.set_foto_items(new_foto_list)
        if new_foto_list:
            self.main_app.set_foto_corrente(0)
        else:
            self.main_app.editor_panel.clear()

        messagebox.showinfo("Ordine Caricato", f"Ordine Busta {ordine.get('num_busta')} caricato nell'editor!")
        self.destroy()

    def elimina_ordine_selezionato(self):
        ordine = self._get_selected_order()
        if not ordine:
            return

        busta = ordine.get("num_busta", "")
        conferma = messagebox.askyesno(
            "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare definitivamente l'ordine Busta {busta} e tutti i suoi file?",
            icon="warning"
        )
        if conferma:
            try:
                shutil.rmtree(ordine["_folder_path"])
                messagebox.showinfo("Eliminato", "Ordine rimosso dall'archivio.")
                self.carica_lista_ordini()
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile eliminare l'ordine:\n{e}")
