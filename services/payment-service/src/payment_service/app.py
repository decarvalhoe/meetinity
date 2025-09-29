"""FastAPI application factory."""
from __future__ import annotations

from fastapi import FastAPI

from .config import get_settings
from .routes import health, payments, subscriptions


def create_app() -> FastAPI:
    """Create the FastAPI application."""

    settings = get_settings()
    app = FastAPI(title="Meetinity Payment Service", version="0.1.0")
    app.state.settings = settings
    app.include_router(health.router)
    app.include_router(subscriptions.router)
    app.include_router(payments.router)
    return app


app = create_app()


__all__ = ["app", "create_app"]

