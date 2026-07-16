from __future__ import annotations

from collections.abc import Iterator
import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import DB_PATH
from src.database.models import Base


class DatabaseUnavailableError(RuntimeError):
    """Raised when the hosted database cannot be reached after a short retry."""


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
    return create_engine(
        resolved_url,
        future=True,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=3,
        max_overflow=2,
        pool_timeout=20,
        connect_args={
            "connect_timeout": 15,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 3,
        },
    )


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


def ensure_database_connection(attempts: int = 3) -> None:
    """Check connectivity, retrying brief wake-up/network interruptions safely."""
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except (OperationalError, DBAPIError) as error:
            last_error = error
            # A connection left in the pool after a server wake-up must not be reused.
            engine.dispose()
    raise DatabaseUnavailableError(
        "Nao foi possivel conectar ao banco de dados hospedado. "
        "Verifique se DATABASE_URL usa a URL do pooler do Supabase com sslmode=require."
    ) from last_error


def init_db() -> None:
    ensure_database_connection()
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
