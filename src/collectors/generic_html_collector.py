from __future__ import annotations

from bs4 import BeautifulSoup

from src.collectors.base_collector import ActiveProtectionError, BaseCollector, RobotsBlockedError, SourceContext
from src.processing.cleaner import clean_text
from src.processing.price_parser import PriceObservationIn, parse_brl_price


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
        price = parse_brl_price(response.text)
        if price is None:
            return [
                self.status_observation(
                    context,
                    "no_price",
                    "Pagina carregou, mas nenhum preco publico em BRL foi detectado.",
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
                raw_product_name=title,
                raw_price=f"R$ {price:.2f}",
                parsed_price=price,
                raw_unit="peca",
                collection_status="success",
                source_type=context.source_type,
                used_regex_fallback=True,
                unit_assumed=True,
            ).finalized()
        ]

