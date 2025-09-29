"""Application entry point for the Search Service."""
from __future__ import annotations

from fastapi import Depends, FastAPI, Response, status

from src.dependencies import get_pipeline_service
from src.routes.graphql import build_graphql_router
from src.routes.rest import router as rest_router


def create_app() -> FastAPI:
    app = FastAPI(title="Meetinity Search Service", version="1.0.0")

    @app.get("/health")
    async def health(
        service = Depends(get_pipeline_service),
    ) -> dict[str, str | bool]:
        backend_info = getattr(service.client, "info", lambda: {"cluster_name": "unknown"})
        info = backend_info()
        return {
            "status": "ok",
            "service": "search-service",
            "backend": info.get("cluster_name", "unknown"),
        }

    app.include_router(rest_router, prefix="/api")
    app.include_router(build_graphql_router(), prefix="/graphql")

    @app.get("/")
    async def root() -> Response:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()


__all__ = ["app", "create_app"]
