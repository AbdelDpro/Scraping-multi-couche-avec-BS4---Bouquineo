import requests
import time
import structlog
from scraper.config import DELAY, TIMEOUT, USER_AGENT

logger = structlog.get_logger()
_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})
_dernier_appel = 0.0

def fetch(url):
    """Récupère le HTML d'une page en respectant le délai entre requêtes.

    Lève une HTTPError si le serveur répond avec un code d'erreur.
    """

    global _dernier_appel

    ecoule = time.monotonic() - _dernier_appel
    if ecoule < DELAY:
        time.sleep(DELAY - ecoule)
    _dernier_appel = time.monotonic()

    response = _session.get(url, timeout=TIMEOUT)

    response.raise_for_status()
    logger.info("données récupérées", size=len(response.content), url=url)
    return response.text