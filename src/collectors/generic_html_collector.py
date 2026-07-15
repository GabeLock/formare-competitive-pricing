from __future__ import annotations

import json

from bs4 import BeautifulSoup

from src.collectors.base_collector import ActiveProtectionError, BaseCollector, RobotsBlockedError, SourceContext
from src.processing.cleaner import clean_text
from src.processing.price_parser import PriceObservationIn, parse_brl_price


def _json_ld_products(payload):
    if isinstance(payload, list):
        for item in payload:
            yield from _json_ld_products(item)
    elif isinstance(payload, dict):
        item_type = payload.get("@type", [])
        item_types = {item_type} if isinstance(item_type, str) else set(item_type)
        if "Product" in item_types:
            yield payload
        for value in payload.values():
            if isinstance(value, (dict, list)):
                yield from _json_ld_products(value)


def structured_product_price(soup: BeautifulSoup) -> tuple[str | None, float | None]:
    """Extract an explicit product offer; never infer a price from page text."""
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            payload = json.loads(script.get_text(strip=True))
        except (json.JSONDecodeError, TypeError):
            continue
        for product in _json_ld_products(payload):
            offers = product.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            if not isinstance(offers, dict):
                continue
            raw_price = str(offers.get("price") or offers.get("lowPrice") or "")
            try:
                price = float(raw_price.replace(",", "."))
            except ValueError:
                price = parse_brl_price(raw_price)
            if price is not None:
                return clean_text(str(product.get("name") or "")), price

    meta_price = soup.select_one('meta[property="product:price:amount"], meta[itemprop="price"]')
    if meta_price:
        price = parse_brl_price(meta_price.get("content") or "")
        if price is not None:
            return None, price
    return None, None


class GenericHtmlCollector(BaseCollector):
    def collect(self, context: SourceContext) -> list[PriceObservationIn]:
        try:
            response = self.get(context.url)
            self.save_snapshot(context, response.text)
        except RobotsBlockedError as exc:
            return [self.status_observation(context, "blocked", str(exc))]
        except ActiveProtectionError as exc:
            return [self.status_observation(context, "blocked", str(exc))]
        except Exception as exc:
            return [self.status_observation(context, "error", f"Erro de coleta: {exc}")]

        soup = BeautifulSoup(response.text, "lxml")
        title = clean_text(soup.title.get_text(" ")) if soup.title else context.product_id
        if context.url_type != "product":
            return [
                self.status_observation(
                    context,
                    "no_price",
                    "Pagina de categoria verificada; exige coletor especifico para associar preco ao produto correto.",
                )
            ]
        structured_title, price = structured_product_price(soup)
        if price is None:
            return [
                self.status_observation(
                    context,
                    "no_price",
                    "Pagina carregou, mas nao expôs preco estruturado do produto.",
                )
            ]

        return [
            PriceObservationIn(
                competitor_id=context.competitor_id,
                competitor_name=context.competitor_name,
                tier=context.tier,
                product_id=context.product_id,
                category=context.category,
                url=context.url,
                raw_product_name=structured_title or title,
                raw_price=f"R$ {price:.2f}",
                parsed_price=price,
                raw_unit="peca",
                collection_status="success",
                source_type=context.source_type,
                customer_segment=context.customer_segment,
                unit_assumed=True,
            ).finalized()
        ]
