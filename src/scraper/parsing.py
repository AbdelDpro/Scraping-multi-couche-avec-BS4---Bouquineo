from urllib.parse import urljoin
from bs4 import BeautifulSoup
import structlog
from scraper.config import MAPPING_NOTES

logger = structlog.get_logger()

def convert_note(classes):
    """Convertit les classes CSS en une note numérique."""
    for mot in classes:
        if mot in MAPPING_NOTES:
            return MAPPING_NOTES[mot]
    logger.warning("note inconnue", classes=classes)

# Note inconnue, pour la gestion des erreurs en SQL et ses fonctions d'agrégation. Une absence de valeur ≠ valeur nulle.
    return None 

def convert_price(texte):
    """Extrait un nombre depuis un texte de prix

    Hypothese : les prix du site utilisent le point comme separateur decimal
    et n'ont pas de separateur de milliers. Verifie sur books.toscrape ou tous
    les prix sont entre 10 et 60 GBP. Un format europeen ("1.234,56") donnerait
    un resultat faux d'un facteur 1000 sans lever d'erreur.
    """
    chiffres = "".join(c for c in texte if c.isdigit() or c == ".")
    return float(chiffres)


def parser_page_list(html, url_page):
    """Extrait les livres d'une page de liste.

    Rend une liste de dicts : titre, prix, note, url_fiche.
    """
    soup = BeautifulSoup(html, "lxml")
    blocs = soup.select("article.product_pod")

    livres = []
    for bloc in blocs:
        lien = bloc.select_one("h3 a")
        prix_tag = bloc.select_one("p.price_color")
        note_tag = bloc.select_one("p.star-rating")

        livres.append({
            "titre": lien["title"],
            "prix": convert_price(prix_tag.text),
            "note": convert_note(note_tag["class"]),
            "url_fiche": urljoin(url_page, lien["href"]),
        })

    logger.info("page parsee", url=url_page, livres=len(livres))
    return livres