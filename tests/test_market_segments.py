import pandas as pd

from src.analytics.market_segments import b2b_competitive_reference, b2c_retail_ceiling


def test_b2b_reference_ignores_b2c_prices():
    df = pd.DataFrame(
        [
            {"product_id": "p1", "parsed_price": 90.0, "customer_segment": "b2b_atacado"},
            {"product_id": "p1", "parsed_price": 120.0, "customer_segment": "b2b_atacado"},
            {"product_id": "p1", "parsed_price": 300.0, "customer_segment": "b2c_varejo"},
        ]
    )

    ref = b2b_competitive_reference(df)

    assert ref.loc[0, "menor_preco_b2b"] == 90.0
    assert ref.loc[0, "media_b2b"] == 105.0


def test_b2c_ceiling_is_separate_from_b2b_average():
    df = pd.DataFrame(
        [
            {"product_id": "p1", "parsed_price": 90.0, "customer_segment": "b2b_atacado"},
            {"product_id": "p1", "parsed_price": 300.0, "customer_segment": "b2c_varejo"},
            {"product_id": "p1", "parsed_price": 250.0, "customer_segment": "b2c_varejo"},
        ]
    )

    ceiling = b2c_retail_ceiling(df)

    assert ceiling.loc[0, "teto_b2c_varejo"] == 300.0
    assert ceiling.loc[0, "media_b2c_varejo"] == 275.0
