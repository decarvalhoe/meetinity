"""HTTP client for the moderation service."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(slots=True)
class ModerationResponse:
    status: str
    score: float
    labels: dict[str, Any]


class ModerationClient:
    """Small wrapper calling the moderation service's filter endpoint."""

    def __init__(self, base_url: str | None):
        self.base_url = base_url.rstrip("/") if base_url else None

    def is_enabled(self) -> bool:
        return bool(self.base_url)

    def review_message(self, text: str, **context: Any) -> ModerationResponse | None:
        if not self.base_url:
            return None

        response = httpx.post(
            f"{self.base_url}/v1/filters/check",
            json={"content": text, "context": context},
            timeout=4.0,
        )
        response.raise_for_status()
        payload = response.json()
        return ModerationResponse(
            status=str(payload.get("status", "approved")),
            score=float(payload.get("score", 0.0)),
            labels=dict(payload.get("labels", {})),
        )

    def create_report(self, *, content_reference: str, reporter_id: int | None, summary: str | None) -> None:
        if not self.base_url:
            return
        try:
            httpx.post(
                f"{self.base_url}/v1/reports",
                json={
                    "content_type": "message",
                    "content_reference": content_reference,
                    "reporter_id": reporter_id,
                    "summary": summary,
                },
                timeout=4.0,
            )
        except httpx.HTTPError:
            return


__all__ = ["ModerationClient", "ModerationResponse"]
