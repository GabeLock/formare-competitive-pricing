from src.database.connection import database_url
from src.database.repository import load_yaml
from src.config.settings import COMPETITORS_CONFIG, PRODUCTS_CONFIG


def test_database_url_defaults_to_local_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert database_url().startswith("sqlite:///")


def test_database_url_normalizes_postgres_scheme(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@host:5432/db")
    assert database_url() == "postgresql+psycopg://user:pass@host:5432/db"


def test_every_monitored_product_has_at_least_two_active_sources():
    products = {product["id"] for product in load_yaml(PRODUCTS_CONFIG)["products"]}
    source_count = {product_id: 0 for product_id in products}
    for competitor in load_yaml(COMPETITORS_CONFIG)["competitors"]:
        if not competitor.get("active", True):
            continue
        for source in competitor.get("urls", []):
            if source.get("active", True):
                source_count[source["product_id"]] += 1
    assert all(count >= 2 for count in source_count.values()), source_count
