"""
perfil_telhas.py

Concorrente direto regional (sede Timóteo/MG, filial na região metropolitana
de BH). Confirmado manualmente: modelo "faça seu orçamento e compare", sem
preço público.
"""

from scrapers.generic_scraper import GenericScraper


def build_scraper() -> GenericScraper:
    return GenericScraper(
        competitor_name="Perfil Telhas",
        competitor_tier="regional_direto",
        competitor_city_region="Timóteo/MG (+ filial Grande BH)",
        known_price_type="manual_quote",
    )
