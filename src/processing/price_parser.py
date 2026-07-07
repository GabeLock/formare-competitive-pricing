from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from src.analytics.scoring import confidence_score
from src.config.settings import COLLECTION_STATUSES, SOURCE_TYPES
from src.processing.matcher import build_item_hash
from src.processing.normalizer import normalize_price

BRL_PATTERNS = [
    re.compile(r"R\$\s*([\d\.]{1,12},\d{2})"),
    re.compile(r'"price"\s*:\s*"?([\d]+\.\d{2})"?'),
    re.compile(r'itemprop=["\']price["\']\s+content=["\']([\d\.]+)["\']'),
]


def parse_brl_price(text: str | None) -> float | None:
    if not text:
        return None
    for pattern in BRL_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        raw = match.group(1)
        if "," in raw:
            raw = raw.replace(".", "").replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            continue
    return None


class PriceObservationIn(BaseModel):
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    competitor_id: str
    competitor_name: str
    tier: Literal["regional_direto", "tecnico_referencia", "benchmark_publico"]
    product_id: str
    category: str | None = None
    url: str
    raw_product_name: str | None = None
    raw_price: str | None = None
    parsed_price: float | None = None
    raw_unit: str | None = None
    normalized_unit: str | None = None
    normalized_price: float | None = None
    length_m: float | None = None
    width_mm: float | None = None
    thickness_mm: float | None = None
    weight_kg: float | None = None
    material: str | None = None
    finish: str | None = None
    coating: str | None = None
    color: str | None = None
    tile_type: str | None = None
    core_type: str | None = None
    core_density: str | None = None
    wave_height: str | None = None
    model: str | None = None
    brand: str | None = None
    availability: str | None = None
    delivery_eta: str | None = None
    freight_info: str | None = None
    payment_condition: str | None = None
    cash_price: float | None = None
    pix_price: float | None = None
    installment_price: float | None = None
    installment_count: int | None = None
    discount_info: str | None = None
    minimum_order: str | None = None
    service_region: str | None = None
    notes: str | None = None
    collection_status: str = "success"
    source_type: str = "public_price"
    confidence_score: int | None = None
    item_hash: str | None = None
    technical_specs: dict[str, Any] = Field(default_factory=dict)
    used_regex_fallback: bool = False
    unit_assumed: bool = False
    fuzzy_match: bool = False
    stale_snapshot: bool = False
    simulated: bool = False

    @field_validator("collection_status")
    @classmethod
    def validate_collection_status(cls, value: str) -> str:
        if value not in COLLECTION_STATUSES:
            raise ValueError(f"invalid collection_status: {value}")
        return value

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        if value not in SOURCE_TYPES:
            raise ValueError(f"invalid source_type: {value}")
        return value

    @field_validator("parsed_price", "normalized_price", "cash_price", "pix_price", "installment_price")
    @classmethod
    def validate_non_negative_price(cls, value: float | None) -> float | None:
        if value is not None and value < 0:
            raise ValueError("price cannot be negative")
        return value

    def finalized(self) -> "PriceObservationIn":
        data = self.model_copy(deep=True)
        if data.parsed_price is None:
            data.parsed_price = parse_brl_price(data.raw_price)
        if data.normalized_unit is None and data.normalized_price is None:
            data.normalized_unit, data.normalized_price = normalize_price(
                data.parsed_price,
                data.raw_unit,
                thickness_mm=data.thickness_mm,
                width_mm=data.width_mm,
                length_m=data.length_m,
            )
        if data.item_hash is None:
            specs = {
                **data.technical_specs,
                "length_m": data.length_m,
                "width_mm": data.width_mm,
                "thickness_mm": data.thickness_mm,
                "material": data.material,
                "finish": data.finish,
                "coating": data.coating,
                "model": data.model,
            }
            data.item_hash = build_item_hash(data.competitor_id, data.product_id, specs)
        if data.confidence_score is None:
            data.confidence_score = confidence_score(
                data.collection_status,
                used_regex_fallback=data.used_regex_fallback,
                unit_assumed=data.unit_assumed,
                fuzzy_match=data.fuzzy_match,
                stale_snapshot=data.stale_snapshot,
            )
        if data.simulated:
            data.source_type = "estimated_price"
            data.confidence_score = min(data.confidence_score or 20, 20)
        return data

