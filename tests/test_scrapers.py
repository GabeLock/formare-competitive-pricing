"""
Testes básicos — não fazem nenhuma requisição de rede real.
Rodar com: pytest
"""

from scrapers.price_detector import (
    detect_price_in_html,
    detect_price_with_selector,
    normalize_price_per_kg,
)

SAMPLE_HTML_WITH_PRICE = """
<html><body>
  <div class="preco-produto">R$ 94,76</div>
</body></html>
"""

SAMPLE_HTML_NO_PRICE = """
<html><body>
  <button>Fazer Orçamento</button>
</body></html>
"""


def test_detect_price_in_html_finds_price():
    price = detect_price_in_html(SAMPLE_HTML_WITH_PRICE)
    assert price == 94.76


def test_detect_price_in_html_returns_none_when_absent():
    price = detect_price_in_html(SAMPLE_HTML_NO_PRICE)
    assert price is None


def test_detect_price_with_selector():
    price = detect_price_with_selector(SAMPLE_HTML_WITH_PRICE, ".preco-produto")
    assert price == 94.76


def test_normalize_price_per_kg_by_linear_meter():
    # Chapa de 0,43mm de espessura, 1000mm de largura, vendida a R$50/m
    result = normalize_price_per_kg(
        price_value=50.0,
        unit_measure="R$/m",
        thickness_mm=0.43,
        width_mm=1000,
    )
    assert result is not None
    assert 14 < result < 16  # ordem de grandeza esperada para aço ~7850 kg/m3


def test_normalize_price_per_kg_returns_none_without_specs():
    result = normalize_price_per_kg(price_value=50.0, unit_measure="R$/m")
    assert result is None


def test_normalize_price_per_kg_passthrough_when_already_per_kg():
    result = normalize_price_per_kg(price_value=12.5, unit_measure="R$/kg")
    assert result == 12.5
