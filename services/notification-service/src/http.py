"""HTTP helper utilities."""
from __future__ import annotations

from flask import Response, jsonify


def error_response(status_code: int, message: str, details: dict[str, list[str]] | None = None) -> tuple[Response, int]:
    payload = {"error": status_code, "message": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status_code
