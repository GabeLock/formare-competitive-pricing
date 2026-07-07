"""
gravia.py

Único concorrente confirmado (nesta pesquisa) com preço numérico público em
todas as páginas de produto — plataforma VTEX. Confirmado ao vivo: Telha
Trapézio GR40 Galvalume = R$ 94,76/un no momento da checagem.

Sites VTEX normalmente expõem os dados do produto também via:
  - meta itemprop="price" content="94.76"
  - JSON embutido em <script type="application/ld+json">
  - API pública: https://www.gravia.com/api/catalog_system/pub/products/search/{termo}

Aqui usamos o HTML da página de categoria/produto (mais simples e estável
para manter); se a extração via seletor falhar, cai no price_detector
genérico automaticamente.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, PriceObservation
from scrapers.price_detector import detect_price_in_html

# Seletores mais comuns em vitrines VTEX (pode variar por tema — ajustar após
# primeira execução real olhando o HTML salvo em data/raw_snapshots/gravia/).
CANDIDATE_SELECTORS = [
    "span.vtex-product-price-1-x-sellingPriceValue",
    "span.vtex-product-price-1-x-sellingPrice",
    "meta[itemprop='price']",
    ".price__SellingPrice",
]


class GraviaScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            competitor_name="Gravia",
            competitor_tier="benchmark_publico",
            competitor_city_region="Nacional (Brasília/DF)",
        )

    def parse(self, html: str, url: str, category: str) -> list[PriceObservation]:
        soup = BeautifulSoup(html, "lxml")
        price = None

        for selector in CANDIDATE_SELECTORS:
            el = soup.select_one(selector)
            if el is None:
                continue
            text = el.get("content") if el.name == "meta" else el.get_text(strip=True)
            if not text:
                continue
            cleaned = text.replace("R$", "").strip()
            try:
                if "," in cleaned:
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                price = float(cleaned)
                break
            except ValueError:
                continue

        if price is None:
            price = detect_price_in_html(html)

        if price is None:
            return [
                PriceObservation(
                    competitor_name=self.competitor_name,
                    competitor_tier=self.competitor_tier,
                    competitor_city_region=self.competitor_city_region,
                    product_category=category,
                    source_url=url,
                    price_type="unavailable",
                    notes=(
                        "Preço não encontrado nesta coleta — o tema VTEX pode ter mudado. "
                        "Verifique o snapshot salvo e ajuste CANDIDATE_SELECTORS em gravia.py."
                    ),
                )
            ]

        # Múltiplos produtos podem existir na mesma página de categoria; esta
        # implementação inicial captura o primeiro card como amostra.
        # Refinamento sugerido: iterar por soup.select(".vtex-product-summary-2-x-container")
        # e gerar uma PriceObservation por item.
        return [
            PriceObservation(
                competitor_name=self.competitor_name,
                competitor_tier=self.competitor_tier,
                competitor_city_region=self.competitor_city_region,
                product_category=category,
                source_url=url,
                price_value=price,
                unit_measure="R$/un",
                price_type="auto_scraped",
            )
        ]


def build_scraper() -> GraviaScraper:
    return GraviaScraper()
