"""Notification service application factory."""
from __future__ import annotations

import os

from flask import Flask

from .database import Base, get_engine, init_engine
from .dependencies import cleanup_services
from .http import error_response
from .routes import notifications_bp


def create_app(config: dict[str, object] | None = None) -> Flask:
    app = Flask(__name__)

    default_config = {
        "DATABASE_URL": os.getenv("DATABASE_URL", ""),
        "REDIS_URL": os.getenv("REDIS_URL", "redis://redis:6379/0"),
        "KAFKA_BOOTSTRAP_SERVERS": os.getenv("KAFKA_BOOTSTRAP_SERVERS", ""),
        "KAFKA_NOTIFICATION_TOPIC": os.getenv("KAFKA_NOTIFICATION_TOPIC", "notifications.dispatch"),
        "KAFKA_SCHEMA_REGISTRY_URL": os.getenv("KAFKA_SCHEMA_REGISTRY_URL", ""),
        "KAFKA_SECURITY_PROTOCOL": os.getenv("KAFKA_SECURITY_PROTOCOL", ""),
        "KAFKA_SASL_MECHANISM": os.getenv("KAFKA_SASL_MECHANISM", ""),
        "KAFKA_SASL_USERNAME": os.getenv("KAFKA_SASL_USERNAME", ""),
        "KAFKA_SASL_PASSWORD": os.getenv("KAFKA_SASL_PASSWORD", ""),
        "KAFKA_DLQ_TOPIC": os.getenv("KAFKA_DLQ_TOPIC", "notifications.dispatch.dlq"),
    }
    app.config.from_mapping(default_config)
    if config:
        app.config.update(config)

    database_url = app.config.get("DATABASE_URL") or None
    init_engine(database_url)
    Base.metadata.create_all(get_engine())

    app.register_blueprint(notifications_bp)
    app.teardown_appcontext(cleanup_services)
    register_error_handlers(app)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "notification-service"}

    return app


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def handle_404(_):
        return error_response(404, "Ressource introuvable.")

    @app.errorhandler(405)
    def handle_405(_):
        return error_response(405, "Méthode non autorisée pour cette ressource.")

    @app.errorhandler(500)
    def handle_500(_):
        return error_response(500, "Erreur interne. Veuillez réessayer plus tard.")


app = create_app()
