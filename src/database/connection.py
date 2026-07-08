from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import DB_PATH
from src.database.models import Base


def get_engine(db_path=DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", future=True)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        for table_name in ("monitored_urls", "price_observations"):
            columns = {
                row[1]
                for row in connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
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
