"""Logging and optional error tracking configuration."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from importlib import import_module
from typing import Any

LOGGER_NAME = "dataset_preflight"
logger = logging.getLogger(LOGGER_NAME)


class ErrorTracker:
    """Small boundary that keeps the service independent of any SaaS tracker."""

    def __init__(self, capture: Callable[[BaseException], None] | None = None) -> None:
        self._capture = capture or (lambda _exc: None)

    def capture_exception(self, exc: BaseException) -> None:
        self._capture(exc)


def configure_logging() -> None:
    """Configure predictable process logging from DATASET_PREFLIGHT_LOG_LEVEL."""

    level_name = os.getenv("DATASET_PREFLIGHT_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger.setLevel(level)


def configure_error_tracking() -> ErrorTracker:
    """Enable Sentry only when an explicit DSN is supplied."""

    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return ErrorTracker()
    try:
        sentry_sdk: Any = import_module("sentry_sdk")
        traces_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0"))
        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("SENTRY_ENVIRONMENT", "local"),
            traces_sample_rate=traces_rate,
        )
        logger.info("optional Sentry error tracking enabled")
        return ErrorTracker(sentry_sdk.capture_exception)
    except (ImportError, ValueError) as exc:
        logger.warning("Sentry error tracking unavailable: %s", exc)
        return ErrorTracker()


__all__ = ["ErrorTracker", "configure_error_tracking", "configure_logging"]
