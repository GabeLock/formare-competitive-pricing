from __future__ import annotations

import threading
import time
import urllib.robotparser as robotparser
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from src.config.settings import DEFAULT_TIMEOUT_SECONDS, MIN_SECONDS_BETWEEN_DOMAIN_REQUESTS, RAW_DIR
from src.processing.price_parser import PriceObservationIn
from src.utils.helpers import slugify
from src.utils.logger import logger
from src.utils.user_agent import get_user_agent

_DOMAIN_LOCK = threading.Lock()
_LAST_REQUEST_BY_DOMAIN: dict[str, float] = {}
_ROBOTS_CACHE: dict[str, robotparser.RobotFileParser] = {}


class RobotsBlockedError(Exception):
    pass


class ActiveProtectionError(Exception):
    pass


@dataclass(frozen=True)
class SourceContext:
    competitor_id: str
    competitor_name: str
    tier: str
    region: str | None
    product_id: str
    category: str | None
    url: str
    query: str | None
    source_type: str
    customer_segment: str
    collection_method: str


class BaseCollector:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": get_user_agent()})

    def _domain(self, url: str) -> str:
        return urlparse(url).netloc

    def _robots(self, url: str) -> robotparser.RobotFileParser:
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain in _ROBOTS_CACHE:
            return _ROBOTS_CACHE[domain]
        robots_url = f"{parsed.scheme}://{domain}/robots.txt"
        parser = robotparser.RobotFileParser()
        parser.set_url(robots_url)
        try:
            parser.read()
        except Exception as exc:
            logger.warning("robots.txt indisponivel em {}: {}", robots_url, exc)
        _ROBOTS_CACHE[domain] = parser
        return parser

    def assert_allowed(self, url: str) -> None:
        parser = self._robots(url)
        if not parser.can_fetch(get_user_agent(), url):
            raise RobotsBlockedError(f"robots.txt bloqueia {url}")

    def cooldown(self, url: str) -> None:
        domain = self._domain(url)
        with _DOMAIN_LOCK:
            last = _LAST_REQUEST_BY_DOMAIN.get(domain)
            if last is not None:
                elapsed = time.monotonic() - last
                remaining = MIN_SECONDS_BETWEEN_DOMAIN_REQUESTS - elapsed
                if remaining > 0:
                    logger.info("Cooldown de {:.1f}s para {}", remaining, domain)
                    time.sleep(remaining)
            _LAST_REQUEST_BY_DOMAIN[domain] = time.monotonic()

    def get(self, url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> requests.Response:
        self.assert_allowed(url)
        self.cooldown(url)
        response = self.session.get(url, timeout=timeout)
        if response.status_code in {403, 429}:
            retry_after = response.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                time.sleep(min(int(retry_after), 60))
            raise ActiveProtectionError(f"HTTP {response.status_code} em {url}")
        response.raise_for_status()
        return response

    def save_snapshot(self, context: SourceContext, html: str) -> Path:
        folder = RAW_DIR / slugify(context.competitor_id)
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = folder / f"{context.product_id}_{stamp}.html"
        path.write_text(html, encoding="utf-8", errors="ignore")
        return path

    def status_observation(
        self,
        context: SourceContext,
        collection_status: str,
        notes: str,
        source_type: str | None = None,
    ) -> PriceObservationIn:
        return PriceObservationIn(
            competitor_id=context.competitor_id,
            competitor_name=context.competitor_name,
            tier=context.tier,
            product_id=context.product_id,
            category=context.category,
            url=context.url,
            collection_status=collection_status,
            source_type=source_type or context.source_type,
            customer_segment=context.customer_segment,
            notes=notes,
        ).finalized()

    def collect(self, context: SourceContext) -> list[PriceObservationIn]:
        raise NotImplementedError
