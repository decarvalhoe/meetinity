"""Application factory for the moderation service."""
from __future__ import annotations

import os

from flask import Flask

from .config import ModerationConfig
from .database import Base, get_engine, init_engine
from .redis_client import create_redis_client
from .routes import api_bp


def create_app(config: dict[str, object] | None = None) -> Flask:
    app = Flask(__name__)

    default_config = {
        "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///:memory:"),
        "REDIS_URL": os.getenv("REDIS_URL", "fakeredis://"),
        "KAFKA_BOOTSTRAP_SERVERS": os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        "KAFKA_MODERATION_TOPIC": os.getenv("KAFKA_MODERATION_TOPIC", "moderation.events"),
        "KAFKA_SCHEMA_REGISTRY_URL": os.getenv("KAFKA_SCHEMA_REGISTRY_URL"),
        "KAFKA_SECURITY_PROTOCOL": os.getenv("KAFKA_SECURITY_PROTOCOL"),
        "KAFKA_SASL_MECHANISM": os.getenv("KAFKA_SASL_MECHANISM"),
        "KAFKA_SASL_USERNAME": os.getenv("KAFKA_SASL_USERNAME"),
        "KAFKA_SASL_PASSWORD": os.getenv("KAFKA_SASL_PASSWORD"),
        "KAFKA_DLQ_TOPIC": os.getenv("KAFKA_DLQ_TOPIC", "moderation.events.dlq"),
        "ML_CLASSIFIER_URL": os.getenv("ML_CLASSIFIER_URL"),
        "AUTO_APPROVE_THRESHOLD": float(os.getenv("AUTO_APPROVE_THRESHOLD", 0.55)),
        "AUTO_BLOCK_THRESHOLD": float(os.getenv("AUTO_BLOCK_THRESHOLD", 0.9)),
    }
    app.config.from_mapping(default_config)
    if config:
        app.config.update(config)

    cfg = ModerationConfig.from_app(app)
    init_engine(cfg.database_url)
    Base.metadata.create_all(get_engine())

    # Initialize Redis eagerly to fail fast if configuration is wrong.
    create_redis_client(cfg.redis_url)

    app.register_blueprint(api_bp, url_prefix="/v1")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "moderation-service"}

    return app


app = create_app()

__all__ = ["create_app", "app"]
