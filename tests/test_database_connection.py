from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from src.database import connection
from src.database.connection import DatabaseUnavailableError, database_url
from src.database.repository import load_yaml
from src.config.settings import COMPETITORS_CONFIG, PRODUCTS_CONFIG


def test_database_url_defaults_to_local_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert database_url().startswith("sqlite:///")


def test_database_url_normalizes_postgres_scheme(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@host:5432/db")
    assert database_url() == "postgresql+psycopg://user:pass@host:5432/db"


def test_ensure_database_connection_retries_transient_failure(monkeypatch):
    calls = 0

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def execute(self, statement):
            assert str(statement) == str(text("SELECT 1"))

    class FakeEngine:
        def connect(self):
            nonlocal calls
            calls += 1
            if calls < 3:
                raise OperationalError("SELECT 1", {}, OSError("temporary failure"))
            return FakeConnection()

        def dispose(self):
            pass

    monkeypatch.setattr(connection, "engine", FakeEngine())

    connection.ensure_database_connection()

    assert calls == 3


def test_ensure_database_connection_exposes_safe_error(monkeypatch):
    class OfflineEngine:
        def connect(self):
            raise OperationalError("SELECT 1", {}, OSError("offline"))

        def dispose(self):
            pass

    monkeypatch.setattr(connection, "engine", OfflineEngine())

    try:
        connection.ensure_database_connection(attempts=2)
    except DatabaseUnavailableError as error:
        assert "DATABASE_URL" in str(error)
    else:
        raise AssertionError("Expected a safe connectivity error")


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
