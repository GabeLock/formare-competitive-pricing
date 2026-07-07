from __future__ import annotations

import sys

from loguru import logger

from src.config.settings import LOG_DIR


def configure_logger() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(
        LOG_DIR / "collection_{time:YYYYMMDD}.log",
        level="INFO",
        rotation="5 MB",
        retention="30 days",
        enqueue=True,
    )


__all__ = ["configure_logger", "logger"]

