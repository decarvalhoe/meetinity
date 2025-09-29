"""HTTP endpoints for notification management."""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, Response, jsonify, request

from ..auth import get_authenticated_user_id
from ..dependencies import (
    get_notification_service,
    get_preference_service,
)
from ..errors import (
    AuthenticationError,
    AuthorizationError,
    NotificationNotFoundError,
    ValidationError,
)
from ..http import error_response

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("/notifications")
def list_notifications() -> Response:
    try:
        user_id = get_authenticated_user_id(request)
    except AuthenticationError as exc:
        return error_response(401, str(exc))

    service = get_notification_service()
    notifications = service.list_notifications(user_id)
    return jsonify({"notifications": notifications})


@notifications_bp.post("/notifications")
def create_notification() -> tuple[Response, int]:
    try:
        initiator_id = get_authenticated_user_id(request)
    except AuthenticationError as exc:
        return error_response(401, str(exc))

    if not request.is_json:
        return error_response(415, "Content-Type 'application/json' requis.")

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return error_response(400, "Payload JSON invalide: un objet est requis.")

    recipient_raw = payload.get("recipient_id")
    try:
        recipient_id = int(recipient_raw)
    except (TypeError, ValueError):
        return error_response(
            400,
            "Validation échouée.",
            {"recipient_id": ["Identifiant du destinataire invalide."]},
        )

    channels_raw = payload.get("channels")
    if not isinstance(channels_raw, list):
        return error_response(
            400,
            "Validation échouée.",
            {"channels": ["Une liste de canaux est requise."]},
        )

    template = payload.get("template")
    if not isinstance(template, str) or not template.strip():
        return error_response(
            400,
            "Validation échouée.",
            {"template": ["Le gabarit est requis."]},
        )

    body_payload = payload.get("payload")
    if body_payload is not None and not isinstance(body_payload, dict):
        return error_response(
            400,
            "Validation échouée.",
            {"payload": ["Le payload doit être un objet JSON."]},
        )

    scheduled_for_str = payload.get("scheduled_for")
    scheduled_for: datetime | None = None
    if scheduled_for_str:
        if not isinstance(scheduled_for_str, str):
            return error_response(
                400,
                "Validation échouée.",
                {"scheduled_for": ["La date planifiée doit être une chaîne ISO 8601."]},
            )
        try:
            scheduled_for = datetime.fromisoformat(scheduled_for_str)
        except ValueError:
            return error_response(
                400,
                "Validation échouée.",
                {"scheduled_for": ["Format de date/heure invalide. Utilisez ISO 8601."]},
            )

    service = get_notification_service()
    try:
        notification = service.schedule_notification(
            initiator_id,
            recipient_id,
            channels_raw,
            template.strip(),
            payload=body_payload,
            scheduled_for=scheduled_for,
        )
    except ValidationError as exc:
        return error_response(400, exc.message, exc.details)

    return jsonify(notification), 201


@notifications_bp.get("/notifications/<int:notification_id>/deliveries")
def list_deliveries(notification_id: int):
    try:
        user_id = get_authenticated_user_id(request)
    except AuthenticationError as exc:
        return error_response(401, str(exc))

    service = get_notification_service()
    try:
        deliveries = service.list_deliveries(notification_id, user_id)
    except NotificationNotFoundError as exc:
        return error_response(404, str(exc))
    except AuthorizationError as exc:
        return error_response(403, str(exc))

    return jsonify({"deliveries": deliveries})


@notifications_bp.post("/notifications/<int:notification_id>/deliveries")
def update_delivery(notification_id: int):
    try:
        user_id = get_authenticated_user_id(request)
    except AuthenticationError as exc:
        return error_response(401, str(exc))

    if not request.is_json:
        return error_response(415, "Content-Type 'application/json' requis.")

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return error_response(400, "Payload JSON invalide: un objet est requis.")

    channel = payload.get("channel")
    status = payload.get("status")
    detail = payload.get("detail")

    if not isinstance(channel, str) or not channel:
        return error_response(
            400,
            "Validation échouée.",
            {"channel": ["Le canal est requis."]},
        )
    if not isinstance(status, str) or not status:
        return error_response(
            400,
            "Validation échouée.",
            {"status": ["Le statut est requis."]},
        )
    if detail is not None and not isinstance(detail, str):
        return error_response(
            400,
            "Validation échouée.",
            {"detail": ["Le détail doit être une chaîne."]},
        )

    service = get_notification_service()
    try:
        delivery = service.record_delivery(notification_id, user_id, channel, status, detail)
    except NotificationNotFoundError as exc:
        return error_response(404, str(exc))
    except AuthorizationError as exc:
        return error_response(403, str(exc))
    except ValidationError as exc:
        return error_response(400, exc.message, exc.details)

    return jsonify(delivery)


@notifications_bp.get("/preferences")
def get_preferences():
    try:
        user_id = get_authenticated_user_id(request)
    except AuthenticationError as exc:
        return error_response(401, str(exc))

    service = get_preference_service()
    preferences = service.get_preferences(user_id)
    return jsonify({"preferences": preferences})


@notifications_bp.put("/preferences")
def update_preferences():
    try:
        user_id = get_authenticated_user_id(request)
    except AuthenticationError as exc:
        return error_response(401, str(exc))

    if not request.is_json:
        return error_response(415, "Content-Type 'application/json' requis.")

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return error_response(400, "Payload JSON invalide: un objet est requis.")

    preferences_payload = payload.get("preferences")
    if not isinstance(preferences_payload, dict):
        return error_response(
            400,
            "Validation échouée.",
            {"preferences": ["Un dictionnaire de préférences est requis."]},
        )

    service = get_preference_service()
    try:
        preferences = service.update_preferences(user_id, preferences_payload)
    except ValidationError as exc:
        return error_response(400, exc.message, exc.details)

    return jsonify({"preferences": preferences})
