from pathlib import Path

USER_AGENT = "Scraping/1.0 (etude de cas; contact: https://github.com/AbdelDpro/Scraping-multi-couche-avec-BS4---Bouquineo)"
TIMEOUT = (5, 15)   # 5 s pour établir la connexion, 15 s pour recevoir la réponse

BASE_URL = "https://books.toscrape.com/"
URL_PAGE_LISTE = "catalogue/page-{n}.html"

ROOT = Path(__file__).resolve().parents[2]
DIR_WORK = ROOT / "data" / "work"
DIR_EXPORT = ROOT / "data" / "export"


DELAY = 0.5

MAX_PAGES = 60 # sécurité anti-boucle infinie

MAPPING_NOTES = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}