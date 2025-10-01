"""Client wrapper for the notification service."""
from __future__ import annotations

from typing import Any

import httpx


class NotificationClient:
    """Minimal HTTP client used to publish push notifications."""

    def __init__(self, base_url: str | None, *, timeout: float = 3.0) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self._timeout = timeout

    def is_enabled(self) -> bool:
        return bool(self.base_url)

    def publish_new_message(
        self,
        *,
        conversation_id: int,
        message_id: int,
        sender_id: int,
        recipient_id: int,
        preview_text: str | None,
        attachment: dict[str, Any] | None,
    ) -> None:
        if not self.is_enabled():
            return

        payload = {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "preview_text": preview_text,
            "attachment": attachment,
        }
        try:
            httpx.post(
                f"{self.base_url}/notifications/messages",
                json=payload,
                timeout=self._timeout,
            )
        except httpx.HTTPError:
            # Failures should not break message delivery. Errors are logged
            # upstream where the client is invoked.
            raise

