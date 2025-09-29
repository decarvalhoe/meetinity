from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from src.main import create_app


def test_ingest_and_search_roundtrip(monkeypatch):
    monkeypatch.setenv("SEARCH_USE_IN_MEMORY", "1")
    # Ensure registry uses predictable indices in tests
    if "SEARCH_NODES" in os.environ:
        monkeypatch.delenv("SEARCH_NODES", raising=False)
    app = create_app()

    client = TestClient(app)

    payload = {
        "documents": [
            {"id": "event-1", "title": "Keynote IA", "description": "Conférence IA"},
            {"id": "event-2", "title": "Networking", "description": "Apéro"},
        ]
    }

    resp = client.post("/api/pipelines/events/documents", json=payload)
    assert resp.status_code == 202, resp.text
    assert resp.json()["indexed"] == 2

    search = client.get("/api/search", params={"pipeline": "events", "query": "IA"})
    assert search.status_code == 200
    data = search.json()
    assert data["total"] >= 1
    assert any("Keynote" in doc["source"].get("title", "") for doc in data["results"])

    graphql = client.post(
        "/graphql",
        json={"query": "{ search(pipeline: \"events\", query: \"Networking\") { total results { id } } }"},
    )
    assert graphql.status_code == 200
    payload = graphql.json()["data"]["search"]
    assert payload["total"] >= 1
    assert any(doc["id"] == "event-2" for doc in payload["results"])
