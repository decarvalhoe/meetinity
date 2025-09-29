"""Abstractions over the Elasticsearch/OpenSearch client."""
from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from elasticsearch import Elasticsearch, NotFoundError


class SearchBackendError(RuntimeError):
    """Raised when the underlying search backend is unavailable."""


class SearchClient(AbstractContextManager["SearchClient"]):
    """Wrapper around the official Elasticsearch client with safe defaults."""

    def __init__(
        self,
        hosts: Iterable[str],
        *,
        username: str | None = None,
        password: str | None = None,
        verify_certs: bool = True,
        timeout: int = 10,
    ) -> None:
        kwargs: dict[str, Any] = {
            "hosts": list(hosts),
            "verify_certs": verify_certs,
            "request_timeout": timeout,
        }
        if username:
            kwargs["basic_auth"] = (username, password or "")
        self._client = Elasticsearch(**kwargs)

    def close(self) -> None:
        self._client.close()

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()
        return None

    # Index management -----------------------------------------------------
    def ensure_index(self, name: str, *, mappings: Mapping[str, Any], settings: Mapping[str, Any]) -> None:
        if self._client.indices.exists(index=name):
            return
        self._client.indices.create(index=name, mappings=mappings, settings=settings)

    def put_lifecycle(self, name: str, policy: Mapping[str, Any]) -> None:
        try:
            self._client.ilm.put_lifecycle(policy=name, body=policy)
        except Exception as exc:  # pragma: no cover - pass-through for unsupported clusters
            raise SearchBackendError(str(exc)) from exc

    def delete_index(self, name: str) -> None:
        try:
            self._client.indices.delete(index=name)
        except NotFoundError:
            return

    # Documents ------------------------------------------------------------
    def bulk_index(self, index: str, documents: Iterable[Mapping[str, Any]]) -> None:
        actions = []
        for doc in documents:
            action: dict[str, Any] = {"index": {"_index": index}}
            if "id" in doc:
                action["index"]["_id"] = doc["id"]
            actions.append(action)
            actions.append(doc)
        if not actions:
            return
        self._client.bulk(operations=actions, refresh="wait_for")

    def search(self, index: str, query: Mapping[str, Any], *, size: int = 10, from_: int = 0) -> Mapping[str, Any]:
        return self._client.search(index=index, query=query, size=size, from_=from_)

    def info(self) -> Mapping[str, Any]:
        return self._client.info()


@dataclass
class SearchDocument:
    id: str
    score: float
    source: Mapping[str, Any]


def hits_to_documents(payload: Mapping[str, Any]) -> list[SearchDocument]:
    hits = payload.get("hits", {}).get("hits", [])
    documents: list[SearchDocument] = []
    for hit in hits:
        documents.append(
            SearchDocument(
                id=str(hit.get("_id")),
                score=float(hit.get("_score") or 0.0),
                source=hit.get("_source", {}),
            )
        )
    return documents


__all__ = ["SearchBackendError", "SearchClient", "SearchDocument", "hits_to_documents"]
