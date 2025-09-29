"""Simple bearer-token authentication helpers."""
from __future__ import annotations

from flask import Request

from .errors import AuthenticationError


def get_authenticated_user_id(request: Request) -> int:
    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise AuthenticationError("Jeton d'authentification manquant ou invalide.")

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise AuthenticationError("Jeton d'authentification manquant ou invalide.")

    user_id = _extract_user_id(token)
    if user_id is None:
        raise AuthenticationError("Jeton d'authentification manquant ou invalide.")
    return user_id


def _extract_user_id(token: str) -> int | None:
    token = token.strip()
    if not token:
        return None
    if token.isdigit():
        return int(token)

    lowered = token.lower()
    prefixes = ("user:", "user-", "uid:", "uid-")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            candidate = token[len(prefix) :]
            if candidate.isdigit():
                return int(candidate)
            return None

    segments = token.split(":")
    if len(segments) >= 2 and segments[-1].isdigit():
        return int(segments[-1])

    return None
