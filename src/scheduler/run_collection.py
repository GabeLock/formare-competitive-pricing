from __future__ import annotations

from collections.abc import Iterable

from apscheduler.schedulers.blocking import BlockingScheduler

from src.collectors.base_collector import SourceContext
from src.collectors.generic_html_collector import GenericHtmlCollector
from src.collectors.generic_quote_collector import GenericQuoteCollector
from src.collectors.mercado_livre_collector import MercadoLivreCollector
from src.collectors.pizzinatto_collector import PizzinattoCollector
from src.collectors.servicorte_collector import ServicorteCollector
from src.collectors.telhas_online_collector import TelhasOnlineCollector
from src.database.connection import SessionLocal
from src.database.repository import active_sources, initialize_database, save_observations
from src.processing.price_parser import PriceObservationIn
from src.utils.logger import configure_logger, logger

COLLECTOR_BY_METHOD = {
    "quote_probe": GenericQuoteCollector,
    "html": GenericHtmlCollector,
    "mercado_livre_api": MercadoLivreCollector,
}

COLLECTOR_BY_COMPETITOR = {
    "telhas_online": TelhasOnlineCollector,
    "grupo_pizzinatto": PizzinattoCollector,
    "servicorte": ServicorteCollector,
}


def _context(competitor, product, monitored_url) -> SourceContext:
    url = monitored_url.url or "https://api.mercadolibre.com/sites/MLB/search"
    return SourceContext(
        competitor_id=competitor.id,
        competitor_name=competitor.name,
        tier=competitor.tier,
        region=competitor.region,
        product_id=product.id,
        category=product.category,
        url=url,
        query=monitored_url.query,
        source_type=monitored_url.source_type,
        collection_method=monitored_url.collection_method,
    )


def _collector_for(context: SourceContext):
    cls = COLLECTOR_BY_COMPETITOR.get(context.competitor_id)
    if cls is None:
        cls = COLLECTOR_BY_METHOD.get(context.collection_method, GenericHtmlCollector)
    return cls()


def simulated_fallback(context: SourceContext) -> PriceObservationIn:
    return PriceObservationIn(
        competitor_id=context.competitor_id,
        competitor_name=context.competitor_name,
        tier=context.tier,
        product_id=context.product_id,
        category=context.category,
        url=context.url,
        raw_product_name="Dado simulado para demonstracao",
        raw_price="R$ 0,00",
        parsed_price=0,
        raw_unit="peca",
        collection_status="success",
        source_type="estimated_price",
        confidence_score=20,
        simulated=True,
        notes="Gerado apenas porque --allow-simulated-fallback foi informado.",
    ).finalized()


def collect(
    source: str | None = None,
    dry_run: bool = False,
    allow_simulated_fallback: bool = False,
) -> list[PriceObservationIn]:
    configure_logger()
    initialize_database()
    observations: list[PriceObservationIn] = []
    with SessionLocal() as session:
        sources = active_sources(session, source_id=source)
        logger.info("Fontes ativas selecionadas: {}", len(sources))
        for competitor, product, monitored_url in sources:
            context = _context(competitor, product, monitored_url)
            logger.info("Coletando {} / {}", context.competitor_name, context.product_id)
            try:
                collected = _collector_for(context).collect(context)
            except Exception as exc:
                logger.exception("Falha isolada em {}: {}", context.competitor_name, exc)
                collected = [
                    PriceObservationIn(
                        competitor_id=context.competitor_id,
                        competitor_name=context.competitor_name,
                        tier=context.tier,
                        product_id=context.product_id,
                        category=context.category,
                        url=context.url,
                        collection_status="error",
                        source_type=context.source_type,
                        notes=f"Falha isolada no pipeline: {exc}",
                    ).finalized()
                ]
            if allow_simulated_fallback and all(item.collection_status != "success" for item in collected):
                collected.append(simulated_fallback(context))
            observations.extend(collected)

        if dry_run:
            logger.info("Dry-run: {} observacoes nao gravadas.", len(observations))
        else:
            count = save_observations(session, observations)
            logger.info("{} observacoes gravadas.", count)
    return observations


def run_local_scheduler() -> None:
    scheduler = BlockingScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(collect, "cron", hour="8,17", minute=0)
    scheduler.start()


def main() -> None:
    collect()


if __name__ == "__main__":
    main()

