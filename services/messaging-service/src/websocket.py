"""WebSocket utilities for the messaging service."""
from __future__ import annotations

from typing import Any

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room


socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")


def init_socketio(app) -> None:
    """Attach the global ``SocketIO`` instance to *app*."""

    socketio.init_app(app, cors_allowed_origins="*")


def _conversation_room(conversation_id: int) -> str:
    return f"conversation:{conversation_id}"


@socketio.on("join_conversation")
def join_conversation_event(data: dict[str, Any]) -> None:
    conversation_id = data.get("conversation_id")
    if not isinstance(conversation_id, int):
        emit(
            "conversation.error",
            {"error": "conversation_id must be provided as an integer."},
            room=request.sid,
        )
        return

    join_room(_conversation_room(conversation_id))
    emit("conversation.joined", {"conversation_id": conversation_id}, room=request.sid)


@socketio.on("leave_conversation")
def leave_conversation_event(data: dict[str, Any]) -> None:
    conversation_id = data.get("conversation_id")
    if not isinstance(conversation_id, int):
        emit(
            "conversation.error",
            {"error": "conversation_id must be provided as an integer."},
            room=request.sid,
        )
        return

    leave_room(_conversation_room(conversation_id))
    emit("conversation.left", {"conversation_id": conversation_id}, room=request.sid)


def broadcast_message_created(payload: dict[str, Any]) -> None:
    """Emit a message creation event to conversation subscribers."""

    conversation_id = payload.get("conversation_id")
    if not isinstance(conversation_id, int):
        return
    socketio.emit("message.created", payload, room=_conversation_room(conversation_id))

