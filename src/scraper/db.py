from pathlib import Path

import psycopg
import structlog

from scraper.config import DIR_WORK
from scraper.storage import read_books

logger = structlog.get_logger()

DSN = "postgresql://bouquineo:bouquineo@localhost:5432/bouquineo"

RACINE = Path(__file__).resolve().parents[2]
FICHIER_SCHEMA = RACINE / "sql" / "schema.sql"
FICHIER_FICHES = DIR_WORK / "fiches.jsonl"

REQUETE_UPSERT = """
    INSERT INTO books (
        upc, title, category, price_excl, price_incl, tax,
        rating, stock, reviews_count, description, url
    )
    VALUES (
        %(upc)s, %(titre)s, %(categorie)s, %(prix_ht)s, %(prix_ttc)s, %(taxe)s,
        %(note)s, %(stock)s, %(nb_avis)s, %(description)s, %(url_fiche)s
    )
    ON CONFLICT (upc) DO UPDATE SET
        title         = EXCLUDED.title,
        category      = EXCLUDED.category,
        price_excl    = EXCLUDED.price_excl,
        price_incl    = EXCLUDED.price_incl,
        tax           = EXCLUDED.tax,
        rating        = EXCLUDED.rating,
        stock         = EXCLUDED.stock,
        reviews_count = EXCLUDED.reviews_count,
        description   = EXCLUDED.description,
        url           = EXCLUDED.url,
        collected_at  = now();
"""


def creer_schema():
    """Execute sql/schema.sql. Rejouable sans erreur."""
    sql = FICHIER_SCHEMA.read_text(encoding="utf-8")
    with psycopg.connect(DSN) as conn:
        conn.execute(sql)
    logger.info("schema cree ou deja present")


def charger(source=FICHIER_FICHES):
    """Charge les fiches collectees dans PostgreSQL.

    Idempotent : une seconde execution met a jour les lignes existantes
    au lieu d'en creer de nouvelles (conflit sur la cle primaire upc).
    """
    fiches = read_books(source)
    if not fiches:
        logger.error("aucune fiche a charger", source=str(source))
        return 0

    charges = 0
    ignorees = 0

    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            for fiche in fiches:
                if not fiche.get("upc"):
                    ignorees += 1
                    logger.warning("fiche sans upc ignoree", url=fiche.get("url_fiche"))
                    continue
                cur.execute(REQUETE_UPSERT, fiche)
                charges += 1

    logger.info("chargement termine", charges=charges, ignorees=ignorees)
    return charges