"""
suri_metais.py

Concorrente direto regional (Pouso Alegre/MG). Confirmado manualmente:
modelo "solicite orçamento", sem preço público.
"""

from scrapers.generic_scraper import GenericScraper


def build_scraper() -> GenericScraper:
    return GenericScraper(
        competitor_name="Suri Metais",
        competitor_tier="regional_direto",
        competitor_city_region="Pouso Alegre/MG",
        known_price_type="manual_quote",
    )
