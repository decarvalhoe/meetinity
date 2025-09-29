"""Default pipeline registry for the search service."""
from __future__ import annotations

from typing import Iterable, Mapping, MutableMapping

from src.pipelines.base import IngestionPipeline


class PipelineRegistry:
    """Keeps track of enabled ingestion pipelines."""

    def __init__(self) -> None:
        self._pipelines: MutableMapping[str, IngestionPipeline] = {}

    def register(self, pipeline: IngestionPipeline) -> None:
        self._pipelines[pipeline.name] = pipeline

    def get(self, name: str) -> IngestionPipeline:
        try:
            return self._pipelines[name]
        except KeyError as exc:  # pragma: no cover - handled by FastAPI
            raise KeyError(f"Pipeline '{name}' not found") from exc

    def all(self) -> Iterable[IngestionPipeline]:
        return self._pipelines.values()


class EventPipeline(IngestionPipeline):
    def __init__(self) -> None:
        super().__init__(name="events", index_name="meetinity-events")

    @property
    def mappings(self) -> Mapping[str, object]:
        return {
            "properties": {
                "id": {"type": "keyword"},
                "title": {"type": "text", "analyzer": "rebuilt_french"},
                "description": {"type": "text", "analyzer": "rebuilt_french"},
                "location": {"type": "keyword"},
                "start_at": {"type": "date"},
                "end_at": {"type": "date"},
                "tags": {"type": "keyword"},
            }
        }

    def transform_document(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        return {
            "id": payload.get("id"),
            "title": payload.get("title"),
            "description": payload.get("description"),
            "location": payload.get("location"),
            "start_at": payload.get("start_at"),
            "end_at": payload.get("end_at"),
            "tags": payload.get("tags", []),
        }


class ProfilePipeline(IngestionPipeline):
    def __init__(self) -> None:
        super().__init__(name="profiles", index_name="meetinity-profiles")

    @property
    def mappings(self) -> Mapping[str, object]:
        return {
            "properties": {
                "id": {"type": "keyword"},
                "full_name": {"type": "text", "analyzer": "rebuilt_french"},
                "bio": {"type": "text", "analyzer": "rebuilt_french"},
                "headline": {"type": "text", "analyzer": "rebuilt_french"},
                "skills": {"type": "keyword"},
                "company": {"type": "keyword"},
            }
        }

    def transform_document(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        return {
            "id": payload.get("id"),
            "full_name": payload.get("full_name") or payload.get("name"),
            "bio": payload.get("bio"),
            "headline": payload.get("headline") or payload.get("title"),
            "skills": payload.get("skills", []),
            "company": payload.get("company"),
        }


def create_default_registry() -> PipelineRegistry:
    registry = PipelineRegistry()
    registry.register(EventPipeline())
    registry.register(ProfilePipeline())
    return registry


__all__ = [
    "PipelineRegistry",
    "EventPipeline",
    "ProfilePipeline",
    "create_default_registry",
]
