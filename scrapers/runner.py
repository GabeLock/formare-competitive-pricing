"""
runner.py

Orquestrador principal. Lê config/sources.yaml, roda cada scraper (uma
fonte não pode derrubar as outras), calcula o preço normalizado por kg
quando possível, e grava tudo em:
  - data/prices.db   (SQLite, histórico completo, tabela price_observations)
  - data/prices.csv  (append incremental, mesmo schema, para leitura rápida)

Uso:
    python -m scrapers.runner

Chamado automaticamente 2x/dia pelo GitHub Actions
(.github/workflows/collect_prices.yml).
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import asdict
from pathlib import Path

import pandas as pd
import yaml

from scrapers.base_scraper import PriceObservation
from scrapers.price_detector import normalize_price_per_kg

# Scrapers específicos / fábricas
from scrapers import (
    formare,
    perfil_telhas,
    galvaminas,
    telhas_barreiro,
    suri_metais,
    acotel,
    ananda_metais,
    multiperfil,
    gravia,
)
from scrapers.marketplaces import build_mercado_livre_scraper, build_generic_tier3_scraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "sources.yaml"
DB_PATH = ROOT / "data" / "prices.db"
CSV_PATH = ROOT / "data" / "prices.csv"

# Mapa "nome do concorrente no yaml" -> módulo/fábrica de scraper dedicado
# (Gravia e Mercado Livre têm implementação própria; os demais usam o
# GenericScraper por trás do build_scraper() de cada arquivo fino.)
DEDICATED_BUILDERS = {
    "Formare Metais": formare.build_scraper,
    "Perfil Telhas": perfil_telhas.build_scraper,
    "Galvaminas": galvaminas.build_scraper,
    "Telhas Barreiro": telhas_barreiro.build_scraper,
    "Suri Metais": suri_metais.build_scraper,
    "Açotel": acotel.build_scraper,
    "Ananda Metais": ananda_metais.build_scraper,
    "Multiperfil": multiperfil.build_scraper,
    "Gravia": gravia.build_scraper,
}

TIER3_GENERIC_NAMES = {
    "Telhas Online (CBS)",
    "Grupo Pizzinatto",
    "Servicorte",
}


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_all() -> list[PriceObservation]:
    config = load_config()
    all_observations: list[PriceObservation] = []

    for competitor in config.get("competitors", []):
        name = competitor["name"]
        region = competitor.get("region", "")

        try:
            if name == "Mercado Livre":
                scraper = build_mercado_livre_scraper()
                for entry in competitor.get("urls", []):
                    query = entry["query"]
                    category = entry["category"]
                    logger.info("Coletando Mercado Livre: %s", query)
                    all_observations.extend(scraper.collect_by_query(query, category))
                continue

            if name in TIER3_GENERIC_NAMES:
                scraper = build_generic_tier3_scraper(name, region)
            elif name in DEDICATED_BUILDERS:
                scraper = DEDICATED_BUILDERS[name]()
            else:
                logger.warning("Concorrente '%s' sem builder definido em runner.py — pulando.", name)
                continue

            for entry in competitor.get("urls", []):
                url = entry["url"]
                category = entry["category"]
                logger.info("Coletando %s [%s]: %s", name, category, url)
                all_observations.extend(scraper.collect(url, category))

        except Exception as exc:
            # Uma fonte quebrada nunca derruba as demais.
            logger.exception("Falha inesperada ao processar concorrente '%s': %s", name, exc)
            continue

    # Normalização de preço por kg quando houver espessura/largura conhecidas
    for obs in all_observations:
        if obs.price_value is not None and obs.unit_measure:
            obs.normalized_price_per_kg = normalize_price_per_kg(
                price_value=obs.price_value,
                unit_measure=obs.unit_measure,
                thickness_mm=obs.spec_thickness_mm,
                width_mm=obs.spec_width_mm,
                length_m=obs.spec_length_m,
            )

    return all_observations


def persist(observations: list[PriceObservation]) -> None:
    if not observations:
        logger.warning("Nenhuma observação coletada nesta rodada.")
        return

    df = pd.DataFrame([asdict(o) for o in observations])

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("price_observations", conn, if_exists="append", index=False)

    header_needed = not CSV_PATH.exists()
    df.to_csv(CSV_PATH, mode="a", header=header_needed, index=False)

    logger.info("Persistidas %d observações (%d fontes com preço, %d manuais/indisponíveis).",
                len(df),
                (df["price_type"] == "auto_scraped").sum(),
                (df["price_type"] != "auto_scraped").sum())


def main() -> None:
    observations = run_all()
    persist(observations)


if __name__ == "__main__":
    main()
