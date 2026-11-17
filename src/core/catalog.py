"""
Catalogo Ufficiale dei Prodotti — Linea Estro Wedding (Officine dei Ricordi).
Definisce i 18 modelli con relative schede tecniche, vincoli di formato, campionari colore e opzioni personalizzate.
"""

from pathlib import Path
from src.core.constants import BASE_DIR

# =============================================================================
# CAMPIONARI TESSUTI, PELLI E MATERIALI
# =============================================================================
CAMPIONARI_COLORI = {
    "Vellutino": [
        {"codice": "700", "nome": "Burro"},
        {"codice": "701", "nome": "Avorio"},
        {"codice": "702", "nome": "Sabbia"},
        {"codice": "703", "nome": "Mogano"},
        {"codice": "704", "nome": "Lilla"},
        {"codice": "705", "nome": "Cipria"},
        {"codice": "706", "nome": "Rosso Fiamma"},
        {"codice": "707", "nome": "Pastello"},
        {"codice": "708", "nome": "Azzurro"},
        {"codice": "709", "nome": "Oltremare"},
        {"codice": "710", "nome": "Nero"},
        {"codice": "711", "nome": "Grigio Bambù"},
        {"codice": "712", "nome": "Safari"},
        {"codice": "713", "nome": "Smeraldo"},
        {"codice": "715", "nome": "Verde Bottiglia"}
    ],
    "Canapina": [
        {"codice": "250", "nome": "Grigio"},
        {"codice": "251", "nome": "Nero"},
        {"codice": "252", "nome": "Beige"},
        {"codice": "253", "nome": "Marrone"},
        {"codice": "254", "nome": "Rosa"},
        {"codice": "255", "nome": "Celeste"},
        {"codice": "256", "nome": "Blu"},
        {"codice": "257", "nome": "Verde"}
    ],
    "Tacto": [
        {"codice": "551", "nome": "Nocciola"},
        {"codice": "552", "nome": "Marrone"},
        {"codice": "553", "nome": "Azzurro"},
        {"codice": "554", "nome": "Fuxia"},
        {"codice": "555", "nome": "Bianco"},
        {"codice": "556", "nome": "Grigio Chiaro"},
        {"codice": "557", "nome": "Grigio Scuro"},
        {"codice": "558", "nome": "Nero"},
        {"codice": "559", "nome": "Rosa Confetto"},
        {"codice": "560", "nome": "Tiffany"},
        {"codice": "561", "nome": "Blu"}
    ],
    "Wood": [
        {"codice": "113", "nome": "Verde"},
        {"codice": "120", "nome": "Azzurro"},
        {"codice": "122", "nome": "Antracite"},
        {"codice": "124", "nome": "Sabbia"},
        {"codice": "129", "nome": "Rosa"},
        {"codice": "138", "nome": "Nero"},
        {"codice": "139", "nome": "Grigio"},
        {"codice": "141", "nome": "Mogano"},
        {"codice": "143", "nome": "Blu"},
        {"codice": "144", "nome": "Giallo"},
        {"codice": "145", "nome": "Fuxia"},
        {"codice": "146", "nome": "Verde Tiffany"},
        {"codice": "150", "nome": "Rosso"},
        {"codice": "154", "nome": "Bianco Grigio"}
    ],
    "Tweed": [
        {"codice": "500", "nome": "Grigio"},
        {"codice": "501", "nome": "Nero"},
        {"codice": "502", "nome": "Beige"},
        {"codice": "503", "nome": "Blu Royal"},
        {"codice": "504", "nome": "Rosa"},
        {"codice": "505", "nome": "Celeste"}
    ],
    "Zebrano": [
        {"codice": "750", "nome": "Celeste"},
        {"codice": "751", "nome": "Rosa"},
        {"codice": "752", "nome": "Nero"},
        {"codice": "753", "nome": "Grigio"},
        {"codice": "754", "nome": "Marrone"}
    ],
    "Spigato": [
        {"codice": "500", "nome": "Grigio"},
        {"codice": "501", "nome": "Nero"},
        {"codice": "502", "nome": "Beige"},
        {"codice": "503", "nome": "Blu Royal"},
        {"codice": "504", "nome": "Rosa"},
        {"codice": "505", "nome": "Celeste"}
    ],
    "Coagulato": [
        {"codice": "152", "nome": "Bianco Perlato"},
        {"codice": "155", "nome": "Bianco Liscio"}
    ]
}


