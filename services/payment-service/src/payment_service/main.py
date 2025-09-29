"""Entrypoint for running the service with Uvicorn."""
from __future__ import annotations

import uvicorn

from .app import app


def run() -> None:  # pragma: no cover - runtime helper
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":  # pragma: no cover
    run()

