"""
generic_scraper.py

Scraper genérico usado por padrão para qualquer concorrente que ainda não
tenha um parser dedicado. Ele:
  1. Faz o GET respeitando robots.txt/rate-limit (via BaseScraper);
  2. Tenta um seletor CSS opcional (se fornecido em sources.yaml no futuro);
  3. Cai no price_detector genérico (regex por "R$ 0,00" / JSON-LD / itemprop);
  4. Se nada for encontrado, marca price_type="manual_quote" (ou "unavailable"
     se nem o HTML carregou), preservando a URL para consulta manual.

Quando um site específico precisar de lógica própria (ex.: paginação,
JavaScript, API interna), crie um arquivo dedicado (ver gravia.py como
exemplo) e aponte para ele no runner.py.
"""

from __future__ import annotations

from typing import Optional

from scrapers.base_scraper import BaseScraper, PriceObservation
from scrapers.price_detector import detect_price_with_selector


class GenericScraper(BaseScraper):
    def __init__(
        self,
        competitor_name: str,
        competitor_tier: str,
        competitor_city_region: str,
        css_selector: Optional[str] = None,
        known_price_type: str = "unknown",
    ):
        super().__init__(competitor_name, competitor_tier, competitor_city_region)
        self.css_selector = css_selector
        self.known_price_type = known_price_type  # "manual_quote" | "auto_scraped" | "unknown"

    def parse(self, html: str, url: str, category: str) -> list[PriceObservation]:
        # Se já sabemos (por pesquisa manual) que esta fonte é "manual_quote",
        # nem tentamos raspar preço — só confirmamos que a página ainda está no ar
        # e guardamos o snapshot para referência (ex.: mudança de portfólio de produtos).
        if self.known_price_type == "manual_quote":
            return [
                PriceObservation(
                    competitor_name=self.competitor_name,
                    competitor_tier=self.competitor_tier,
                    competitor_city_region=self.competitor_city_region,
                    product_category=category,
                    source_url=url,
                    price_type="manual_quote",
                    notes=(
                        "Fonte confirmada como 'solicitar orçamento' (sem preço público). "
                        "Registre o valor manualmente no dashboard após cotação por telefone/WhatsApp."
                    ),
                )
            ]

        price = None
        if self.css_selector:
            price = detect_price_with_selector(html, self.css_selector)
        else:
            from scrapers.price_detector import detect_price_in_html

            price = detect_price_in_html(html)

        if price is None:
            return [
                PriceObservation(
                    competitor_name=self.competitor_name,
                    competitor_tier=self.competitor_tier,
                    competitor_city_region=self.competitor_city_region,
                    product_category=category,
                    source_url=url,
                    price_type="manual_quote",
                    notes="Nenhum preço detectado automaticamente nesta coleta — provável modelo de orçamento.",
                )
            ]

        return [
            PriceObservation(
                competitor_name=self.competitor_name,
                competitor_tier=self.competitor_tier,
                competitor_city_region=self.competitor_city_region,
                product_category=category,
                source_url=url,
                price_value=price,
                unit_measure="R$/un",  # ajuste fino por site pode refinar isso depois
                price_type="auto_scraped",
            )
        ]
