"""HTTP routes for conversation operations."""
from __future__ import annotations

from uuid import uuid4

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
    if text is not None and not isinstance(text, str):
        return error_response(
            400,
            "Validation échouée.",
            {"text": ["Le message doit être une chaîne de caractères lorsqu'elle est fournie."]},
        )

    attachment_payload = payload.get("attachment")
    if attachment_payload is not None and not isinstance(attachment_payload, dict):
        return error_response(
            400,
            "Validation échouée.",
            {"attachment": ["Les métadonnées de pièce jointe doivent être fournies sous forme d'objet."]},
        )

    service = get_conversation_service()
    try:
        message = service.send_message(
            conversation_id, user_id, text, attachment=attachment_payload
        )
    except ConversationNotFoundError as exc:
        return error_response(404, str(exc))
    except AuthorizationError as exc:
        return error_response(403, str(exc))
    except ValidationError as exc:
        return error_response(400, exc.message, exc.details)

    return jsonify(message), 201


@conversations_bp.post("/conversations/<int:conversation_id>/attachments")
def create_attachment_upload(conversation_id: int):
    try:
        user_id = get_authenticated_user_id(request)
    except AuthenticationError as exc:
        return error_response(401, str(exc))

    if not request.is_json:
        return error_response(415, "Content-Type 'application/json' requis.")

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return error_response(400, "Payload JSON invalide: un objet est requis.")

    file_name = payload.get("file_name")
    if not isinstance(file_name, str) or not file_name:
        return error_response(
            400,
            "Validation échouée.",
            {"file_name": ["Le nom du fichier est requis."]},
        )

    size = payload.get("size")
    try:
        size_value = int(size)
    except (TypeError, ValueError):
        size_value = -1
    if size_value <= 0:
        return error_response(
            400,
            "Validation échouée.",
            {"size": ["La taille du fichier doit être un entier positif."]},
        )

    encryption_key = payload.get("encryption_key")
    if not isinstance(encryption_key, str) or not encryption_key:
        return error_response(
            400,
            "Validation échouée.",
            {"encryption_key": ["La clé de chiffrement est requise."]},
        )

    service = get_conversation_service()
    try:
        service.ensure_participant(conversation_id, user_id)
    except ConversationNotFoundError as exc:
        return error_response(404, str(exc))
    except AuthorizationError as exc:
        return error_response(403, str(exc))

    file_token = uuid4().hex
    file_url = f"https://cdn.meetinity.local/conversations/{conversation_id}/{file_token}/{file_name}"
    upload_url = f"https://uploads.meetinity.local/conversations/{conversation_id}/{file_token}"

    return (
        jsonify(
            {
                "file_url": file_url,
                "upload_url": upload_url,
                "size": size_value,
                "encryption_key": encryption_key,
            }
        ),
        201,
    )


@conversations_bp.get(
    "/conversations/<int:conversation_id>/attachments/<int:message_id>"
)
def download_attachment(conversation_id: int, message_id: int):
    try:
        user_id = get_authenticated_user_id(request)
    except AuthenticationError as exc:
        return error_response(401, str(exc))

    service = get_conversation_service()
    try:
        metadata = service.get_attachment_metadata(conversation_id, user_id, message_id)
    except ConversationNotFoundError as exc:
        return error_response(404, str(exc))
    except AuthorizationError as exc:
        return error_response(403, str(exc))

    return jsonify(metadata)


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
