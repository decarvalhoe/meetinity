"""REST API endpoints for search and ingestion."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.dependencies import get_pipeline_service
from src.services import PipelineService

router = APIRouter()


class IngestRequest(BaseModel):
    documents: Sequence[Mapping[str, Any]] = Field(default_factory=list)


class IngestResponse(BaseModel):
    pipeline: str
    indexed: int


class SearchDocumentModel(BaseModel):
    id: str
    score: float
    source: Mapping[str, Any]


class SearchResponse(BaseModel):
    pipeline: str
    total: int
    results: list[SearchDocumentModel]


@router.post("/pipelines/{pipeline}/documents", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_documents(
    pipeline: str,
    request: IngestRequest,
    service: PipelineService = Depends(get_pipeline_service),
) -> IngestResponse:
    if not request.documents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'documents' ne peut pas être vide")
    try:
        indexed = service.ingest(pipeline, list(request.documents))
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return IngestResponse(pipeline=pipeline, indexed=indexed)


@router.get("/search", response_model=SearchResponse)
async def search_documents(
    pipeline: str = Query(..., description="Pipeline to target, e.g. events"),
    query: str = Query(..., description="Full-text query"),
    size: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    service: PipelineService = Depends(get_pipeline_service),
) -> SearchResponse:
    try:
        result = service.search(pipeline, query, size=size, from_=offset)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    response_docs = [
        SearchDocumentModel(id=doc.id, score=doc.score, source=doc.source)
        for doc in result.documents
    ]
    return SearchResponse(pipeline=pipeline, total=result.total, results=response_docs)


@router.get("/pipelines")
async def list_pipelines(service: PipelineService = Depends(get_pipeline_service)) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for pipeline in service.pipelines():
        items.append({"name": pipeline.name, "index": pipeline.index_name})
    return items


__all__ = ["router"]
