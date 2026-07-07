"""
telhas_barreiro.py

Concorrente direto regional (MG). Status de preço público ainda não
verificado -> tentativa automática via price_detector.
"""

from scrapers.generic_scraper import GenericScraper


def build_scraper() -> GenericScraper:
    return GenericScraper(
        competitor_name="Telhas Barreiro",
        competitor_tier="regional_direto",
        competitor_city_region="MG",
        known_price_type="unknown",
    )
