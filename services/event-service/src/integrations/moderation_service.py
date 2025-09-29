"""HTTP client for the central moderation service."""
from __future__ import annotations

from typing import Any, Mapping

import httpx


class ModerationServiceClient:
    def __init__(self, base_url: str | None):
        self.base_url = base_url.rstrip("/") if base_url else None

    def is_enabled(self) -> bool:
        return bool(self.base_url)

    def check_feedback(self, *, event_id: int, comment: str, metadata: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
        if not self.base_url:
            return None
        response = httpx.post(
            f"{self.base_url}/v1/filters/check",
            json={
                "content": comment,
                "context": {"event_id": event_id, **(metadata or {})},
            },
            timeout=4.0,
        )
        response.raise_for_status()
        return response.json()

    def create_report(
        self,
        *,
        event_id: int,
        feedback_id: int,
        reporter_id: int | None,
        summary: str | None,
        filter_result: Mapping[str, Any] | None,
    ) -> None:
        if not self.base_url:
            return
        payload = {
            "content_type": "event_feedback",
            "content_reference": f"event:{event_id}:feedback:{feedback_id}",
            "reporter_id": reporter_id,
            "summary": summary,
        }
        if filter_result:
            payload["filter_result"] = filter_result
        try:
            httpx.post(f"{self.base_url}/v1/reports", json=payload, timeout=4.0)
        except httpx.HTTPError:
            return


__all__ = ["ModerationServiceClient"]
