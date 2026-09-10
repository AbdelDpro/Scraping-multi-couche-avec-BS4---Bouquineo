from urllib.parse import urljoin

import structlog

from scraper.config import BASE_URL, URL_PAGE_LISTE, MAX_PAGES, DIR_WORK
from scraper.http_client import fetch
from scraper.parsing import read_number_of_pages, parser_page_list
from scraper.storage import add_book

logger = structlog.get_logger()

FICHIER_LIVRES = DIR_WORK / "livres.jsonl"


def collecter_pages_liste(chemin=FICHIER_LIVRES, limite=None):
    """Parcourt les pages de liste et ecrit chaque livre dans un fichier JSONL, avec un nombre maximum de pages a parcourir (mode echantillon).
    """
    url_premiere = urljoin(BASE_URL, URL_PAGE_LISTE.format(n=1))
    html = fetch(url_premiere)

    total_pages = read_number_of_pages(html)
    if total_pages is None:
        logger.warning("nombre de pages introuvable, passe sur MAX_PAGES", max_pages=MAX_PAGES)
        total_pages = MAX_PAGES
    total_pages = min(total_pages, MAX_PAGES)

    if limite is not None:
        total_pages = min(total_pages, limite)

    logger.info("debut de la collecte", pages=total_pages)

    compteur = 0
    for n in range(1, total_pages + 1):
        url = urljoin(BASE_URL, URL_PAGE_LISTE.format(n=n))
        html = fetch(url) if n > 1 else html   # la page 1 est deja en memoire

        livres = parser_page_list(html, url)
        for livre in livres:
            add_book(chemin, livre)
        compteur += len(livres)

    logger.info("collecte terminee", pages=total_pages, livres=compteur)
    return compteur