"""Service layer for ingestion and querying."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from src.pipelines.base import IngestionPipeline
from src.pipelines.registry import PipelineRegistry, create_default_registry
from src.search.client import SearchDocument, SearchBackendError, hits_to_documents


@dataclass
class SearchResult:
    documents: list[SearchDocument]
    total: int


class PipelineService:
    def __init__(
        self,
        client: Any,
        registry: PipelineRegistry | None = None,
    ) -> None:
        self.client = client
        self.registry = registry or create_default_registry()

    def _ensure_pipeline(self, pipeline: IngestionPipeline) -> None:
        self.client.ensure_index(
            pipeline.index_name,
            mappings=pipeline.mappings,
            settings=pipeline.settings,
        )
        policy = pipeline.lifecycle_policy()
        if policy:
            try:
                self.client.put_lifecycle(f"{pipeline.index_name}-policy", policy["policy"])
            except SearchBackendError:
                # Lifecycle management is best-effort; ignore for unsupported plans.
                pass

    def ingest(self, pipeline_name: str, documents: Sequence[Mapping[str, Any]]) -> int:
        pipeline = self.registry.get(pipeline_name)
        self._ensure_pipeline(pipeline)
        normalised = list(pipeline.prepare_documents(documents))
        self.client.bulk_index(pipeline.index_name, normalised)
        return len(normalised)

    def search(
        self,
        pipeline_name: str,
        query_text: str,
        *,
        from_: int = 0,
        size: int = 10,
    ) -> SearchResult:
        pipeline = self.registry.get(pipeline_name)
        query = {
            "multi_match": {
                "query": query_text,
                "fields": ["*"]
            }
        }
        raw = self.client.search(pipeline.index_name, query=query, size=size, from_=from_)
        documents = hits_to_documents(raw)
        total = int(raw.get("hits", {}).get("total", {}).get("value", len(documents)))
        return SearchResult(documents=documents, total=total)

    def pipelines(self) -> Iterable[IngestionPipeline]:
        return self.registry.all()


__all__ = ["PipelineService", "SearchResult"]
