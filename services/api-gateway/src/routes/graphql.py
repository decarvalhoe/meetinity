"""GraphQL federation endpoints exposed by the gateway."""

from __future__ import annotations

from typing import Iterable

import requests
from flask import Blueprint, Response, current_app, jsonify, request

from ..graphql import FederatedGraphQLGateway
from ..utils.responses import error_response


FORWARDED_HEADERS: tuple[str, ...] = (
    "content-type",
    "accept",
    "x-request-id",
    "authorization",
)


def create_graphql_blueprint() -> Blueprint:
    blueprint = Blueprint("graphql", __name__)

    @blueprint.route("/graphql", methods=["GET", "POST", "OPTIONS"])
    def graphql_proxy() -> Response:
        federation = _get_federation()
        if federation is None:
            return error_response(404, "GraphQL federation disabled")

        if request.method == "OPTIONS":
            return Response(status=204)

        router_url = current_app.config.get("GRAPHQL_ROUTER_URL") or ""
        if not router_url:
            return error_response(503, "GraphQL router not configured")

        session = current_app.extensions.get("http_session")
        if session is None:
            return error_response(500, "HTTP session not initialised")

        timeout = (
            float(current_app.config.get("PROXY_TIMEOUT_CONNECT", 2.0)),
            float(current_app.config.get("PROXY_TIMEOUT_READ", 10.0)),
        )

        headers = _filter_headers(request.headers.items())
        params = request.args.items(multi=True)
        try:
            upstream: requests.Response = session.request(
                request.method,
                router_url,
                headers=headers,
                params=list(params),
                data=request.get_data(),
                timeout=timeout,
            )
        except requests.RequestException:
            return error_response(502, "GraphQL router unavailable")

        response = Response(upstream.content, status=upstream.status_code)
        for key, value in upstream.headers.items():
            if key.lower() == "content-length":
                continue
            response.headers[key] = value
        return response

    @blueprint.route("/graphql/schema", methods=["GET"])
    def graphql_schema() -> Response:
        federation = _get_federation()
        if federation is None or federation.latest is None:
            return error_response(404, "GraphQL federation disabled")
        schema = federation.latest
        return Response(schema.supergraph_sdl, mimetype="text/plain")

    @blueprint.route("/graphql/metadata", methods=["GET"])
    def graphql_metadata() -> Response:
        federation = _get_federation()
        if federation is None or federation.latest is None:
            return error_response(404, "GraphQL federation disabled")
        schema = federation.latest
        manifest_path = schema.manifest_path
        metadata = {
            "version": schema.version,
            "composed_at": schema.composed_at.isoformat(),
            "manifest_path": str(manifest_path),
            "supergraph_path": str(schema.supergraph_path),
            "operations": federation.operation_catalog,
            "subgraphs": [
                {
                    "name": snapshot.definition.name,
                    "routing_url": snapshot.definition.routing_url,
                    "digest": snapshot.digest,
                }
                for snapshot in schema.subgraphs
            ],
        }
        return jsonify(metadata)

    @blueprint.route("/graphql/operations", methods=["GET"])
    def graphql_operations() -> Response:
        federation = _get_federation()
        if federation is None:
            return error_response(404, "GraphQL federation disabled")
        return jsonify(federation.operation_catalog)

    return blueprint


def _filter_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    allowed = {name.lower() for name in FORWARDED_HEADERS}
    filtered: dict[str, str] = {}
    for key, value in headers:
        if key.lower() in allowed:
            filtered[key] = value
    return filtered


def _get_federation() -> FederatedGraphQLGateway | None:
    federation = current_app.extensions.get("graphql_federation")
    if not isinstance(federation, FederatedGraphQLGateway):
        return None
    return federation

