from __future__ import annotations

from dataclasses import dataclass

TIER_RISK_WEIGHT = {
    "regional_direto": 100,
    "tecnico_referencia": 65,
    "benchmark_publico": 35,
}


def confidence_score(
    collection_status: str,
    used_regex_fallback: bool = False,
    unit_assumed: bool = False,
    fuzzy_match: bool = False,
    stale_snapshot: bool = False,
) -> int:
    """Score 0-100. Penalizes weaker collection and parsing signals."""
    score = 100
    if collection_status != "success":
        score -= 40
    if used_regex_fallback:
        score -= 25
    if unit_assumed:
        score -= 15
    if fuzzy_match:
        score -= 15
    if stale_snapshot:
        score -= 10
    return max(0, min(100, score))


def gap_vs_lowest_price(formare_price: float | None, lowest_market_price: float | None) -> float:
    if formare_price is None or lowest_market_price is None or lowest_market_price <= 0:
        return 0.0
    return min(100.0, max(0.0, ((formare_price - lowest_market_price) / lowest_market_price) * 100))


def commercial_risk(
    formare_price: float | None,
    lowest_market_price: float | None,
    tendencia_queda_7d: float = 0,
    disponibilidade_concorrente_mais_barato: float = 0,
    similaridade_tecnica_do_item: float = 50,
    confidence: float = 100,
    tier: str = "benchmark_publico",
) -> float:
    gap = gap_vs_lowest_price(formare_price, lowest_market_price)
    tier_weight = TIER_RISK_WEIGHT.get(tier, 35)
    risk = (
        0.30 * gap
        + 0.20 * min(100, max(0, tendencia_queda_7d))
        + 0.15 * min(100, max(0, disponibilidade_concorrente_mais_barato))
        + 0.15 * min(100, max(0, similaridade_tecnica_do_item))
        + 0.10 * (100 - min(100, max(0, confidence)))
        + 0.10 * tier_weight
    )
    return round(min(100.0, max(0.0, risk)), 2)


def classify_risk(risk: float) -> str:
    if risk <= 25:
        return "Baixo"
    if risk <= 50:
        return "Moderado"
    if risk <= 75:
        return "Alto"
    return "Critico"


@dataclass(frozen=True)
class CommercialPosition:
    label: str
    margin: float | None


def classify_commercial_position(margin: float | None, target_margin: float | None) -> str:
    if margin is None:
        return "Sem dados"
    if target_margin is None:
        target_margin = 0.25
    if margin < 0:
        return "Fora de mercado"
    if margin < target_margin * 0.5:
        return "Pressionado"
    if margin < target_margin:
        return "Atencao"
    if margin > target_margin * 1.3:
        return "Oportunidade de margem"
    return "Competitivo"

