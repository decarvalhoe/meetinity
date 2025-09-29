"""Blueprint registration for the moderation service."""
from __future__ import annotations

from flask import Blueprint

from .admin import admin_bp
from .filters import filters_bp
from .reports import reports_bp


api_bp = Blueprint("moderation_api", __name__)
api_bp.register_blueprint(filters_bp, url_prefix="/filters")
api_bp.register_blueprint(reports_bp, url_prefix="/reports")
api_bp.register_blueprint(admin_bp, url_prefix="/admin")

__all__ = ["api_bp"]
