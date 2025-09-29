"""Business logic for notification scheduling and delivery tracking."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from ..errors import (
    AuthorizationError,
    NotificationNotFoundError,
    ValidationError,
)
from ..models import Notification, NotificationDelivery, NotificationPreference
from ..queue import InMemoryQueue, NotificationQueue, QueueMessage

ALLOWED_CHANNELS = {"email", "sms", "push", "in_app"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PreferenceService:
    """Manage notification preferences with Redis caching support."""

    def __init__(self, session: Session, cache_client):
        self.session = session
        self.cache = cache_client

    def _cache_key(self, user_id: int) -> str:
        return f"notification-preferences:{user_id}"

    def get_preferences(self, user_id: int) -> dict[str, bool]:
        cached = self.cache.get(self._cache_key(user_id))
        if cached:
            if isinstance(cached, str):
                import json

                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    pass
            elif isinstance(cached, bytes):
                import json

                try:
                    return json.loads(cached.decode("utf-8"))
                except json.JSONDecodeError:
                    pass

        query: Select[NotificationPreference] = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
        rows = self.session.execute(query).scalars().all()
        preferences = {channel: True for channel in ALLOWED_CHANNELS}
        for row in rows:
            preferences[row.channel] = bool(row.enabled)
        self._store_cache(user_id, preferences)
        return preferences

    def update_preferences(self, user_id: int, updates: dict[str, bool]) -> dict[str, bool]:
        if not isinstance(updates, dict):
            raise ValidationError(
                "Payload invalide.", {"preferences": ["Un dictionnaire de préférences est requis."]}
            )

        sanitized: dict[str, bool] = {}
        for channel, enabled in updates.items():
            if channel not in ALLOWED_CHANNELS:
                raise ValidationError(
                    "Canal inconnu.", {"channel": [f"Canal '{channel}' non supporté."]}
                )
            if not isinstance(enabled, bool):
                raise ValidationError(
                    "Valeur invalide.", {channel: ["La préférence doit être un booléen."]}
                )
            sanitized[channel] = enabled

        preferences = self.get_preferences(user_id)

        for channel, enabled in sanitized.items():
            preference = self._get_or_create_preference(user_id, channel)
            preference.enabled = enabled
            preference.updated_at = _utcnow()
            preferences[channel] = enabled

        self.session.commit()
        self._store_cache(user_id, preferences)
        return preferences

    def is_channel_enabled(self, user_id: int, channel: str) -> bool:
        preferences = self.get_preferences(user_id)
        return preferences.get(channel, True)

    def _get_or_create_preference(self, user_id: int, channel: str) -> NotificationPreference:
        query = (
            select(NotificationPreference)
            .where(NotificationPreference.user_id == user_id, NotificationPreference.channel == channel)
            .limit(1)
        )
        result = self.session.execute(query).scalars().first()
        if result is not None:
            return result

        preference = NotificationPreference(user_id=user_id, channel=channel, enabled=True)
        self.session.add(preference)
        self.session.flush()
        return preference

    def _store_cache(self, user_id: int, preferences: dict[str, bool]) -> None:
        import json

        self.cache.set(self._cache_key(user_id), json.dumps(preferences), ex=3600)


class NotificationService:
    """High-level operations for managing notifications."""

    def __init__(
        self,
        session: Session,
        preference_service: PreferenceService,
        queue: NotificationQueue | InMemoryQueue,
    ):
        self.session = session
        self.preferences = preference_service
        self.queue = queue

    def list_notifications(self, user_id: int) -> list[dict[str, object]]:
        query: Select[Notification] = (
            select(Notification)
            .where(Notification.recipient_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
        )
        notifications = self.session.execute(query).scalars().all()
        return [self._serialize_notification(notification) for notification in notifications]

    def schedule_notification(
        self,
        initiator_id: int,
        recipient_id: int,
        channels: Iterable[str],
        template: str,
        payload: dict[str, object] | None = None,
        scheduled_for: datetime | None = None,
    ) -> dict[str, object]:
        if recipient_id <= 0:
            raise ValidationError(
                "Validation échouée.", {"recipient_id": ["Identifiant du destinataire invalide."]}
            )
        if not template or not isinstance(template, str):
            raise ValidationError("Validation échouée.", {"template": ["Le gabarit est requis."]})

        payload = payload or {}
        requested_channels = [channel.strip() for channel in channels if channel and channel.strip()]
        if not requested_channels:
            raise ValidationError(
                "Validation échouée.", {"channels": ["Au moins un canal doit être fourni."]}
            )

        for channel in requested_channels:
            if channel not in ALLOWED_CHANNELS:
                raise ValidationError(
                    "Validation échouée.", {"channels": [f"Canal '{channel}' non supporté."]}
                )

        effective_channels = [
            channel
            for channel in requested_channels
            if self.preferences.is_channel_enabled(recipient_id, channel)
        ]
        if not effective_channels:
            raise ValidationError(
                "Aucun canal disponible.",
                {"channels": ["Toutes les options demandées sont désactivées dans les préférences."]},
            )

        notification = Notification(
            initiator_id=initiator_id,
            recipient_id=recipient_id,
            template=template,
            payload=payload,
            channels=effective_channels,
            scheduled_for=scheduled_for,
            status="scheduled",
        )
        self.session.add(notification)
        self.session.flush()

        deliveries: list[NotificationDelivery] = []
        for channel in effective_channels:
            delivery = NotificationDelivery(
                notification_id=notification.id,
                channel=channel,
                status="queued",
                queued_at=scheduled_for or _utcnow(),
            )
            self.session.add(delivery)
            deliveries.append(delivery)

        self.session.flush()
        self.session.commit()

        for delivery in deliveries:
            self.queue.enqueue(
                QueueMessage(
                    notification_id=notification.id,
                    channel=delivery.channel,
                    payload={
                        "template": template,
                        "payload": payload,
                        "recipient_id": recipient_id,
                        "scheduled_for": scheduled_for.isoformat() if scheduled_for else None,
                    },
                )
            )

        notification.deliveries = deliveries
        return self._serialize_notification(notification)

    def list_deliveries(self, notification_id: int, user_id: int) -> list[dict[str, object]]:
        notification = self._get_notification(notification_id)
        if notification.recipient_id != user_id:
            raise AuthorizationError("Accès refusé.")
        return [self._serialize_delivery(delivery) for delivery in notification.deliveries]

    def record_delivery(
        self,
        notification_id: int,
        user_id: int,
        channel: str,
        status: str,
        detail: str | None = None,
    ) -> dict[str, object]:
        notification = self._get_notification(notification_id)
        if notification.recipient_id != user_id:
            raise AuthorizationError("Accès refusé.")

        delivery = next((d for d in notification.deliveries if d.channel == channel), None)
        if delivery is None:
            raise ValidationError(
                "Canal inconnu.", {"channel": [f"Le canal '{channel}' n'est pas associé à la notification."]}
            )

        delivery.status = status
        delivery.detail = detail
        delivery.updated_at = _utcnow()
        notification.updated_at = delivery.updated_at
        notification.status = self._derive_notification_status(notification)
        self.session.commit()
        return self._serialize_delivery(delivery)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_notification(self, notification_id: int) -> Notification:
        query = (
            select(Notification)
            .where(Notification.id == notification_id)
            .limit(1)
        )
        notification = self.session.execute(query).scalars().first()
        if notification is None:
            raise NotificationNotFoundError("Notification introuvable.")
        # eager load deliveries
        notification.deliveries  # access relationship
        return notification

    def _derive_notification_status(self, notification: Notification) -> str:
        statuses = {delivery.status for delivery in notification.deliveries}
        if not statuses:
            return notification.status
        if statuses == {"delivered"}:
            return "delivered"
        if "failed" in statuses and "delivered" not in statuses:
            return "failed"
        if "failed" in statuses and "delivered" in statuses:
            return "partial"
        if statuses == {"queued"}:
            return "scheduled"
        return "in_progress"

    def _serialize_notification(self, notification: Notification) -> dict[str, object]:
        return {
            "id": notification.id,
            "recipient_id": notification.recipient_id,
            "template": notification.template,
            "payload": notification.payload,
            "channels": notification.channels,
            "status": notification.status,
            "scheduled_for": notification.scheduled_for.isoformat() if notification.scheduled_for else None,
            "created_at": notification.created_at.isoformat().replace("+00:00", "Z"),
            "deliveries": [self._serialize_delivery(delivery) for delivery in notification.deliveries],
        }

    def _serialize_delivery(self, delivery: NotificationDelivery) -> dict[str, object]:
        return {
            "channel": delivery.channel,
            "status": delivery.status,
            "detail": delivery.detail,
            "queued_at": delivery.queued_at.isoformat().replace("+00:00", "Z"),
            "updated_at": delivery.updated_at.isoformat().replace("+00:00", "Z"),
        }
