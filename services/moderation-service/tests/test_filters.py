from __future__ import annotations

def test_filter_blocks_banned_terms(client):
    response = client.post(
        "/v1/filters/check",
        json={"content": "This is a spam message"},
    )
    body = response.get_json()
    assert response.status_code == 200
    assert body["status"] == "blocked"
    assert body["labels"]["heuristics"]["banned_terms"]["spam"] == 1


def test_filter_enforces_rate_limits(app):
    client = app.test_client()
    for _ in range(55):
        response = client.post(
            "/v1/filters/check",
            json={"content": "hello", "context": {"user_id": 42}},
        )
    body = response.get_json()
    assert body["status"] in {"needs_review", "blocked"}
    assert "rate_limit" in body["labels"]["heuristics"]
