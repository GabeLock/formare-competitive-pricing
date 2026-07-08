from src.processing.price_parser import PriceObservationIn, parse_brl_price


def test_parse_brl_price_pt_br():
    assert parse_brl_price("Preco: R$ 1.234,56") == 1234.56


def test_observation_rejects_negative_price():
    try:
        PriceObservationIn(
            competitor_id="c",
            competitor_name="C",
            tier="benchmark_publico",
            product_id="p",
            url="https://example.com",
            parsed_price=-1,
        )
    except ValueError as exc:
        assert "price cannot be negative" in str(exc)
    else:
        raise AssertionError("negative price should fail")


def test_observation_finalized_adds_hash_and_confidence():
    obs = PriceObservationIn(
        competitor_id="c",
        competitor_name="C",
        tier="benchmark_publico",
        product_id="p",
        url="https://example.com",
        raw_price="R$ 10,00",
        raw_unit="peca",
        collection_status="success",
    ).finalized()
    assert obs.parsed_price == 10.0
    assert obs.item_hash
    assert obs.confidence_score == 100
    assert obs.customer_segment == "b2b_atacado"


def test_observation_accepts_b2c_segment():
    obs = PriceObservationIn(
        competitor_id="c",
        competitor_name="C",
        tier="benchmark_publico",
        product_id="p",
        url="https://example.com",
        parsed_price=99,
        customer_segment="b2c_varejo",
    )
    assert obs.customer_segment == "b2c_varejo"
