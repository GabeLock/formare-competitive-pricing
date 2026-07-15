from __future__ import annotations

from collections.abc import Iterator
import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import DB_PATH
from src.database.models import Base


def database_url() -> str:
    """Use hosted PostgreSQL when DATABASE_URL is configured, otherwise SQLite."""
    configured = os.getenv("DATABASE_URL", "").strip()
    if not configured:
        return f"sqlite:///{DB_PATH}"
    if configured.startswith("postgres://"):
        configured = "postgresql://" + configured.removeprefix("postgres://")
    if configured.startswith("postgresql://"):
        return "postgresql+psycopg://" + configured.removeprefix("postgresql://")
    return configured


def get_engine(url: str | None = None) -> Engine:
    resolved_url = url or database_url()
    if resolved_url.startswith("sqlite:"):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(resolved_url, future=True)
    return create_engine(resolved_url, future=True, pool_pre_ping=True, connect_args={"connect_timeout": 15})


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(engine)
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as connection:
        for table_name in ("monitored_urls", "price_observations"):
            columns = {
                column["name"]
                for column in inspect(connection).get_columns(table_name)
            }
            if "customer_segment" not in columns:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        "ADD COLUMN customer_segment VARCHAR(40) DEFAULT 'b2b_atacado'"
                    )
                )


def get_session() -> Iterator[Session]:
    init_db()
    with SessionLocal() as session:
        yield session
