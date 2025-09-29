"""Configuration helpers for the analytics service."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import os
from typing import Any


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration resolved from environment variables."""

    database_url: str
    warehouse_url: str | None
    ingestion_topic: str
    warehouse_rollup_minutes: int
    retention_days: int
    enable_metrics: bool = True

    @property
    def rollup_interval(self) -> timedelta:
        return timedelta(minutes=self.warehouse_rollup_minutes)


def _env(key: str, default: str | None = None) -> str | None:
    value = os.getenv(key)
    if value is None or value == "":
        return default
    return value


def _parse_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def load_config(overrides: dict[str, Any] | None = None) -> AppConfig:
    """Load configuration from environment variables and optional overrides."""

    overrides = overrides or {}
    database_url = str(overrides.get("DATABASE_URL") or _env("DATABASE_URL") or "sqlite:///./analytics.db")
    warehouse_url = overrides.get("WAREHOUSE_URL") or _env("WAREHOUSE_URL")
    ingestion_topic = str(overrides.get("INGESTION_TOPIC") or _env("INGESTION_TOPIC") or "analytics.events")
    rollup_minutes_raw = overrides.get("WAREHOUSE_ROLLUP_MINUTES") or _env("WAREHOUSE_ROLLUP_MINUTES", "60") or 60
    retention_days_raw = overrides.get("EVENT_RETENTION_DAYS") or _env("EVENT_RETENTION_DAYS", "90") or 90
    rollup_minutes = int(rollup_minutes_raw)
    retention_days = int(retention_days_raw)
    enable_metrics = _parse_bool(overrides.get("ENABLE_METRICS", _env("ENABLE_METRICS")))

    return AppConfig(
        database_url=database_url,
        warehouse_url=str(warehouse_url) if warehouse_url else None,
        ingestion_topic=ingestion_topic,
        warehouse_rollup_minutes=rollup_minutes,
        retention_days=retention_days,
        enable_metrics=enable_metrics,
    )
