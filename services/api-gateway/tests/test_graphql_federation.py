import json
import os
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.graphql import (
    FederatedGraphQLGateway,
    SchemaCompositionError,
    SubgraphDefinition,
    load_subgraph_definitions,
)
from src.routes import PROXY_ROUTE_DEFINITIONS


def test_load_subgraph_definitions_from_json():
    payload = json.dumps(
        [
            {
                "name": "identity",
                "routing_url": "http://router.identity/graphql",
                "sdl": "type Query { viewer: ID }",
                "rest_mappings": {"/api/users": "viewer"},
            }
        ]
    )

    definitions = load_subgraph_definitions(payload)
    assert len(definitions) == 1
    assert definitions[0].name == "identity"
    assert definitions[0].routing_url.endswith("graphql")


def test_federated_supergraph_versioning(tmp_path: Path):
    subgraphs = (
        SubgraphDefinition(
            name="identity",
            routing_url="http://router.identity/graphql",
            sdl="""
            type Query {
              users: [ID!]
              profile: ID
            }
            """,
            rest_mappings={
                "/api/users": "users",
                "/api/profile": "profile",
            },
        ),
        SubgraphDefinition(
            name="engagement",
            routing_url="http://router.engagement/graphql",
            sdl="""
            type Query {
              events: [ID!]
              matching: [ID!]
              conversations: [ID!]
              analytics: [ID!]
            }
            """,
            rest_mappings={
                "/api/events": "events",
                "/api/matching": "matching",
                "/api/conversations": "conversations",
                "/api/analytics": "analytics",
            },
        ),
        SubgraphDefinition(
            name="auth",
            routing_url="http://router.auth/graphql",
            sdl="""
            type Mutation {
              login: Boolean
            }
            type Query {
              auth: Boolean
            }
            """,
            rest_mappings={"/api/auth": "auth"},
        ),
    )

    gateway = FederatedGraphQLGateway(
        subgraphs=subgraphs,
        supergraph_dir=tmp_path / "supergraph",
        contract_dir=tmp_path / "contracts",
    )

    initial = gateway.refresh_schema(force=True)
    assert initial.supergraph_path.exists()
    assert gateway.manifest_path is not None
    manifest = json.loads(Path(gateway.manifest_path).read_text(encoding="utf-8"))
    assert manifest["version"] == initial.version

    # Re-compose without changes should reuse the same version.
    cached = gateway.refresh_schema()
    assert cached.version == initial.version

    updated_auth = SubgraphDefinition(
        name="auth",
        routing_url="http://router.auth/graphql",
        sdl="""
        type Mutation {
          login: Boolean
          revoke: Boolean
        }
        type Query {
          auth: Boolean
        }
        """,
        rest_mappings={"/api/auth": "auth"},
    )
    gateway.replace_subgraphs((subgraphs[0], subgraphs[1], updated_auth))
    recomposed = gateway.refresh_schema(force=True)
    assert recomposed.version != initial.version
    assert (tmp_path / "supergraph" / f"supergraph-{recomposed.version}.graphql").exists()

    missing = gateway.validate_rest_mappings(PROXY_ROUTE_DEFINITIONS)
    assert missing == []


def test_load_subgraph_definitions_requires_routing_url():
    payload = json.dumps([{"name": "invalid"}])
    with pytest.raises(SchemaCompositionError):
        load_subgraph_definitions(payload)