# =============================================================================
# I 18 MODELLI ESTRO WEDDING
# =============================================================================
MODELLI_ALBUM = [
    {
        "id": "evo",
        "nome": "EVO 01 / 02",
        "sottotitolo": "Display Smart IPS 7'' estraibile & Cofanetto Arredo",
        "descrizione": "Fotolibro innovativo con display IPS LCD 7'' estraibile e speaker da 12W. Plancia Total White o White e Cristal. Cofanetto in legno pregiato rivestito con funzione espositore da tavolo.",
        "immagine": "media/models/model_003_01.jpg",
        "formati": ["30x40", "40x30"],
        "max_pagine": 100,
        "campionari": ["Vellutino", "Canapina"],
        "cofanetto": "Legno rivestito espositore con pochette da viaggio",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": True,
            "allegato_video": True
        }
    },
    {
        "id": "butterfly_lumina",
        "nome": "Estro Butterfly Lumina",
        "sottotitolo": "Coperchio con Pannello Retroilluminato a LED",
        "descrizione": "Il cofanetto Lumina nasconde nel coperchio un pannello retroilluminato a led con comando a filo per trasformare la copertina in quadro luminoso d'effetto. Incisione nomi sposi.",
        "immagine": "media/models/model_011_01.jpg",
        "formati": ["30x40", "40x30", "35x45"],
        "max_pagine": 60,
        "campionari": ["Vellutino", "Canapina"],
        "cofanetto": "Legno rivestito con coperchio retroilluminato a LED a bassa tensione",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": False,
            "allegato_video": False
        }
    },
    {
        "id": "estro_stile",
        "nome": "Estro Stile",
        "sottotitolo": "Cofanetto con Plexi Sinuoso & Taglio Geometrico",
        "descrizione": "Design contemporaneo con cofanetto in legno e plexiglass dalle linee sinuose. Copertina album con iconico taglio geometrico ad angolo per foto sposi o logo personalizzato.",
        "immagine": "media/models/model_016_01.jpg",
        "formati": ["30x40", "40x30", "35x25", "25x35", "30x20"],
        "max_pagine": 60,
        "campionari": ["Vellutino", "Canapina"],
        "cofanetto": "Legno rivestito e plexi sagomato trasparente",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": False,
            "allegato_video": False
        }
    },
    {
        "id": "estro_360",
        "nome": "Estro 360",
        "sottotitolo": "Cofanetto Espositivo Girevole a 360 Gradi",
        "descrizione": "Cofanetto girevole in plexiglass e legno che permette di ruotare l'album per esporlo da entrambi i lati come una teca da museo. Fotocopertina frontale e retro coordinato.",
        "immagine": "media/models/model_021_01.jpg",
        "formati": ["30x40", "40x30", "35x25", "25x35", "30x20"],
        "max_pagine": 60,
        "campionari": ["Vellutino", "Canapina"],
        "cofanetto": "Legno rivestito con perno rotante e plexi 360°",
        "opzioni": {
            "nomi_sposi": False,
            "foto_interna": False,
            "allegato_video": False
        }
    },
    {
        "id": "estro_horizon",
        "nome": "Estro Horizon (Vista)",
        "sottotitolo": "Plexi a Campana Cristallino & Copertina Bifacciale",
        "descrizione": "Cofanetto d'avanguardia con base in legno rivestito e campana in plexi con chiusura ermetica da tutti i lati. Album con fotocopertina bifacciale (fronte e retro visibili).",
        "immagine": "media/models/model_027_01.jpg",
        "formati": ["30x40", "40x30", "35x25", "25x35"],
        "max_pagine": 60,
        "campionari": ["Vellutino", "Canapina"],
        "cofanetto": "Base legno rivestito con cupola/campana in plexi trasparente",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": False,
            "allegato_video": False
        }
    },
    {
        "id": "estro_ares",
        "nome": "Estro Ares",
        "sottotitolo": "Design Scultoreo in Legno Massello e Plexi Curvo",
        "descrizione": "Base in legno massello scuro con struttura trasparente rifinita con accento in legno chiaro a contrasto. Fotolibro con fotocopertina su entrambi i lati e dorso in eco.",
        "immagine": "media/models/model_032_01.jpg",
        "formati": ["30x40", "40x30"],
        "max_pagine": 60,
        "campionari": ["Canapina", "Vellutino"],
        "cofanetto": "Espositore scultoreo in legno massello e plexy curvo",
        "opzioni": {
            "nomi_sposi": False,
            "foto_interna": False,
            "allegato_video": False
        }
    },
    {
        "id": "estro_idea",
        "nome": "Estro Idea",
        "sottotitolo": "Taglio Sagomato Moderno & Fotocopertina Bifacciale",
        "descrizione": "Cofanetto con sagoma diagonale moderna in legno rivestito e plexi da ambo i lati. Album con fotocopertina da ambo i lati e dorso in tessuto/eco coordinato.",
        "immagine": "media/models/model_037_01.jpg",
        "formati": ["30x40", "40x30", "35x25", "25x35"],
        "max_pagine": 60,
        "campionari": ["Canapina", "Vellutino"],
        "cofanetto": "Legno rivestito e plexi sagomato bifacciale",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": False,
            "allegato_video": False
        }
    },
    {
        "id": "estro_panorama",
        "nome": "Estro Panorama",
        "sottotitolo": "Cassa in Legno con Perno Centrale & Finitura Soft-Touch",
        "descrizione": "Cassa in legno massello naturale o bianco che ruota su se stessa tramite perno centrale di precisione. Album double-face con foto-copertina vellutata Soft Touch.",
        "immagine": "media/models/model_042_01.jpg",
        "formati": ["30x40", "40x30", "25x35", "35x25"],
        "max_pagine": 60,
        "campionari": ["Canapina", "Vellutino"],
        "cofanetto": "Cassa legno massello naturale/bianco girevole con doppio plexi",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": False,
            "allegato_video": False
        }
    },
    {
        "id": "butterfly_1",
        "nome": "Estro Butterfly 1",
        "sottotitolo": "Chiusura Magnetica & Foto Interna Coperchio",
        "descrizione": "Scrigno compatto dalle linee pure con chiusura a patta magnetica in eco/tessuto. Nomi sposi sul fronte e foto a tutta pagina all'apertura del cofanetto.",
        "immagine": "media/models/model_048_01.jpg",
        "formati": ["30x40", "40x30", "25x35", "35x25"],
        "max_pagine": 60,
        "campionari": ["Canapina", "Vellutino"],
        "cofanetto": "Scrigno rivestito con chiusura a patta magnetica e foto interna",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": True,
            "allegato_video": False
        }
    },
    {
        "id": "butterfly_2",
        "nome": "Estro Butterfly 2",
        "sottotitolo": "Placca in Alluminio Argento con Stampa a Caldo",
        "descrizione": "Elegante placca in alluminio argento lucido con foto degli sposi impressa a caldo sul cofanetto. Album con sottile striscia di alluminio incastonata con nomi sposi.",
        "immagine": "media/models/model_052_01.jpg",
        "formati": ["30x40", "40x30", "35x25", "25x35"],
        "max_pagine": 60,
        "campionari": ["Canapina", "Vellutino"],
        "cofanetto": "Placca in alluminio con foto impressa a caldo e foto interna",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": True,
            "allegato_video": False
        }
    },
    {
        "id": "butterfly_3",
        "nome": "Estro Butterfly 3",
        "sottotitolo": "Taglio Obliquo con Foto Incassata & Rilievo Nomi",
        "descrizione": "Copertina con lavorazione a taglio obliquo: metà tessuto/eco e metà foto sposi incassata. Nomi sposi a rilievo sul lato sinistro della copertina e foto interna al cofanetto.",
        "immagine": "media/models/model_057_01.jpg",
        "formati": ["30x40", "40x30"],
        "max_pagine": 60,
        "campionari": ["Canapina", "Vellutino"],
        "cofanetto": "Cofanetto con nomi sposi a rilievo e foto interna",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": True,
            "allegato_video": False
        }
    },
    {
        "id": "anthea_01",
        "nome": "Estro Anthea 01",
        "sottotitolo": "Metà Ecopelle, Metà Legno Venato Chiaro con Nomi a Rilievo",
        "descrizione": "Cassa in legno bianco rivestito eco (apertura orizzontale o verticale). Album: lato sinistro in eco coordinato, lato destro in legno venato chiaro con scritta nomi a rilievo.",
        "immagine": "media/models/model_062_01.jpg",
        "formati": ["30x40", "40x30"],
        "max_pagine": 60,
        "campionari": ["Tacto", "Vellutino"],
        "cofanetto": "Cassa legno bianco rivestito eco con foto interna coperchio",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": True,
            "allegato_video": False
        }
    },
    {
        "id": "anthea_02",
        "nome": "Estro Anthea 02",
        "sottotitolo": "Taglio Diagonale in Legno Massello Chiaro & Tessuto Pregiato",
        "descrizione": "Cofanetto in essenze di legno chiaro levigato con foto interna. Album con taglio diagonale di precisione che fonde legno venato chiaro e tessuti caldi, con nomi a rilievo.",
        "immagine": "media/models/model_067_01.jpg",
        "formati": ["30x40", "40x30", "25x35", "35x25"],
        "max_pagine": 60,
        "campionari": ["Tacto", "Vellutino"],
        "cofanetto": "Cassa in legno naturale con perno espositore e foto interna",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": True,
            "allegato_video": False
        }
    },
    {
        "id": "estro_strip",
        "nome": "Estro Strip",
        "sottotitolo": "Copertina in Cristal & Inserto Strip Vedo-Non-Vedo",
        "descrizione": "Copertina in Cristal trasparente con inserto 'Strip' in ecopelle o tessuto. Cofanetto coordinato con struttura parzialmente aperta che svela la foto dell'album.",
        "immagine": "media/models/model_072_01.jpg",
        "formati": ["30x40", "40x30", "25x35", "35x25"],
        "max_pagine": 60,
        "campionari": ["Tweed", "Zebrano"],
        "cofanetto": "Cassa legno rivestito con strip cristal e foto interna",
        "opzioni": {
            "nomi_sposi": False,
            "foto_interna": True,
            "allegato_video": False
        }
    },
    {
        "id": "estro_zen",
        "nome": "Estro Zen",
        "sottotitolo": "Doppio Piano Trasparente 'Fluttuante' & Ricamo su Velluto",
        "descrizione": "Cofanetto con superfici in cristallo acrilico sopra e sotto dove l'album sembra fluttuare nel vuoto a 360°. Due versioni: Ricamo artigianale su velluto oppure foto con nomi a rilievo.",
        "immagine": "media/models/model_077_01.jpg",
        "formati": ["30x40", "40x30"],
        "max_pagine": 60,
        "campionari": ["Vellutino", "Coagulato"],
        "cofanetto": "Cassa legno naturale con doppio plexi fluttuante",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": False,
            "allegato_video": False
        }
    },
    {
        "id": "estro_etnik",
        "nome": "Estro Etnik",
        "sottotitolo": "Legno Nero, Bacchetta in Legno Chiaro & Nomi a Rilievo",
        "descrizione": "Cofanetto teca espositiva nera con inserti e bacchetta in legno chiaro con venature vive e doppio plexiglass. Copertina album in legno nero con nomi sposi a rilievo su legno.",
        "immagine": "media/models/model_082_01.jpg",
        "formati": ["30x40", "40x30"],
        "max_pagine": 60,
        "campionari": ["Vellutino", "Zebrano"],
        "cofanetto": "Cassa legno nero verniciato con bacchetta decorativa e doppio plexi",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": False,
            "allegato_video": False
        }
    },
    {
        "id": "estro_vanity",
        "nome": "Estro Vanity",
        "sottotitolo": "Teca 360° in Plexi Trasparente & Finestra Panoramica",
        "descrizione": "Teca con giro a 360° in plexi trasparente invisibile, coperchio e fondo in ecomateriale. Album essenziale con finestra per foto sposi e nomi incisi con eleganza.",
        "immagine": "media/models/model_087_01.jpg",
        "formati": ["25x35", "35x25", "30x40", "40x30"],
        "max_pagine": 60,
        "campionari": ["Vellutino", "Wood", "Coagulato"],
        "cofanetto": "Fondo e coperchio in eco/tessuto con giro completo in plexi a vista",
        "opzioni": {
            "nomi_sposi": True,
            "foto_interna": False,
            "allegato_video": False
        }
    },
    {
        "id": "estro_theca",
        "nome": "Estro Theca",
        "sottotitolo": "Cristal Sagomato & Finestra Panoramica 10x37 cm",
        "descrizione": "Cofanetto con coperchio interamente in cristal sagomato trasparente e fondo in legno rivestito. Album con finestra panoramica orizzontale 10x37 cm per foto sposi.",
        "immagine": "media/models/model_092_01.jpg",
        "formati": ["30x40", "40x30"],
        "max_pagine": 60,
        "campionari": ["Vellutino", "Spigato"],
        "cofanetto": "Fondo legno rivestito con coperchio interamente in cristal sagomato",
        "opzioni": {
            "nomi_sposi": False,
            "foto_interna": False,
            "allegato_video": False
        }
    }
]


def get_modello_by_id(modello_id: str) -> dict | None:
    """Restituisce il modello corrispondente all'id o None."""
    for m in MODELLI_ALBUM:
        if m["id"] == modello_id:
            return m
    return None
