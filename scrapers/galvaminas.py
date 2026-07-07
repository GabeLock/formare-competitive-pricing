"""
galvaminas.py

Concorrente direto regional (MG). Status de preço público AINDA NÃO
verificado manualmente -> known_price_type="unknown", deixamos o
price_detector genérico tentar identificar automaticamente na primeira
execução. Depois de confirmado, atualize known_price_type aqui e em
config/sources.yaml.
"""

from scrapers.generic_scraper import GenericScraper


def build_scraper() -> GenericScraper:
    return GenericScraper(
        competitor_name="Galvaminas",
        competitor_tier="regional_direto",
        competitor_city_region="MG",
        known_price_type="unknown",
    )
