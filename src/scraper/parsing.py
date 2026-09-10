from urllib.parse import urljoin
from bs4 import BeautifulSoup
import structlog
from scraper.config import MAPPING_NOTES
import re

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

    Rend None si aucun nombre n'est trouvable.
    """
    chiffres = "".join(c for c in texte if c.isdigit() or c == ".")
    if not chiffres:
        logger.warning("prix illisible", texte=texte)
        return None
    return float(chiffres)

def extract_first_number(texte):
    """Extrait le premier nombre entier du texte. Rend 0 s'il n'y en a pas."""
    correspondance = re.search(r"\d+", texte)
    return int(correspondance.group()) if correspondance else 0

def read_number_of_pages(html):
    """Lit le nombre total de pages depuis le texte "Page 1 of 50".

    Rend None si le motif est absent : l'appelant decide quoi faire.
    """
    soup = BeautifulSoup(html, "lxml")
    tag = soup.select_one("li.current")
    if tag is None:
        logger.warning("indicateur de pagination absent")
        return None

    correspondance = re.search(r"of\s+(\d+)", tag.text)
    if correspondance is None:
        logger.warning("format de pagination inattendu", texte=tag.text.strip())
        return None

    return int(correspondance.group(1))

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

def parser_fiche(html):
    """Extrait les champs d'une fiche produit et rend un dict : upc, prix_ht, prix_ttc, taxe, stock, nb_avis,
    description, categorie.
    """
    soup = BeautifulSoup(html, "lxml")

    # Le tableau Product Information : une ligne = un th (libelle) + un td (valeur)
    infos = {}
    for ligne in soup.select("table.table-striped tr"):
        libelle = ligne.select_one("th")
        valeur = ligne.select_one("td")
        if libelle is not None and valeur is not None:
            infos[libelle.text.strip()] = valeur.text.strip()

    # La categorie est le dernier lien du chemin de navigation
    liens = soup.select("ul.breadcrumb a")
    categorie = liens[-1].text.strip() if liens else None

    description_tag = soup.select_one("#product_description + p")
    description = description_tag.text.strip() if description_tag else None

    return {
        "upc": infos.get("UPC"),
        "prix_ht": convert_price(infos.get("Price (excl. tax)", "")),
        "prix_ttc": convert_price(infos.get("Price (incl. tax)", "")),
        "taxe": convert_price(infos.get("Tax", "")),
        "stock": extract_first_number(infos.get("Availability", "")),
        "nb_avis": extract_first_number(infos.get("Number of reviews", "")),
        "description": description,
        "categorie": categorie,
    }