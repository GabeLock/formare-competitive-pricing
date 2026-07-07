"""
price_detector.py

Fallback genérico: quando um scraper específico não tem (ou ainda não tem)
um seletor CSS dedicado, tentamos detectar automaticamente um preço em Real
dentro do HTML. Se nada for encontrado, a fonte é marcada como
`price_type=unavailable` — o que é o comportamento correto para os sites que
trabalham só com "solicitar orçamento" (Formare, Perfil Telhas, Suri Metais,
Ananda Metais e, possivelmente, Galvaminas / Telhas Barreiro / Açotel /
Multiperfil / Servicorte até serem verificados).

IMPORTANTE: esta função NUNCA deve preencher formulários. Ela só analisa o
HTML que já foi retornado por um GET simples.
"""

from __future__ import annotations

import re
from typing import Optional

from bs4 import BeautifulSoup

# Padrões comuns de preço em sites brasileiros de e-commerce
PRICE_PATTERNS = [
    re.compile(r"R\$\s*([\d\.]{1,10},\d{2})"),          # R$ 1.234,56
    re.compile(r'"price"\s*:\s*"?([\d]+\.\d{2})"?'),     # JSON-LD / VTEX: "price": 94.76
    re.compile(r'itemprop=["\']price["\']\s+content=["\']([\d\.]+)["\']'),
]

STEEL_DENSITY_KG_PER_M3 = 7850  # aço carbono, aproximado


def detect_price_in_html(html: str) -> Optional[float]:
    """Tenta achar um preço em BRL no HTML bruto. Retorna float (em reais) ou None."""
    for pattern in PRICE_PATTERNS:
        match = pattern.search(html)
        if match:
            raw = match.group(1)
            if "," in raw:
                raw = raw.replace(".", "").replace(",", ".")
            try:
                return float(raw)
            except ValueError:
                continue
    return None


def detect_price_with_selector(html: str, css_selector: str) -> Optional[float]:
    """Tenta extrair preço usando um seletor CSS específico do site; cai no
    fallback genérico se o seletor não encontrar nada."""
    soup = BeautifulSoup(html, "lxml")
    el = soup.select_one(css_selector)
    if el is not None:
        text = el.get_text(strip=True)
        match = re.search(r"([\d\.]{1,10},\d{2})", text)
        if match:
            raw = match.group(1).replace(".", "").replace(",", ".")
            try:
                return float(raw)
            except ValueError:
                pass
    return detect_price_in_html(html)


def normalize_price_per_kg(
    price_value: float,
    unit_measure: str,
    thickness_mm: Optional[float] = None,
    width_mm: Optional[float] = None,
    length_m: Optional[float] = None,
) -> Optional[float]:
    """
    Converte preço para R$/kg quando houver espessura + largura (chapa/telha/perfil
    de aço), permitindo comparar concorrentes que vendem por metro, m² ou peça.

    kg por metro linear = espessura(m) * largura(m) * 1 metro de comprimento * densidade(kg/m3)
    """
    if unit_measure == "R$/kg":
        return price_value

    if thickness_mm is None or width_mm is None:
        return None  # dado insuficiente para normalizar

    thickness_m = thickness_mm / 1000
    width_m = width_mm / 1000

    if unit_measure in ("R$/m", "R$/peça", "R$/un") :
        kg_per_linear_meter = thickness_m * width_m * STEEL_DENSITY_KG_PER_M3
        if kg_per_linear_meter <= 0:
            return None
        if unit_measure == "R$/m":
            return price_value / kg_per_linear_meter
        if length_m:
            total_kg = kg_per_linear_meter * length_m
            return price_value / total_kg if total_kg > 0 else None
        return None

    if unit_measure == "R$/m2":
        kg_per_m2 = thickness_m * STEEL_DENSITY_KG_PER_M3
        return price_value / kg_per_m2 if kg_per_m2 > 0 else None

    return None
