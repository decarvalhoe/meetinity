import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import jwt
import pytest
import requests
from pathlib import Path
from urllib3._collections import HTTPHeaderDict


class _CapturingHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.app import create_app  # noqa: E402


def _patch_proxy_session(monkeypatch, handler):
    mock_session = Mock()
    mock_session.request = handler
    monkeypatch.setattr("src.routes.proxy._get_http_session", lambda: mock_session)
    return mock_session


def _make_jwt_token(secret: str = "secret", sub: str = "user-123") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "exp": now + timedelta(minutes=5),
        "iat": now,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def _create_app_without_cors_origins(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.setenv("USER_SERVICE_URL", "http://upstream")
    monkeypatch.setenv("EVENT_SERVICE_URL", "http://events")
    monkeypatch.setenv("MATCHING_SERVICE_URL", "http://matching")
    monkeypatch.setenv("MESSAGING_SERVICE_URL", "http://messaging")
    monkeypatch.setenv("ANALYTICS_SERVICE_URL", "http://analytics")
    monkeypatch.setenv("PAYMENT_SERVICE_URL", "http://payments")
    monkeypatch.setenv("JWT_SECRET", "secret")
    monkeypatch.setenv("RATE_LIMIT_AUTH", "10/minute")
    monkeypatch.setenv("RATE_LIMIT_EVENTS", "10/minute")
    monkeypatch.setenv("RATE_LIMIT_MATCHING", "10/minute")
    monkeypatch.setenv("RESILIENCE_BACKOFF_FACTOR", "0")

    mock_resp = Mock()
    mock_resp.status_code = 200
    monkeypatch.setattr(
        "src.app.requests.get", lambda *args, **kwargs: mock_resp
    )

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def app(monkeypatch):
    os.environ["USER_SERVICE_URL"] = "http://upstream"
    os.environ["EVENT_SERVICE_URL"] = "http://events"
    os.environ["MATCHING_SERVICE_URL"] = "http://matching"
    os.environ["MESSAGING_SERVICE_URL"] = "http://messaging"
    os.environ["ANALYTICS_SERVICE_URL"] = "http://analytics"
    os.environ["PAYMENT_SERVICE_URL"] = "http://payments"
    os.environ["CORS_ORIGINS"] = ""
    os.environ["JWT_SECRET"] = "secret"
    os.environ["RATE_LIMIT_AUTH"] = "10/minute"
    os.environ["RATE_LIMIT_EVENTS"] = "10/minute"
    os.environ["RATE_LIMIT_MATCHING"] = "10/minute"
    os.environ["RESILIENCE_BACKOFF_FACTOR"] = "0"

    mock_resp = Mock()
    mock_resp.status_code = 200
    monkeypatch.setattr(
        "src.app.requests.get", lambda *args, **kwargs: mock_resp
    )

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["upstreams"]["user_service"] == "up"
    assert response.json["upstreams"]["event_service"] == "up"
    assert response.json["upstreams"]["matching_service"] == "up"


def test_health_upstream_down(client, monkeypatch):
    def fail_health(*args, **kwargs):
        raise requests.RequestException()

    monkeypatch.setattr("src.app.requests.get", fail_health)

    response = client.get("/health")
    assert response.status_code == 503
    assert response.json["status"] == "error"
    assert response.json["upstreams"]["user_service"] == "down"
    assert response.json["upstreams"]["event_service"] == "down"
    assert response.json["upstreams"]["matching_service"] == "down"


def test_users_requires_jwt(client):
    response = client.get("/api/users/me")
    assert response.status_code == 401
    assert response.json == {"error": {"code": 401, "message": "Unauthorized"}}


def test_events_requires_jwt(client):
    response = client.get("/api/events")
    assert response.status_code == 401
    assert response.json == {"error": {"code": 401, "message": "Unauthorized"}}


def test_matching_requires_jwt(client):
    response = client.get("/api/matching")
    assert response.status_code == 401
    assert response.json == {"error": {"code": 401, "message": "Unauthorized"}}


def test_options_users_without_authorization(client):
    response = client.options("/api/users")
    assert response.status_code != 401


def test_auth_proxy_failure(client, monkeypatch):
    def fail_request(*args, **kwargs):
        raise requests.RequestException()
    _patch_proxy_session(monkeypatch, fail_request)
    response = client.post("/api/auth/login")
    assert response.status_code == 502
    assert response.json == {"error": {"code": 502, "message": "Bad Gateway"}}


def test_proxy_preserves_duplicate_query_params(client, monkeypatch):
    captured = {}

    def fake_request(*args, **kwargs):
        captured["params"] = kwargs.get("params")
        captured["timeout"] = kwargs.get("timeout")
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = b"{}"
        mock_resp.headers = {}
        return mock_resp

    _patch_proxy_session(monkeypatch, fake_request)

    response = client.get("/api/auth/tokens?tag=a&tag=b")

    assert response.status_code == 200
    assert captured["params"] == [("tag", "a"), ("tag", "b")]
    assert captured["timeout"] == (2.0, 10.0)


def test_events_proxy_targets_event_service(client, monkeypatch):
    token = _make_jwt_token(sub="event-tester")
    captured: dict[str, object] = {}

    def fake_execute(**kwargs):
        registry = kwargs["registry"]
        service_name = kwargs["service_name"]
        instances = registry.get_instances(service_name)
        captured["service_name"] = service_name
        captured["instances"] = [inst.url for inst in instances]
        assert instances, "Expected event service instances"
        return kwargs["request_func"](instances[0])

    resilience = client.application.extensions["resilience_middleware"]
    monkeypatch.setattr(resilience, "execute", fake_execute)

    calls: list[str] = []

    def fake_request(method, url, **kwargs):
        calls.append(url)
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = b"{}"
        mock_resp.headers = {}
        mock_resp.raw = Mock(headers={})
        return mock_resp

    _patch_proxy_session(monkeypatch, fake_request)

    response = client.get(
        "/api/events/list",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert captured["service_name"] == "event-service"
    assert any(url.startswith("http://events") for url in captured["instances"])
    assert any(url.startswith("http://events") and url.endswith("/events/list") for url in calls)


def test_matching_proxy_targets_matching_service(client, monkeypatch):
    token = _make_jwt_token(sub="matching-tester")
    captured: dict[str, object] = {}

    def fake_execute(**kwargs):
        registry = kwargs["registry"]
        service_name = kwargs["service_name"]
        instances = registry.get_instances(service_name)
        captured["service_name"] = service_name
        captured["instances"] = [inst.url for inst in instances]
        assert instances, "Expected matching service instances"
        return kwargs["request_func"](instances[0])

    resilience = client.application.extensions["resilience_middleware"]
    monkeypatch.setattr(resilience, "execute", fake_execute)

    calls: list[str] = []

    def fake_request(method, url, **kwargs):
        calls.append(url)
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = b"{}"
        mock_resp.headers = {}
        mock_resp.raw = Mock(headers={})
        return mock_resp

    _patch_proxy_session(monkeypatch, fake_request)

    response = client.get(
        "/api/matching/find",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert captured["service_name"] == "matching-service"
    assert any(url.startswith("http://matching") for url in captured["instances"])
    assert any(url.startswith("http://matching") and url.endswith("/matching/find") for url in calls)


def test_proxy_preserves_multiple_set_cookie_headers(client, monkeypatch):
    header_dict = HTTPHeaderDict()
    header_dict.add("Set-Cookie", "a=1; Path=/")
    header_dict.add("Set-Cookie", "b=2; Path=/")

    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.content = b"{}"
    mock_resp.raw = Mock(headers=header_dict)
    mock_resp.headers = {}

    _patch_proxy_session(monkeypatch, lambda *args, **kwargs: mock_resp)

    response = client.get("/api/auth/session")

    assert response.status_code == 200
    assert response.headers.getlist("Set-Cookie") == [
        "a=1; Path=/",
        "b=2; Path=/",
    ]


def test_proxy_generates_request_id_and_forwarded_headers(client, monkeypatch):
    captured = {}

    def fake_request(*args, **kwargs):
        captured["headers"] = kwargs.get("headers")
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = b"{}"
        mock_resp.headers = {}
        return mock_resp

    _patch_proxy_session(monkeypatch, fake_request)

    response = client.get(
        "/api/auth/session",
        base_url="https://localhost",
        environ_base={"REMOTE_ADDR": "198.51.100.4"},
    )

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    forwarded_headers = captured["headers"]
    assert forwarded_headers["X-Forwarded-For"] == "198.51.100.4"
    assert forwarded_headers["X-Forwarded-Proto"] == "https"
    assert forwarded_headers["X-Request-ID"] == response.headers["X-Request-ID"]


def test_proxy_appends_forwarded_for_header(client, monkeypatch):
    captured = {}

    def fake_request(*args, **kwargs):
        captured["headers"] = kwargs.get("headers")
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = b"{}"
        mock_resp.headers = {}
        return mock_resp

    _patch_proxy_session(monkeypatch, fake_request)

    response = client.get(
        "/api/auth/session",
        headers={"X-Forwarded-For": "203.0.113.10"},
        environ_base={"REMOTE_ADDR": "198.51.100.4"},
    )

    assert response.status_code == 200
    forwarded_headers = captured["headers"]
    assert (
        forwarded_headers["X-Forwarded-For"]
        == "203.0.113.10, 198.51.100.4"
    )


def test_request_logging_includes_metadata(client):
    handler = _CapturingHandler()
    handler.setLevel(logging.INFO)
    client.application.logger.addHandler(handler)
    try:
        response = client.get(
            "/health",
            headers={"X-Forwarded-For": "203.0.113.20"},
            environ_base={"REMOTE_ADDR": "198.51.100.4"},
        )
    finally:
        client.application.logger.removeHandler(handler)

    assert response.status_code == 200
    assert handler.records
    payload = json.loads(handler.records[-1].getMessage())
    assert payload["method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["status"] == 200
    assert payload["ip"] == "203.0.113.20"
    assert payload["request_id"] == response.headers["X-Request-ID"]


def test_request_logging_includes_user_id(client, monkeypatch):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.content = b"{}"
    mock_resp.headers = {}

    _patch_proxy_session(monkeypatch, lambda *args, **kwargs: mock_resp)

    handler = _CapturingHandler()
    handler.setLevel(logging.INFO)
    client.application.logger.addHandler(handler)

    token = jwt.encode(
        {
            "sub": "user-123",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            "iat": datetime.now(timezone.utc),
        },
        "secret",
        algorithm="HS256",
    )

    try:
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        client.application.logger.removeHandler(handler)

    assert response.status_code == 200
    assert handler.records
    payload = json.loads(handler.records[-1].getMessage())
    assert payload["user_id"] == "user-123"


def test_cors_allows_any_origin_when_env_absent(monkeypatch):
    app = _create_app_without_cors_origins(monkeypatch)
    origin = "https://example.com"
    with app.test_client() as client:
        response = client.get("/health", headers={"Origin": origin})

    assert response.headers.get("Access-Control-Allow-Origin") == origin


def test_cors_allows_another_origin_when_env_absent(monkeypatch):
    app = _create_app_without_cors_origins(monkeypatch)
    origin = "https://another.test"
    with app.test_client() as client:
        response = client.get("/health", headers={"Origin": origin})

    assert response.headers.get("Access-Control-Allow-Origin") == origin


def test_graphql_contract_publication(monkeypatch, tmp_path):
    monkeypatch.setenv("GRAPHQL_FEDERATION_ENABLED", "true")
    monkeypatch.setenv("GRAPHQL_ROUTER_URL", "http://router/graphql")
    monkeypatch.setenv("GRAPHQL_SUPERGRAPH_DIR", str(tmp_path / "supergraph"))
    monkeypatch.setenv("GRAPHQL_CONTRACT_DIR", str(tmp_path / "contracts"))

    subgraphs = [
        {
            "name": "identity",
            "routing_url": "http://router.identity/graphql",
            "sdl": "type Query { users: [ID!] profile: ID }",
            "rest_mappings": {"/api/users": "users", "/api/profile": "profile"},
        },
        {
            "name": "auth",
            "routing_url": "http://router.auth/graphql",
            "sdl": "type Query { auth: Boolean }",
            "rest_mappings": {"/api/auth": "auth"},
        },
        {
            "name": "engagement",
            "routing_url": "http://router.engagement/graphql",
            "sdl": "type Query { events: [ID!] matching: [ID!] conversations: [ID!] analytics: [ID!] }",
            "rest_mappings": {
                "/api/events": "events",
                "/api/matching": "matching",
                "/api/conversations": "conversations",
                "/api/analytics": "analytics",
            },
        },
    ]
    monkeypatch.setenv("GRAPHQL_SUBGRAPHS", json.dumps(subgraphs))

    monkeypatch.setenv("USER_SERVICE_URL", "http://users")
    monkeypatch.setenv("EVENT_SERVICE_URL", "http://events")
    monkeypatch.setenv("MATCHING_SERVICE_URL", "http://matching")
    monkeypatch.setenv("JWT_SECRET", "secret")
    monkeypatch.setenv("RATE_LIMIT_AUTH", "10/minute")
    monkeypatch.setenv("RATE_LIMIT_EVENTS", "10/minute")
    monkeypatch.setenv("RATE_LIMIT_MATCHING", "10/minute")
    monkeypatch.setenv("RESILIENCE_BACKOFF_FACTOR", "0")

    mock_resp = Mock()
    mock_resp.status_code = 200
    monkeypatch.setattr("src.app.requests.get", lambda *args, **kwargs: mock_resp)

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        schema_resp = client.get("/graphql/schema")
        assert schema_resp.status_code == 200
        assert "Supergraph SDL" in schema_resp.data.decode("utf-8")

        metadata_resp = client.get("/graphql/metadata")
        assert metadata_resp.status_code == 200
        metadata = metadata_resp.get_json()
        assert metadata["version"] == app.config["GRAPHQL_SCHEMA_VERSION"]
        assert "/api/users" in metadata["operations"]

    manifest_path = Path(app.config["GRAPHQL_MANIFEST_PATH"])
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["version"] == app.config["GRAPHQL_SCHEMA_VERSION"]

