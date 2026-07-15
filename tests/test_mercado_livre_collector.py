from src.collectors.mercado_livre_collector import is_comparable_result
from bs4 import BeautifulSoup

from src.collectors.generic_html_collector import structured_product_price


def test_marketplace_result_matches_its_monitored_product():
    assert is_comparable_result("perfil_montante_drywall", "Perfil montante drywall 70 mm 3 m")
    assert is_comparable_result("telha_termoacustica_sanduiche_trapezio", "Telha sanduiche EPS trapezoidal")


def test_marketplace_result_rejects_accessory_or_other_product():
    assert not is_comparable_result("perfil_montante_drywall", "Parafuso para perfil drywall")
    assert not is_comparable_result("rolinho_galvalume", "Telha galvalume trapezoidal")


def test_structured_product_price_reads_json_ld_offer():
    soup = BeautifulSoup(
        '<script type="application/ld+json">'
        '{"@type":"Product","name":"Placa Drywall ST",'
        '"offers":{"price":"90.78"}}'
        '</script>',
        "lxml",
    )
    assert structured_product_price(soup) == ("Placa Drywall ST", 90.78)
