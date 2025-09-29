"""Health endpoints."""
from __future__ import annotations

from fastapi import APIRouter


router = APIRouter()


@router.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    """Return service readiness."""

    return {"status": "ok"}


__all__ = ["router"]

