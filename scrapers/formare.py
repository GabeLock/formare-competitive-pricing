"""
formare.py — baseline própria (não é concorrente).

Usado para registrar o "preço de tabela" público da própria Formare
(quando existir) e, principalmente, como lembrete para o usuário inserir
o custo interno real no dashboard (campo manual de CMV).

Confirmado manualmente em pesquisa: o site opera em modelo "Fazer Orçamento",
sem preço numérico exposto.
"""

from scrapers.generic_scraper import GenericScraper


def build_scraper() -> GenericScraper:
    return GenericScraper(
        competitor_name="Formare Metais",
        competitor_tier="regional_direto",
        competitor_city_region="Belo Horizonte/MG",
        known_price_type="manual_quote",
    )
