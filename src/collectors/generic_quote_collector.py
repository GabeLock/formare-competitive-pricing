from __future__ import annotations

from src.collectors.base_collector import ActiveProtectionError, BaseCollector, RobotsBlockedError, SourceContext
from src.processing.price_parser import PriceObservationIn


class GenericQuoteCollector(BaseCollector):
    """Probe public page availability for quote-only sources without submitting forms."""

    def collect(self, context: SourceContext) -> list[PriceObservationIn]:
        try:
            response = self.get(context.url)
            self.save_snapshot(context, response.text)
            return [
                self.status_observation(
                    context,
                    "quote_required",
                    "Pagina publica no ar; fonte trabalha por orcamento. Registrar preco somente manualmente.",
                    source_type="quote_required",
                )
            ]
        except RobotsBlockedError as exc:
            return [self.status_observation(context, "blocked", str(exc))]
        except ActiveProtectionError as exc:
            return [self.status_observation(context, "blocked", str(exc))]
        except Exception as exc:
            return [self.status_observation(context, "error", f"Erro ao verificar pagina: {exc}")]

