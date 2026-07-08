from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Competitor(Base):
    __tablename__ = "competitors"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    website: Mapped[str | None] = mapped_column(String(500))
    tier: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    region: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    monitored_urls: Mapped[list["MonitoredUrl"]] = relationship(back_populates="competitor")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    formare_product_name: Mapped[str] = mapped_column(String(250), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    material: Mapped[str | None] = mapped_column(String(200))
    default_unit: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    monitored_urls: Mapped[list["MonitoredUrl"]] = relationship(back_populates="product")


class MonitoredUrl(Base):
    __tablename__ = "monitored_urls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    competitor_id: Mapped[str] = mapped_column(ForeignKey("competitors.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    url: Mapped[str | None] = mapped_column(String(1000))
    query: Mapped[str | None] = mapped_column(String(500))
    url_type: Mapped[str | None] = mapped_column(String(80))
    collection_method: Mapped[str] = mapped_column(String(80), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    customer_segment: Mapped[str] = mapped_column(String(40), default="b2b_atacado", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)

    competitor: Mapped[Competitor] = relationship(back_populates="monitored_urls")
    product: Mapped[Product] = relationship(back_populates="monitored_urls")

    __table_args__ = (
        UniqueConstraint("competitor_id", "product_id", "url", "query", name="uq_monitored_source"),
    )


class PriceObservation(Base):
    __tablename__ = "price_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    competitor_id: Mapped[str] = mapped_column(String(80), index=True)
    competitor_name: Mapped[str] = mapped_column(String(200))
    product_id: Mapped[str] = mapped_column(String(100), index=True)
    category: Mapped[str | None] = mapped_column(String(100))
    tier: Mapped[str] = mapped_column(String(40), index=True)
    url: Mapped[str | None] = mapped_column(String(1000))
    raw_product_name: Mapped[str | None] = mapped_column(Text)
    raw_price: Mapped[str | None] = mapped_column(String(100))
    parsed_price: Mapped[float | None] = mapped_column(Float)
    raw_unit: Mapped[str | None] = mapped_column(String(80))
    normalized_unit: Mapped[str | None] = mapped_column(String(80))
    normalized_price: Mapped[float | None] = mapped_column(Float)
    length_m: Mapped[float | None] = mapped_column(Float)
    width_mm: Mapped[float | None] = mapped_column(Float)
    thickness_mm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    material: Mapped[str | None] = mapped_column(String(200))
    finish: Mapped[str | None] = mapped_column(String(200))
    coating: Mapped[str | None] = mapped_column(String(200))
    color: Mapped[str | None] = mapped_column(String(100))
    tile_type: Mapped[str | None] = mapped_column(String(120))
    core_type: Mapped[str | None] = mapped_column(String(120))
    core_density: Mapped[str | None] = mapped_column(String(120))
    wave_height: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(120))
    brand: Mapped[str | None] = mapped_column(String(200))
    availability: Mapped[str | None] = mapped_column(String(200))
    delivery_eta: Mapped[str | None] = mapped_column(String(200))
    freight_info: Mapped[str | None] = mapped_column(Text)
    payment_condition: Mapped[str | None] = mapped_column(Text)
    cash_price: Mapped[float | None] = mapped_column(Float)
    pix_price: Mapped[float | None] = mapped_column(Float)
    installment_price: Mapped[float | None] = mapped_column(Float)
    installment_count: Mapped[int | None] = mapped_column(Integer)
    discount_info: Mapped[str | None] = mapped_column(Text)
    minimum_order: Mapped[str | None] = mapped_column(String(200))
    service_region: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    collection_status: Mapped[str] = mapped_column(String(40), index=True)
    source_type: Mapped[str] = mapped_column(String(80), index=True)
    customer_segment: Mapped[str] = mapped_column(String(40), default="b2b_atacado", index=True)
    confidence_score: Mapped[int] = mapped_column(Integer)
    item_hash: Mapped[str] = mapped_column(String(80), index=True)
    technical_specs_json: Mapped[str | None] = mapped_column(Text)
    simulated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class FormareCost(Base):
    __tablename__ = "formare_costs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    internal_cost: Mapped[float | None] = mapped_column(Float)
    sale_price: Mapped[float | None] = mapped_column(Float)
    target_margin: Mapped[float | None] = mapped_column(Float)
    minimum_margin: Mapped[float | None] = mapped_column(Float)
    freight_cost: Mapped[float | None] = mapped_column(Float)
    taxes: Mapped[float | None] = mapped_column(Float)
    commission: Mapped[float | None] = mapped_column(Float)
    variable_expenses: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    product_id: Mapped[str | None] = mapped_column(String(100), index=True)
    competitor_id: Mapped[str | None] = mapped_column(String(80), index=True)
    alert_type: Mapped[str] = mapped_column(String(120))
    severity: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
