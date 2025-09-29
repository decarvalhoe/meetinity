"""Redis cache helpers for notification preferences."""
from __future__ import annotations

import os
from typing import Optional

from flask import current_app

try:
    import redis
except ImportError:  # pragma: no cover - fallback for environments without redis client
    redis = None  # type: ignore


_redis_client: Optional["redis.Redis"] = None


def init_redis(url: str | None = None) -> "redis.Redis":
    if redis is None:
        raise RuntimeError("redis-py is required to use the Redis cache backend")
    client = redis.Redis.from_url(url or _build_redis_url(), decode_responses=True)
    global _redis_client
    _redis_client = client
    return client


def get_redis_client() -> "redis.Redis":
    override = current_app.config.get("REDIS_CLIENT")
    if override is not None:
        return override

    global _redis_client
    if _redis_client is None:
        _redis_client = init_redis(current_app.config.get("REDIS_URL"))
    return _redis_client


def _build_redis_url() -> str:
    host = os.getenv("REDIS_HOST", "redis")
    port = os.getenv("REDIS_PORT", "6379")
    db = os.getenv("REDIS_DB", "0")
    password = os.getenv("REDIS_PASSWORD", "")
    if password:
        return f"redis://:{password}@{host}:{port}/{db}"
    return f"redis://{host}:{port}/{db}"
