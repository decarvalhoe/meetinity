"""Messaging service application factory."""
from __future__ import annotations

import os

from flask import Flask

from .database import Base, get_engine, init_engine
from .dependencies import cleanup_services
from .http import error_response
from .routes.conversations import conversations_bp


def create_app(config: dict[str, object] | None = None) -> Flask:
    app = Flask(__name__)

    default_config = {
        "DATABASE_URL": os.getenv("DATABASE_URL", ""),
    }
    app.config.from_mapping(default_config)
    if config:
        app.config.update(config)

    database_url = app.config.get("DATABASE_URL") or None
    init_engine(database_url)
    Base.metadata.create_all(get_engine())

    app.register_blueprint(conversations_bp)
    app.teardown_appcontext(cleanup_services)
    register_error_handlers(app)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "messaging-service"}

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
