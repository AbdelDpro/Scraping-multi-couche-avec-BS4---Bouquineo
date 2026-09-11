import argparse

import structlog

from scraper.collect_listing import collecter_pages_liste
from scraper.collect_products import collecter_fiches

logger = structlog.get_logger()


def main():
    parser = argparse.ArgumentParser(
        description="Collecte le catalogue de books.toscrape.com."
    )
    parser.add_argument(
        "etape",
        choices=["listing", "produits", "tout"],
        help="etape a executer",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="mode echantillon : nombre de pages (listing) ou de fiches (produits)",
    )

    args = parser.parse_args()

    if args.etape in ("listing", "tout"):
        collecter_pages_liste(limite=args.limit)

    if args.etape in ("produits", "tout"):
        collecter_fiches(limite=args.limit)


if __name__ == "__main__":
    main()