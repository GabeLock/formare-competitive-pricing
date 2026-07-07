"""
multiperfil.py — referência técnica em perfis drywall. Status de preço
público ainda não verificado -> tentativa automática.
"""

from scrapers.generic_scraper import GenericScraper


def build_scraper() -> GenericScraper:
    return GenericScraper(
        competitor_name="Multiperfil",
        competitor_tier="tecnico_referencia",
        competitor_city_region="Nacional",
        known_price_type="unknown",
    )
