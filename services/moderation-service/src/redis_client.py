"""Redis helper utilities with graceful fallbacks for tests."""
from __future__ import annotations

import functools
from typing import Any, Callable

try:  # pragma: no cover - optional dependency
    import redis
except Exception:  # pragma: no cover - fallback for environments without redis client
    redis = None  # type: ignore

try:  # pragma: no cover - optional dependency for tests
    import fakeredis
except Exception:  # pragma: no cover
    fakeredis = None  # type: ignore

RedisFactory = Callable[[str], Any]


@functools.lru_cache(maxsize=4)
def create_redis_client(url: str) -> Any:
    """Return a Redis client or a fake implementation for tests."""

    if url.startswith("fakeredis://"):
        if fakeredis is None:
            raise RuntimeError("fakeredis is not installed but fakeredis:// URL was provided")
        return fakeredis.FakeStrictRedis(decode_responses=True)

    if redis is None:
        raise RuntimeError("redis-py must be installed to use a real Redis backend")

    return redis.from_url(url, decode_responses=True)


__all__ = ["create_redis_client", "RedisFactory"]
