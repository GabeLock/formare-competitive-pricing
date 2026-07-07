"""
base_scraper.py

Classe base para todos os coletores de preço.

Regras não-negociáveis embutidas aqui (não duplicar em cada scraper):
  1. Respeitar robots.txt do domínio antes de qualquer requisição.
  2. Rate limit mínimo entre requisições ao mesmo domínio.
  3. User-Agent identificável, com contato.
  4. Nunca preencher/enviar formulários (POST) de orçamento/contato.
  5. Salvar snapshot bruto (HTML) de toda coleta bem-sucedida, para auditoria.
  6. Falha em uma fonte não pode derrubar o pipeline inteiro (ver runner.py).
"""

from __future__ import annotations

import time
import re
import logging
import urllib.robotparser as robotparser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

USER_AGENT = (
    "FormareCompetitivePricingBot/1.0 "
    "(+monitoramento de precos publicos para inteligencia de mercado; "
    "contato: substituir-pelo-seu-email@dominio.com.br)"
)

MIN_SECONDS_BETWEEN_REQUESTS = 4  # rate limit por domínio
SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw_snapshots"

# Regex genérica para detectar valores em Real (fallback do price_detector.py)
PRICE_REGEX = re.compile(r"R\$\s*([\d\.]{1,10},\d{2})")


@dataclass
class PriceObservation:
    """Representa uma linha da tabela price_observations."""

    competitor_name: str
    competitor_tier: str
    competitor_city_region: str
    product_category: str
    source_url: str
    product_description_raw: str = ""
    spec_thickness_mm: Optional[float] = None
    spec_coating: Optional[str] = None
    spec_width_mm: Optional[float] = None
    spec_length_m: Optional[float] = None
    unit_measure: Optional[str] = None
    price_value: Optional[float] = None
    price_type: str = "unavailable"  # auto_scraped | manual_quote | unavailable
    normalized_price_per_kg: Optional[float] = None
    payment_terms_notes: str = ""
    stock_status_notes: str = ""
    notes: str = ""
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class RobotsDisallowedError(Exception):
    """Levantado quando robots.txt proíbe a coleta desta URL."""


class BaseScraper:
    """
    Subclasses devem implementar:
        fetch(url) -> str (HTML bruto)      [normalmente já resolvido aqui via get()]
        parse(html, url, category) -> list[PriceObservation]
    """

    def __init__(self, competitor_name: str, competitor_tier: str, competitor_city_region: str):
        self.competitor_name = competitor_name
        self.competitor_tier = competitor_tier
        self.competitor_city_region = competitor_city_region
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})
        self._last_request_time_by_domain: dict[str, float] = {}
        self._robots_cache: dict[str, robotparser.RobotFileParser] = {}

    # ------------------------------------------------------------------
    # Compliance: robots.txt + rate limit
    # ------------------------------------------------------------------
    def _get_robots(self, url: str) -> robotparser.RobotFileParser:
        domain = urlparse(url).netloc
        if domain not in self._robots_cache:
            rp = robotparser.RobotFileParser()
            robots_url = f"{urlparse(url).scheme}://{domain}/robots.txt"
            try:
                rp.set_url(robots_url)
                rp.read()
            except Exception as exc:  # robots.txt ausente/erro -> assume permissivo, mas loga
                logger.warning("Não foi possível ler robots.txt de %s (%s). Assumindo permitido.", robots_url, exc)
            self._robots_cache[domain] = rp
        return self._robots_cache[domain]

    def _respect_rate_limit(self, url: str) -> None:
        domain = urlparse(url).netloc
        last = self._last_request_time_by_domain.get(domain)
        if last is not None:
            elapsed = time.monotonic() - last
            wait = MIN_SECONDS_BETWEEN_REQUESTS - elapsed
            if wait > 0:
                time.sleep(wait)
        self._last_request_time_by_domain[domain] = time.monotonic()

    def _check_allowed(self, url: str) -> None:
        rp = self._get_robots(url)
        allowed = True
        try:
            allowed = rp.can_fetch(USER_AGENT, url)
        except Exception:
            allowed = True  # se não conseguiu avaliar, não bloqueia — mas fica logado acima
        if not allowed:
            raise RobotsDisallowedError(f"robots.txt proíbe a coleta de {url}")

    # ------------------------------------------------------------------
    # HTTP GET com retry, nunca POST/submit de formulários
    # ------------------------------------------------------------------
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    def get(self, url: str, timeout: int = 20) -> requests.Response:
        self._check_allowed(url)
        self._respect_rate_limit(url)
        logger.info("GET %s", url)
        response = self._session.get(url, timeout=timeout)
        response.raise_for_status()
        return response

    # ------------------------------------------------------------------
    # Snapshot para auditoria
    # ------------------------------------------------------------------
    def save_snapshot(self, html: str, url: str) -> Path:
        safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", self.competitor_name.lower()).strip("_")
        folder = SNAPSHOT_DIR / safe_name
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = folder / f"{stamp}.html"
        path.write_text(html, encoding="utf-8", errors="ignore")
        return path

    # ------------------------------------------------------------------
    # Ponto de extensão
    # ------------------------------------------------------------------
    def collect(self, url: str, category: str) -> list[PriceObservation]:
        """Fluxo padrão: GET -> snapshot -> parse(). Subclasses normalmente só
        sobrescrevem parse(); só sobrescreva collect() se precisar de um
        fluxo totalmente diferente (ex.: chamada a uma API JSON)."""
        try:
            response = self.get(url)
        except RobotsDisallowedError as exc:
            logger.warning(str(exc))
            return [
                PriceObservation(
                    competitor_name=self.competitor_name,
                    competitor_tier=self.competitor_tier,
                    competitor_city_region=self.competitor_city_region,
                    product_category=category,
                    source_url=url,
                    price_type="unavailable",
                    notes="Bloqueado por robots.txt — não coletado.",
                )
            ]
        except Exception as exc:
            logger.error("Falha ao coletar %s: %s", url, exc)
            return [
                PriceObservation(
                    competitor_name=self.competitor_name,
                    competitor_tier=self.competitor_tier,
                    competitor_city_region=self.competitor_city_region,
                    product_category=category,
                    source_url=url,
                    price_type="unavailable",
                    notes=f"Erro de coleta: {exc}",
                )
            ]

        self.save_snapshot(response.text, url)
        return self.parse(response.text, url, category)

    def parse(self, html: str, url: str, category: str) -> list[PriceObservation]:
        raise NotImplementedError("Subclasses devem implementar parse()")
