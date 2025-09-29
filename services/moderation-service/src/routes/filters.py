"""Endpoints powering automated moderation filters."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from ..config import ModerationConfig
from ..redis_client import create_redis_client
from ..services.filters import AutomatedFilterEngine
from ..clients.ml import ModerationMLClient

filters_bp = Blueprint("filters", __name__)


@filters_bp.post("/check")
def run_filters():
    payload = request.get_json(silent=True) or {}
    text = payload.get("content")
    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Contenu manquant."}), 400

    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}

    app = current_app
    config = ModerationConfig.from_app(app)
    redis_client = create_redis_client(config.redis_url)
    filter_engine = AutomatedFilterEngine(
        config=config,
        redis_client=redis_client,
        ml_client=ModerationMLClient(config.ml_classifier_url),
    )
    result = filter_engine.evaluate(text, context)
    return jsonify(result.to_dict()), 200
