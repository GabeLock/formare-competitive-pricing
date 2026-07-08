from __future__ import annotations

import requests

from src.collectors.base_collector import BaseCollector, SourceContext
from src.processing.price_parser import PriceObservationIn
from src.utils.user_agent import get_user_agent

ML_SEARCH_API = "https://api.mercadolibre.com/sites/MLB/search"


class MercadoLivreCollector(BaseCollector):
    def collect(self, context: SourceContext) -> list[PriceObservationIn]:
        query = context.query or context.product_id
        try:
            self.cooldown(ML_SEARCH_API)
            response = requests.get(
                ML_SEARCH_API,
                params={"q": query, "limit": 5},
                headers={"User-Agent": get_user_agent()},
                timeout=25,
            )
            if response.status_code in {403, 429}:
                return [self.status_observation(context, "blocked", f"API retornou HTTP {response.status_code}")]
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            return [self.status_observation(context, "error", f"Erro na API Mercado Livre: {exc}")]

        observations: list[PriceObservationIn] = []
        for item in data.get("results", [])[:5]:
            seller = item.get("seller", {}).get("nickname", "vendedor nao informado")
            observations.append(
                PriceObservationIn(
                    competitor_id=context.competitor_id,
                    competitor_name=f"Mercado Livre - {seller}",
                    tier=context.tier,
                    product_id=context.product_id,
                    category=context.category,
                    url=item.get("permalink") or context.url,
                    raw_product_name=item.get("title"),
                    raw_price=f"R$ {float(item.get('price', 0)):.2f}",
                    parsed_price=float(item.get("price", 0)),
                    raw_unit="peca",
                    availability=f"Quantidade disponivel: {item.get('available_quantity')}",
                    collection_status="success",
                    source_type="marketplace",
                    customer_segment=context.customer_segment,
                    unit_assumed=True,
                ).finalized()
            )
        if not observations:
            observations.append(
                self.status_observation(
                    context,
                    "unavailable",
                    f"Nenhum resultado retornado pela API para a busca: {query}",
                    source_type="marketplace",
                )
            )
        return observations
