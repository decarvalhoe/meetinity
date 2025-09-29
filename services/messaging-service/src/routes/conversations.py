"""HTTP routes for conversation operations."""
from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

from ..auth import get_authenticated_user_id
from ..dependencies import get_conversation_service
from ..errors import (
    AuthenticationError,
    AuthorizationError,
    ConversationExistsError,
    ConversationNotFoundError,
    ValidationError,
)
from ..http import error_response

conversations_bp = Blueprint("conversations", __name__)


@conversations_bp.get("/conversations")
def list_conversations() -> Response:
    try:
        user_id = get_authenticated_user_id(request)
    except AuthenticationError as exc:
        return error_response(401, str(exc))

    service = get_conversation_service()
    conversations = service.list_conversations(user_id)
    return jsonify({"conversations": conversations})


@conversations_bp.post("/conversations")
def create_conversation() -> tuple[Response, int]:
    try:
        user_id = get_authenticated_user_id(request)
    except AuthenticationError as exc:
        return error_response(401, str(exc))

    if not request.is_json:
        return error_response(415, "Content-Type 'application/json' requis.")

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return error_response(400, "Payload JSON invalide: un objet est requis.")

    participant_raw = payload.get("participant_id")
    try:
        participant_id = int(participant_raw)
    except (TypeError, ValueError):
        return error_response(
            400,
            "Validation échouée.",
            {"participant_id": ["Identifiant du participant invalide."]},
        )

    initial_message = payload.get("initial_message")
    if initial_message is not None and not isinstance(initial_message, str):
        return error_response(
            400,
            "Validation échouée.",
            {"initial_message": ["Le message initial doit être une chaîne de caractères."]},
        )

    service = get_conversation_service()
    try:
        conversation = service.create_conversation(
            user_id, participant_id, initial_message=initial_message
        )
    except ValidationError as exc:
        return error_response(400, exc.message, exc.details)
    except ConversationExistsError as exc:
        return error_response(400, str(exc))

    return jsonify(conversation), 201


@conversations_bp.get("/conversations/<int:conversation_id>/messages")
def list_messages(conversation_id: int) -> Response | tuple[Response, int]:
    try:
        user_id = get_authenticated_user_id(request)
    except AuthenticationError as exc:
        return error_response(401, str(exc))

    service = get_conversation_service()
    try:
        messages = service.get_messages(conversation_id, user_id)
    except ConversationNotFoundError as exc:
        return error_response(404, str(exc))
    except AuthorizationError as exc:
        return error_response(403, str(exc))

    return jsonify({"messages": messages})


@conversations_bp.post("/conversations/<int:conversation_id>/messages")
def post_message(conversation_id: int) -> tuple[Response, int]:
    try:
        user_id = get_authenticated_user_id(request)
    except AuthenticationError as exc:
        return error_response(401, str(exc))

    if not request.is_json:
        return error_response(415, "Content-Type 'application/json' requis.")

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return error_response(400, "Payload JSON invalide: un objet est requis.")

    text = payload.get("text")
    if not isinstance(text, str):
        return error_response(
            400,
            "Validation échouée.",
            {"text": ["Le message doit être une chaîne de caractères."]},
        )

    service = get_conversation_service()
    try:
        message = service.send_message(conversation_id, user_id, text)
    except ConversationNotFoundError as exc:
        return error_response(404, str(exc))
    except AuthorizationError as exc:
        return error_response(403, str(exc))
    except ValidationError as exc:
        return error_response(400, exc.message, exc.details)

    return jsonify(message), 201


@conversations_bp.post("/conversations/<int:conversation_id>/read")
def mark_read(conversation_id: int):
    try:
        user_id = get_authenticated_user_id(request)
    except AuthenticationError as exc:
        return error_response(401, str(exc))

    service = get_conversation_service()
    try:
        service.mark_read(conversation_id, user_id)
    except ConversationNotFoundError as exc:
        return error_response(404, str(exc))
    except AuthorizationError as exc:
        return error_response(403, str(exc))

    return Response(status=204)
