import json
from pathlib import Path

import structlog

logger = structlog.get_logger()


def add_book(chemin, livre):
    """Ajoute un dict en fin de fichier JSONL (une ligne = un objet JSON)."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)

    with open(chemin, "a", encoding="utf-8") as f:
        f.write(json.dumps(livre, ensure_ascii=False) + "\n")


def read_books(chemin):
    """Relit un fichier JSONL et rend la liste des dicts.

    Rend une liste vide si le fichier n'existe pas : ce qui est normal
    au premier lancement.
    """
    chemin = Path(chemin)
    if not chemin.exists():
        return []

    livres = []
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                continue
            livres.append(json.loads(ligne))

    logger.info("fichier relu", chemin=str(chemin), livres=len(livres))
    return livres