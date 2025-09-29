from __future__ import annotations

def test_create_and_assign_report(client, app):
    response = client.post(
        "/v1/reports",
        json={
            "content_type": "message",
            "content_reference": "msg_123",
            "reporter_id": 7,
            "summary": "Propos offensants",
        },
    )
    assert response.status_code == 201
    case_id = response.get_json()["id"]

    assign_response = client.post(
        f"/v1/reports/{case_id}/assign",
        json={"reviewer": "alice", "actor": "alice"},
    )
    assert assign_response.status_code == 200
    payload = assign_response.get_json()
    assert payload["assigned_reviewer"] == "alice"
    assert payload["status"] == "under_review"

    decision = client.post(
        f"/v1/reports/{case_id}/decision",
        json={"status": "action_taken", "actor": "alice", "notes": "Suspendu."},
    )
    assert decision.status_code == 200
    assert decision.get_json()["status"] == "action_taken"


def test_appeal_workflow(client):
    create = client.post(
        "/v1/reports",
        json={
            "content_type": "event_feedback",
            "content_reference": "feedback_99",
            "reporter_id": 2,
        },
    )
    case_id = create.get_json()["id"]

    appeal = client.post(
        f"/v1/reports/{case_id}/appeals",
        json={"submitted_by": "user@example.com", "reason": "Contexte mal interprété"},
    )
    assert appeal.status_code == 201
    appeal_id = appeal.get_json()["id"]

    resolve = client.post(
        f"/v1/reports/appeals/{appeal_id}/decision",
        json={"decision": "overturned", "reviewer": "bob"},
    )
    assert resolve.status_code == 200
    assert resolve.get_json()["decision"] == "overturned"


def test_admin_escalation_and_listing(client):
    for reference in ("msg_a", "msg_b"):
        client.post(
            "/v1/reports",
            json={"content_type": "message", "content_reference": reference},
        )

    response = client.post(
        "/v1/admin/escalations",
        json={"case_ids": [1, 2], "actor": "moderator", "reason": "Menace"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["escalated"]

    listing = client.get("/v1/admin/cases?limit=5")
    assert listing.status_code == 200
    body = listing.get_json()
    assert "cases" in body
    assert len(body["cases"]) >= 2
