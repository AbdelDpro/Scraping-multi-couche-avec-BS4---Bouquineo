import structlog

from scraper.config import DIR_WORK
from scraper.http_client import fetch
from scraper.parsing import parser_fiche
from scraper.storage import add_book, read_books

logger = structlog.get_logger()

FICHIER_LIVRES = DIR_WORK / "livres.jsonl"
FICHIER_FICHES = DIR_WORK / "fiches.jsonl"

MAX_ECHECS_CONSECUTIFS = 20


def collecter_fiches(
    source=FICHIER_LIVRES,
    destination=FICHIER_FICHES,
    limite=None,
):
    """Enrichit chaque livre avec les donnees de sa fiche produit.

    Reprend la collecte la ou elle s'etait arretee : les URL deja presentes
    dans le fichier de destination sont ignorees.
    """
    livres = read_books(source)
    if not livres:
        logger.error("aucun livre a traiter", source=str(source))
        return 0

    deja_faites = {f["url_fiche"] for f in read_books(destination)}
    a_traiter = [livre for livre in livres if livre["url_fiche"] not in deja_faites]

    if limite is not None:
        a_traiter = a_traiter[:limite]

    logger.info(
        "debut de la collecte des fiches",
        total=len(livres),
        deja_faites=len(deja_faites),
        a_traiter=len(a_traiter),
    )

    succes = 0
    echecs = 0
    echecs_consecutifs = 0

    for livre in a_traiter:
        url = livre["url_fiche"]
        try:
            fiche = parser_fiche(fetch(url))
        except Exception as erreur:
            echecs += 1
            echecs_consecutifs += 1
            logger.warning("fiche ignoree", url=url, erreur=str(erreur))

            if echecs_consecutifs >= MAX_ECHECS_CONSECUTIFS:
                logger.error(
                    "trop d'echecs consecutifs, arret",
                    seuil=MAX_ECHECS_CONSECUTIFS,
                    succes=succes,
                )
                break
            continue

        add_book(destination, {**livre, **fiche})
        succes += 1
        echecs_consecutifs = 0

        if succes % 50 == 0:
            logger.info("progression", traitees=succes, restantes=len(a_traiter) - succes)

    logger.info("collecte des fiches terminee", succes=succes, echecs=echecs)
    return succes