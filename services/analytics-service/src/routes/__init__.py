"""Route registration helpers."""
from __future__ import annotations

from flask import Blueprint, Flask

from .ingestion import ingestion_bp
from .metadata import metadata_bp
from .reporting import reporting_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(ingestion_bp, url_prefix="/ingest")
    app.register_blueprint(reporting_bp, url_prefix="/reports")
    app.register_blueprint(metadata_bp, url_prefix="/metadata")
