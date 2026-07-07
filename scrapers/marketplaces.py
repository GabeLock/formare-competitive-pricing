"""
marketplaces.py

Canais Tier 3 (benchmark público de mercado, não regionais).

Mercado Livre: em vez de raspar HTML de busca (frágil e muda com frequência),
usamos a API PÚBLICA e oficial do Mercado Livre, que não exige autenticação
para busca simples:
    GET https://api.mercadolibre.com/sites/MLB/search?q={termo}

Isso é mais robusto, mais rápido e mais respeitoso com os termos de uso do
que fazer scraping da página de resultados.

Google Shopping foi DELIBERADAMENTE deixado fora da automação: raspar
resultados de busca do Google viola os Termos de Serviço do Google e é
tecnicamente instável (bloqueios, CAPTCHAs). Ele continua útil como link de
consulta manual (ver README), mas não deve ser scrapeado por este projeto.
Alternativa, se quiser automatizar no futuro: usar uma API paga de terceiros
(ex.: SerpApi) que já lida com essa camada de conformidade.

Sodimac, Leroy Merlin, Telhas Online, Pizzinatto e Servicorte: usamos o
GenericScraper por padrão (preço público já confirmado ou plausível nesses
canais); se a extração automática falhar, cada um cai em "manual_quote"
até alguém escrever um parser dedicado (seguindo o modelo de gravia.py).
"""

from __future__ import annotations

import logging
from typing import Optional

from scrapers.base_scraper import BaseScraper, PriceObservation, USER_AGENT
from scrapers.generic_scraper import GenericScraper

import requests

logger = logging.getLogger(__name__)

ML_SEARCH_API = "https://api.mercadolibre.com/sites/MLB/search"


class MercadoLivreScraper(BaseScraper):
    """Usa a API pública oficial em vez de raspar HTML de busca."""

    def __init__(self):
        super().__init__(
            competitor_name="Mercado Livre",
            competitor_tier="benchmark_publico",
            competitor_city_region="Nacional (múltiplos vendedores)",
        )

    def collect_by_query(self, query: str, category: str, max_results: int = 5) -> list[PriceObservation]:
        self._respect_rate_limit(ML_SEARCH_API)
        try:
            response = self._session.get(
                ML_SEARCH_API,
                params={"q": query, "limit": max_results},
                headers={"User-Agent": USER_AGENT},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.error("Falha na API do Mercado Livre para '%s': %s", query, exc)
            return [
                PriceObservation(
                    competitor_name=self.competitor_name,
                    competitor_tier=self.competitor_tier,
                    competitor_city_region=self.competitor_city_region,
                    product_category=category,
                    source_url=f"{ML_SEARCH_API}?q={query}",
                    price_type="unavailable",
                    notes=f"Erro na API do Mercado Livre: {exc}",
                )
            ]

        observations: list[PriceObservation] = []
        for item in data.get("results", [])[:max_results]:
            observations.append(
                PriceObservation(
                    competitor_name=f"Mercado Livre — {item.get('seller', {}).get('nickname', 'vendedor não informado')}",
                    competitor_tier=self.competitor_tier,
                    competitor_city_region=self.competitor_city_region,
                    product_category=category,
                    source_url=item.get("permalink", ""),
                    product_description_raw=item.get("title", ""),
                    price_value=item.get("price"),
                    unit_measure="R$/un",
                    price_type="auto_scraped",
                    stock_status_notes=f"estoque disponível: {item.get('available_quantity')}",
                )
            )

        if not observations:
            observations.append(
                PriceObservation(
                    competitor_name=self.competitor_name,
                    competitor_tier=self.competitor_tier,
                    competitor_city_region=self.competitor_city_region,
                    product_category=category,
                    source_url=f"{ML_SEARCH_API}?q={query}",
                    price_type="unavailable",
                    notes="Nenhum resultado retornado pela API para esta busca.",
                )
            )
        return observations

    # Mantido por compatibilidade com a interface do BaseScraper; não é o
    # caminho usado (ver collect_by_query).
    def parse(self, html: str, url: str, category: str) -> list[PriceObservation]:
        raise NotImplementedError("Use collect_by_query() para o Mercado Livre.")


def build_mercado_livre_scraper() -> MercadoLivreScraper:
    return MercadoLivreScraper()


def build_generic_tier3_scraper(name: str, region: str = "Nacional") -> GenericScraper:
    """Fábrica simples para os demais canais Tier 3 (Sodimac, Leroy Merlin,
    Telhas Online, Pizzinatto, Servicorte) até que cada um ganhe um parser
    dedicado, se necessário."""
    return GenericScraper(
        competitor_name=name,
        competitor_tier="benchmark_publico",
        competitor_city_region=region,
        known_price_type="unknown",
    )
