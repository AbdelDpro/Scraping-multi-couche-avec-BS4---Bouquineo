from scraper.config import MAPPING_NOTES
import structlog

logger = structlog.get_logger()

def convert_note(classes):
    """Convertit les classes CSS en une note numérique."""
    for mot in classes:
        if mot in MAPPING_NOTES:
            return MAPPING_NOTES[mot]
    logger.warning("note inconnue", classes=classes)

# Note inconnue, pour la gestion des erreurs en SQL et ses fonctions d'agrégation. Une absence de valeur ≠ valeur nulle.
    return None 