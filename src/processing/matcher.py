from __future__ import annotations

import hashlib
import json


def build_item_hash(
    competitor_id: str,
    product_id: str,
    technical_specs: dict | None = None,
) -> str:
    stable_specs = technical_specs or {}
    payload = {
        "competitor_id": competitor_id,
        "product_id": product_id,
        "technical_specs": stable_specs,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]

