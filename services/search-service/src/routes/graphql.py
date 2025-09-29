"""GraphQL schema for search queries."""
from __future__ import annotations

from typing import Any, Mapping

import strawberry
from fastapi import Depends
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info

from src.dependencies import get_pipeline_service
from src.services import PipelineService


@strawberry.type
class SearchDocument:
    id: str
    score: float
    source: strawberry.scalars.JSON


@strawberry.type
class SearchResult:
    pipeline: str
    total: int
    results: list[SearchDocument]


def _to_document(model) -> SearchDocument:
    return SearchDocument(id=model.id, score=model.score, source=model.source)  # type: ignore[arg-type]


@strawberry.type
class Query:
    @strawberry.field
    def search(
        self,
        info: Info,
        pipeline: str,
        query: str,
        size: int = 10,
        offset: int = 0,
    ) -> SearchResult:
        service: PipelineService = info.context["pipeline_service"]
        result = service.search(pipeline, query, size=size, from_=offset)
        return SearchResult(
            pipeline=pipeline,
            total=result.total,
            results=[_to_document(doc) for doc in result.documents],
        )


def get_context(service: PipelineService = Depends(get_pipeline_service)) -> Mapping[str, Any]:
    return {"pipeline_service": service}


def build_graphql_router() -> GraphQLRouter:
    schema = strawberry.Schema(query=Query)
    return GraphQLRouter(schema, context_getter=get_context)


__all__ = ["build_graphql_router"]
