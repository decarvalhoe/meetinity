"""In-memory search backend used for tests and local development."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass
class _StoredDocument:
    id: str
    body: Mapping[str, Any]


class InMemorySearchClient:
    def __init__(self) -> None:
        self._indices: dict[str, dict[str, _StoredDocument]] = defaultdict(dict)

    def ensure_index(self, name: str, *, mappings: Mapping[str, Any], settings: Mapping[str, Any]) -> None:
        self._indices.setdefault(name, {})

    def put_lifecycle(self, name: str, policy: Mapping[str, Any]) -> None:  # pragma: no cover - noop
        return None

    def delete_index(self, name: str) -> None:
        self._indices.pop(name, None)

    def bulk_index(self, index: str, documents: Iterable[Mapping[str, Any]]) -> None:
        store = self._indices.setdefault(index, {})
        for doc in documents:
            doc_id = str(doc.get("id") or len(store) + 1)
            store[doc_id] = _StoredDocument(id=doc_id, body=dict(doc))

    def search(self, index: str, query: Mapping[str, Any], *, size: int = 10, from_: int = 0) -> Mapping[str, Any]:
        store = self._indices.get(index, {})
        hits: list[dict[str, Any]] = []
        q = str(query.get("multi_match", {}).get("query") or "").lower()
        if not q:
            hits = [
                {"_id": doc.id, "_score": 1.0, "_source": doc.body}
                for doc in list(store.values())[from_: from_ + size]
            ]
        else:
            for doc in store.values():
                joined = " ".join(str(value).lower() for value in doc.body.values())
                if q in joined:
                    hits.append({"_id": doc.id, "_score": 1.0, "_source": doc.body})
        total = len(hits)
        hits = hits[from_: from_ + size]
        return {"hits": {"hits": hits, "total": {"value": total}}}

    def info(self) -> Mapping[str, Any]:
        return {"cluster_name": "in-memory", "version": {"number": "0.0.0"}}


__all__ = ["InMemorySearchClient"]
