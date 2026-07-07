from src.analytics.scoring import classify_risk, commercial_risk, confidence_score, gap_vs_lowest_price


def test_confidence_score_floor_and_penalties():
    assert confidence_score("error", True, True, True, True) == 0
    assert confidence_score("success") == 100


def test_gap_handles_zero_market_price():
    assert gap_vs_lowest_price(100, 0) == 0
    assert gap_vs_lowest_price(120, 100) == 20


def test_commercial_risk_regional_tier_weighs_more():
    regional = commercial_risk(120, 100, confidence=100, tier="regional_direto")
    benchmark = commercial_risk(120, 100, confidence=100, tier="benchmark_publico")
    assert regional > benchmark


def test_classify_risk_boundaries():
    assert classify_risk(25) == "Baixo"
    assert classify_risk(50) == "Moderado"
    assert classify_risk(75) == "Alto"
    assert classify_risk(76) == "Critico"

