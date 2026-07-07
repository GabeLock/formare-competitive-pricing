from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.config.settings import COMPETITORS_CONFIG, DB_PATH, PRODUCTS_CONFIG
from src.database.connection import SessionLocal, init_db
from src.database.models import Alert, Competitor, FormareCost, MonitoredUrl, PriceObservation, Product
from src.processing.price_parser import PriceObservationIn


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def seed_reference_data(session: Session) -> None:
    products = load_yaml(PRODUCTS_CONFIG).get("products", [])
    competitors = load_yaml(COMPETITORS_CONFIG).get("competitors", [])

    for item in products:
        product = session.get(Product, item["id"]) or Product(id=item["id"])
        product.formare_product_name = item["formare_product_name"]
        product.category = item["category"]
        product.material = item.get("material")
        product.default_unit = item.get("default_unit")
        product.notes = item.get("notes")
        product.active = bool(item.get("active", True))
        session.merge(product)

    for item in competitors:
        competitor = session.get(Competitor, item["id"]) or Competitor(id=item["id"])
        competitor.name = item["name"]
        competitor.website = item.get("website")
        competitor.tier = item["tier"]
        competitor.region = item.get("region")
        competitor.notes = item.get("notes")
        competitor.active = bool(item.get("active", True))
        session.merge(competitor)

        session.execute(delete(MonitoredUrl).where(MonitoredUrl.competitor_id == item["id"]))
        for url_item in item.get("urls", []):
            session.add(
                MonitoredUrl(
                    competitor_id=item["id"],
                    product_id=url_item["product_id"],
                    url=url_item.get("url"),
                    query=url_item.get("query"),
                    url_type=url_item.get("url_type"),
                    collection_method=url_item["collection_method"],
                    source_type=url_item["source_type"],
                    active=bool(url_item.get("active", True)),
                    notes=url_item.get("notes"),
                )
            )
    session.commit()


def initialize_database() -> None:
    init_db()
    with SessionLocal() as session:
        seed_reference_data(session)


def active_sources(session: Session, source_id: str | None = None) -> list[tuple[Competitor, Product, MonitoredUrl]]:
    stmt = (
        select(Competitor, Product, MonitoredUrl)
        .join(MonitoredUrl, MonitoredUrl.competitor_id == Competitor.id)
        .join(Product, MonitoredUrl.product_id == Product.id)
        .where(Competitor.active.is_(True), Product.active.is_(True), MonitoredUrl.active.is_(True))
        .order_by(Competitor.tier, Competitor.name, Product.formare_product_name)
    )
    if source_id:
        stmt = stmt.where((Competitor.id == source_id) | (Competitor.name == source_id))
    return list(session.execute(stmt).all())


def save_observations(session: Session, observations: Iterable[PriceObservationIn]) -> int:
    count = 0
    for obs in observations:
        item = obs.finalized()
        session.add(
            PriceObservation(
                collected_at=item.collected_at,
                competitor_id=item.competitor_id,
                competitor_name=item.competitor_name,
                tier=item.tier,
                product_id=item.product_id,
                category=item.category,
                url=item.url,
                raw_product_name=item.raw_product_name,
                raw_price=item.raw_price,
                parsed_price=item.parsed_price,
                raw_unit=item.raw_unit,
                normalized_unit=item.normalized_unit,
                normalized_price=item.normalized_price,
                length_m=item.length_m,
                width_mm=item.width_mm,
                thickness_mm=item.thickness_mm,
                weight_kg=item.weight_kg,
                material=item.material,
                finish=item.finish,
                coating=item.coating,
                color=item.color,
                tile_type=item.tile_type,
                core_type=item.core_type,
                core_density=item.core_density,
                wave_height=item.wave_height,
                model=item.model,
                brand=item.brand,
                availability=item.availability,
                delivery_eta=item.delivery_eta,
                freight_info=item.freight_info,
                payment_condition=item.payment_condition,
                cash_price=item.cash_price,
                pix_price=item.pix_price,
                installment_price=item.installment_price,
                installment_count=item.installment_count,
                discount_info=item.discount_info,
                minimum_order=item.minimum_order,
                service_region=item.service_region,
                notes=item.notes,
                collection_status=item.collection_status,
                source_type=item.source_type,
                confidence_score=item.confidence_score or 0,
                item_hash=item.item_hash or "",
                technical_specs_json=json.dumps(item.technical_specs, ensure_ascii=True, default=str),
                simulated=item.simulated,
            )
        )
        count += 1
    session.commit()
    return count


def read_sql(query: str) -> pd.DataFrame:
    initialize_database()
    return pd.read_sql(query, f"sqlite:///{DB_PATH}")


def latest_observations() -> pd.DataFrame:
    return read_sql("SELECT * FROM price_observations ORDER BY collected_at DESC")


def competitors_df() -> pd.DataFrame:
    return read_sql("SELECT * FROM competitors ORDER BY tier, name")


def products_df() -> pd.DataFrame:
    return read_sql("SELECT * FROM products ORDER BY category, formare_product_name")


def formare_costs_df() -> pd.DataFrame:
    return read_sql("SELECT * FROM formare_costs ORDER BY updated_at DESC")


def alerts_df() -> pd.DataFrame:
    return read_sql("SELECT * FROM alerts ORDER BY created_at DESC")


def upsert_formare_cost(
    session: Session,
    product_id: str,
    internal_cost: float | None,
    sale_price: float | None,
    target_margin: float | None,
    minimum_margin: float | None,
    freight_cost: float | None,
    taxes: float | None,
    commission: float | None,
    variable_expenses: float | None,
    notes: str | None,
) -> None:
    session.add(
        FormareCost(
            product_id=product_id,
            internal_cost=internal_cost,
            sale_price=sale_price,
            target_margin=target_margin,
            minimum_margin=minimum_margin,
            freight_cost=freight_cost,
            taxes=taxes,
            commission=commission,
            variable_expenses=variable_expenses,
            notes=notes,
            updated_at=datetime.now(timezone.utc),
        )
    )
    session.commit()


def save_manual_quote(
    session: Session,
    competitor_id: str,
    competitor_name: str,
    tier: str,
    product_id: str,
    category: str | None,
    url: str,
    price: float,
    raw_unit: str,
    notes: str | None = None,
) -> None:
    observation = PriceObservationIn(
        competitor_id=competitor_id,
        competitor_name=competitor_name,
        tier=tier,
        product_id=product_id,
        category=category,
        url=url,
        raw_product_name="Cotacao manual",
        raw_price=f"R$ {price:.2f}",
        parsed_price=price,
        raw_unit=raw_unit,
        collection_status="success",
        source_type="manual_quote",
        notes=notes,
    )
    save_observations(session, [observation])


def save_alerts(session: Session, alerts: Iterable[dict]) -> int:
    count = 0
    for alert in alerts:
        session.add(Alert(**alert))
        count += 1
    session.commit()
    return count

