"""Optional machine learning integrations for moderation scoring."""
from __future__ import annotations

from typing import Any, Mapping

import httpx


class ModerationMLClient:
    """Simple HTTP client calling an external classifier if configured."""

    def __init__(self, base_url: str | None) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None

    def is_enabled(self) -> bool:
        return self.base_url is not None

    def score(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not self.base_url:
            raise RuntimeError("ML classifier URL not configured")

        response = httpx.post(f"{self.base_url}/score", json=payload, timeout=5.0)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):  # pragma: no cover - defensive
            raise ValueError("Invalid classifier response")
        return data


__all__ = ["ModerationMLClient"]
