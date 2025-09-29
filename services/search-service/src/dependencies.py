"""FastAPI dependency wiring."""
from __future__ import annotations

from typing import Any

from fastapi import Depends

from src.config import SearchSettings, get_settings
from src.pipelines.registry import create_default_registry
from src.search.client import SearchClient
from src.search.memory import InMemorySearchClient
from src.services import PipelineService


_CLIENT_CACHE: dict[tuple[Any, ...], Any] = {}


def _search_client(settings: SearchSettings) -> Any:
    key = (
        tuple(settings.hosts()),
        settings.username,
        settings.password,
        settings.verify_certs,
        settings.timeout,
        settings.use_in_memory_backend,
    )
    if key in _CLIENT_CACHE:
        return _CLIENT_CACHE[key]
    if settings.use_in_memory_backend:
        client = InMemorySearchClient()
    else:
        client = SearchClient(
            hosts=settings.hosts(),
            username=settings.username,
            password=settings.password,
            verify_certs=settings.verify_certs,
            timeout=settings.timeout,
        )
    _CLIENT_CACHE[key] = client
    return client


def get_pipeline_service(
    settings: SearchSettings = Depends(get_settings),
) -> PipelineService:
    client = _search_client(settings)
    return PipelineService(client=client, registry=create_default_registry())


__all__ = ["get_pipeline_service"]
