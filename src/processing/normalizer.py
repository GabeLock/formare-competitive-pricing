from __future__ import annotations

STEEL_DENSITY_KG_PER_M3 = 7850


def steel_kg_per_linear_meter(thickness_mm: float, width_mm: float) -> float:
    return (thickness_mm / 1000) * (width_mm / 1000) * STEEL_DENSITY_KG_PER_M3


def steel_kg_per_square_meter(thickness_mm: float) -> float:
    return (thickness_mm / 1000) * STEEL_DENSITY_KG_PER_M3


def normalize_price(
    parsed_price: float | None,
    raw_unit: str | None,
    thickness_mm: float | None = None,
    width_mm: float | None = None,
    length_m: float | None = None,
) -> tuple[str | None, float | None]:
    if parsed_price is None:
        return None, None

    unit = (raw_unit or "").lower().replace("r$/", "").strip()
    if unit in {"kg", "r$/kg"}:
        return "kg", parsed_price

    if unit in {"m", "metro", "metro linear"}:
        if thickness_mm and width_mm:
            kg_m = steel_kg_per_linear_meter(thickness_mm, width_mm)
            return "kg", parsed_price / kg_m if kg_m > 0 else None
        return "m", parsed_price

    if unit in {"m2", "m²", "metro quadrado"}:
        if thickness_mm:
            kg_m2 = steel_kg_per_square_meter(thickness_mm)
            return "kg", parsed_price / kg_m2 if kg_m2 > 0 else None
        return "m2", parsed_price

    if unit in {"peca", "peça", "un", "unidade", "rolo"}:
        if thickness_mm and width_mm and length_m:
            total_kg = steel_kg_per_linear_meter(thickness_mm, width_mm) * length_m
            return "kg", parsed_price / total_kg if total_kg > 0 else None
        return "peca", parsed_price

    return None, None

