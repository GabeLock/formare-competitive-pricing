"""
ananda_metais.py

Referência nacional em perfis para drywall, com planta em Extrema/MG.
Confirmado manualmente: comercialização via representantes/canais B2B,
sem preço público direto no site institucional.
"""

from scrapers.generic_scraper import GenericScraper


def build_scraper() -> GenericScraper:
    return GenericScraper(
        competitor_name="Ananda Metais",
        competitor_tier="tecnico_referencia",
        competitor_city_region="Piracicaba/SP (planta Extrema/MG)",
        known_price_type="manual_quote",
    )
