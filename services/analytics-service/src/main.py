"""Application entrypoint for the analytics service."""
from __future__ import annotations

from flask import Flask, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .config import load_config
from .database import dispose_engine, init_engine
from .routes import register_blueprints
from .routes.dependencies import cleanup_services


def create_app(config_overrides: dict[str, object] | None = None) -> Flask:
    config = load_config(config_overrides)
    app = Flask(__name__)
    app.config.update(
        {
            "DATABASE_URL": config.database_url,
            "WAREHOUSE_URL": config.warehouse_url,
            "WAREHOUSE_ROLLUP_MINUTES": config.warehouse_rollup_minutes,
            "EVENT_RETENTION_DAYS": config.retention_days,
            "ENABLE_METRICS": config.enable_metrics,
        }
    )

    init_engine(config.database_url)
    register_blueprints(app)
    app.teardown_appcontext(cleanup_services)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "analytics-service"}

    @app.get("/metrics")
    def metrics() -> Response:
        if not config.enable_metrics:
            return Response("", mimetype=CONTENT_TYPE_LATEST)
        payload = generate_latest()
        return Response(payload, mimetype=CONTENT_TYPE_LATEST)

    return app


def shutdown() -> None:
    dispose_engine()


app = create_app()
