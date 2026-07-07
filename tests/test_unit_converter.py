from src.processing.normalizer import normalize_price, steel_kg_per_linear_meter


def test_steel_kg_per_linear_meter():
    kg_m = steel_kg_per_linear_meter(0.43, 1000)
    assert 3.3 < kg_m < 3.5


def test_normalize_meter_to_kg():
    unit, price = normalize_price(50, "m", thickness_mm=0.43, width_mm=1000)
    assert unit == "kg"
    assert 14 < price < 16


def test_normalize_without_specs_keeps_meter():
    unit, price = normalize_price(50, "m")
    assert unit == "m"
    assert price == 50

