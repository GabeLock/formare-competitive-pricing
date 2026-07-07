from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DATABASE_DIR = DATA_DIR / "database"
DB_PATH = DATABASE_DIR / "prices.db"
LOG_DIR = ROOT_DIR / "logs"

PRODUCTS_CONFIG = ROOT_DIR / "src" / "config" / "products.yaml"
COMPETITORS_CONFIG = ROOT_DIR / "src" / "config" / "competitors.yaml"

MIN_SECONDS_BETWEEN_DOMAIN_REQUESTS = 4
DEFAULT_TIMEOUT_SECONDS = 25

COLLECTION_STATUSES = {
    "success",
    "error",
    "no_price",
    "quote_required",
    "blocked",
    "unavailable",
}

SOURCE_TYPES = {
    "public_price",
    "marketplace",
    "quote_required",
    "manual_quote",
    "estimated_price",
}

TIERS = {
    "regional_direto": 0,
    "tecnico_referencia": 1,
    "benchmark_publico": 2,
}

