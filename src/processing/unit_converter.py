from __future__ import annotations

UNIT_ALIASES = {
    "kg": "kg",
    "quilo": "kg",
    "m": "m",
    "metro": "m",
    "m2": "m2",
    "m²": "m2",
    "metro quadrado": "m2",
    "un": "peca",
    "unidade": "peca",
    "peca": "peca",
    "peça": "peca",
    "rolo": "rolo",
}


def normalize_unit(unit: str | None) -> str | None:
    if not unit:
        return None
    cleaned = unit.strip().lower().replace("r$/", "")
    return UNIT_ALIASES.get(cleaned, cleaned)

