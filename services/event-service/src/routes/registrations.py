"""Routes that expose the registration and attendance workflows."""
from __future__ import annotations

from typing import Any, Optional

from flask import Blueprint, jsonify, request

from src.routes.dependencies import get_registration_service
from src.routes.utils import error_response
from src.services.registrations import (
    CheckInError,
    DuplicateRegistrationError,
    PenaltyActiveError,
    RegistrationClosedError,
)

registrations_bp = Blueprint("registrations", __name__)


@registrations_bp.post("/events/<int:event_id>/join")
def join_event(event_id: int):
    """Register an attendee for an event."""

    if not request.is_json:
        return error_response(415, "Content-Type 'application/json' requis.")

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return error_response(
            400,
            "Payload JSON invalide: un objet JSON (type dict) est requis.",
        )

    email = payload.get("email")
    if not isinstance(email, str) or not email.strip():
        return error_response(422, "Validation échouée.", {"email": ["Adresse requise."]})

    full_name = payload.get("name")
    if not isinstance(full_name, str):
        full_name = None

    metadata: Optional[dict[str, Any]] = payload.get("metadata")
    if not isinstance(metadata, dict):
        metadata = None

    service = get_registration_service()
    try:
        result = service.register_attendee(
            event_id,
            email=email,
            full_name=full_name,
            metadata=metadata,
        )
    except LookupError:
        return error_response(404, "Événement introuvable.")
    except RegistrationClosedError as exc:
        return error_response(403, str(exc))
    except DuplicateRegistrationError as exc:
        return error_response(409, str(exc))
    except PenaltyActiveError as exc:
        return error_response(403, str(exc))

    status = result.get("status")
    if status == "confirmed":
        registration = result.get("registration", {})
        payload = {
            "success": True,
            "status": "confirmed",
            "registration_id": registration.get("id"),
            "registration": registration,
        }
        return jsonify(payload)

    waitlist_entry = result.get("waitlist_entry", {})
    payload = {
        "success": False,
        "status": "waitlisted",
        "waitlist_entry": waitlist_entry,
    }
    return jsonify(payload), 202


@registrations_bp.delete("/events/<int:event_id>/join")
def cancel_join(event_id: int):
    """Cancel an existing registration for the authenticated attendee."""

    registration_id = request.args.get("registration_id")
    if registration_id is None and request.is_json:
        payload = request.get_json(silent=True) or {}
        if isinstance(payload, dict):
            registration_id = payload.get("registration_id")

    try:
        registration_identifier = int(registration_id)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return error_response(
            422,
            "Validation échouée.",
            {"registration_id": ["Identifiant d'inscription requis."]},
        )

    service = get_registration_service()
    try:
        result = service.cancel_registration(event_id, registration_identifier)
    except LookupError:
        return error_response(404, "Inscription introuvable.")

    payload = {
        "success": True,
        "status": result.get("status", "cancelled"),
    }
    if promoted := result.get("promoted"):
        payload["promoted"] = promoted
    return jsonify(payload)


@registrations_bp.get("/events/<int:event_id>/registrations")
def list_registrations(event_id: int):
    service = get_registration_service()
    try:
        registrations = service.list_registrations(event_id)
    except LookupError:
        return error_response(404, "Événement introuvable.")
    return jsonify({"registrations": registrations})


@registrations_bp.get("/events/<int:event_id>/waitlist")
def list_waitlist(event_id: int):
    service = get_registration_service()
    try:
        waitlist = service.list_waitlist(event_id)
    except LookupError:
        return error_response(404, "Événement introuvable.")
    return jsonify({"waitlist": waitlist})


@registrations_bp.post("/events/<int:event_id>/waitlist/promote")
def promote_waitlist(event_id: int):
    service = get_registration_service()
    try:
        promoted = service.trigger_waitlist_promotion(event_id)
    except LookupError:
        return error_response(404, "Événement introuvable.")
    return jsonify({"promoted": promoted})


@registrations_bp.get("/events/<int:event_id>/attendance")
def list_attendance(event_id: int):
    service = get_registration_service()
    try:
        attendance = service.list_attendance(event_id)
    except LookupError:
        return error_response(404, "Événement introuvable.")
    return jsonify({"attendance": attendance})


@registrations_bp.post("/events/<int:event_id>/attendance")
def detect_no_shows(event_id: int):
    service = get_registration_service()
    try:
        result = service.detect_no_shows(event_id)
    except LookupError:
        return error_response(404, "Événement introuvable.")
    return jsonify(result)


@registrations_bp.post("/check-in/<token>")
def check_in(token: str):
    service = get_registration_service()

    method = "qr"
    metadata: Optional[dict[str, Any]] = None
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        if isinstance(payload, dict):
            metadata_payload = payload.get("metadata")
            if isinstance(metadata_payload, dict):
                metadata = metadata_payload
            method_value = payload.get("method")
            if isinstance(method_value, str) and method_value.strip():
                method = method_value.strip()

    try:
        attendance = service.check_in_attendee(token, method=method, metadata=metadata)
    except CheckInError as exc:
        return error_response(400, str(exc))
    except LookupError:
        return error_response(404, "Événement introuvable.")

    return jsonify({"message": "Check-in enregistré", "attendance": attendance})
