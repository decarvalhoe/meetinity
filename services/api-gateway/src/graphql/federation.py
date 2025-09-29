"""GraphQL federation and schema composition helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import requests

from ..observability.metrics import MetricsRegistry

DEFAULT_SUPERGRAPH_FILENAME = "supergraph"


class SchemaCompositionError(RuntimeError):
    """Raised when the supergraph cannot be composed."""


@dataclass(frozen=True)
class SubgraphDefinition:
    """Describe a GraphQL subgraph participating in federation."""

    name: str
    routing_url: str
    schema_url: str | None = None
    schema_path: str | None = None
    sdl: str | None = None
    headers: Mapping[str, str] = field(default_factory=dict)
    rest_mappings: Mapping[str, str] = field(default_factory=dict)

    def normalized_rest_mappings(self) -> Mapping[str, str]:
        """Return REST to GraphQL mappings with normalized paths."""

        normalized: dict[str, str] = {}
        for path, field_name in self.rest_mappings.items():
            if not path:
                continue
            normalized[_normalize_path(path)] = str(field_name)
        return normalized


@dataclass(frozen=True)
class SubgraphSnapshot:
    """Snapshot of a subgraph schema used during composition."""

    definition: SubgraphDefinition
    sdl: str
    digest: str


@dataclass(frozen=True)
class FederatedSchema:
    """Metadata describing a composed supergraph."""

    version: str
    composed_at: datetime
    supergraph_sdl: str
    supergraph_path: Path
    manifest_path: Path
    subgraphs: tuple[SubgraphSnapshot, ...]


def _normalize_path(path: str) -> str:
    value = "/" + path.strip()
    value = value.replace("//", "/")
    if not value.startswith("/"):
        value = "/" + value
    return value.rstrip("/") or "/"


def _load_file(path: Path) -> str:
    if not path.exists():
        raise SchemaCompositionError(f"Schema file '{path}' does not exist")
    return path.read_text(encoding="utf-8")


def _request_schema(session: requests.Session, definition: SubgraphDefinition) -> str:
    if not definition.schema_url:
        raise SchemaCompositionError(
            f"Subgraph '{definition.name}' is missing a schema_url"
        )
    try:
        response = session.get(
            definition.schema_url,
            headers=dict(definition.headers),
            timeout=(5, 10),
        )
    except requests.RequestException as exc:  # pragma: no cover - network failure
        raise SchemaCompositionError(
            f"Failed to download schema for subgraph '{definition.name}': {exc}"
        ) from exc

    if response.status_code >= 400:
        raise SchemaCompositionError(
            f"Schema endpoint for subgraph '{definition.name}' returned {response.status_code}"
        )

    return response.text


def load_subgraph_definitions(
    raw: str,
    *,
    hierarchical: Mapping[str, Any] | None = None,
) -> tuple[SubgraphDefinition, ...]:
    """Load subgraph definitions from a JSON string or hierarchical config."""

    if raw.strip():
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SchemaCompositionError("Invalid GRAPHQL_SUBGRAPHS payload") from exc
    else:
        payload = _hierarchical_to_payload(hierarchical or {})

    if not payload:
        return ()

    definitions: list[SubgraphDefinition] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise SchemaCompositionError("Invalid subgraph configuration entry")
        name = str(item.get("name") or item.get("NAME") or "").strip()
        routing_url = str(item.get("routing_url") or item.get("ROUTING_URL") or "").strip()
        if not name or not routing_url:
            raise SchemaCompositionError("Subgraph entries require 'name' and 'routing_url'")
        schema_url = item.get("schema_url") or item.get("SCHEMA_URL")
        schema_path = item.get("schema_path") or item.get("SCHEMA_PATH")
        sdl = item.get("sdl") or item.get("SDL")
        headers = item.get("headers") or item.get("HEADERS") or {}
        rest_mappings = item.get("rest_mappings") or item.get("REST_MAPPINGS") or {}
        definitions.append(
            SubgraphDefinition(
                name=name,
                routing_url=routing_url,
                schema_url=str(schema_url) if schema_url else None,
                schema_path=str(schema_path) if schema_path else None,
                sdl=str(sdl) if sdl else None,
                headers={str(k): str(v) for k, v in dict(headers).items()},
                rest_mappings={str(k): str(v) for k, v in dict(rest_mappings).items()},
            )
        )
    return tuple(definitions)


def _hierarchical_to_payload(tree: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    graphql_tree = tree.get("GRAPHQL")
    if not isinstance(graphql_tree, Mapping):
        return []
    subgraphs = graphql_tree.get("SUBGRAPHS")
    if not isinstance(subgraphs, Mapping):
        return []
    payload: list[Mapping[str, Any]] = []
    for name, data in subgraphs.items():
        if not isinstance(data, Mapping):
            continue
        entry: dict[str, Any] = {"name": name}
        for key, value in data.items():
            entry[key.lower()] = value
        payload.append(entry)
    return payload


class FederatedGraphQLGateway:
    """Compose and publish a federated GraphQL supergraph."""

    def __init__(
        self,
        *,
        subgraphs: Sequence[SubgraphDefinition],
        supergraph_dir: Path,
        contract_dir: Path,
        session: requests.Session | None = None,
        metrics: MetricsRegistry | None = None,
        clock: callable | None = None,
    ) -> None:
        if not subgraphs:
            raise SchemaCompositionError("At least one subgraph must be configured")
        self._subgraphs: list[SubgraphDefinition] = list(subgraphs)
        self._supergraph_dir = Path(supergraph_dir)
        self._contract_dir = Path(contract_dir)
        self._session = session or requests.Session()
        self._metrics = metrics
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._latest: FederatedSchema | None = None
        self._operation_catalog: dict[str, dict[str, str]] = {}

    @property
    def latest(self) -> FederatedSchema | None:
        return self._latest

    @property
    def operation_catalog(self) -> Mapping[str, Mapping[str, str]]:
        return dict(self._operation_catalog)

    @property
    def manifest_path(self) -> Path | None:
        if self._latest:
            return self._latest.manifest_path
        return None

    def replace_subgraphs(self, subgraphs: Sequence[SubgraphDefinition]) -> None:
        if not subgraphs:
            raise SchemaCompositionError("At least one subgraph must be provided")
        self._subgraphs = list(subgraphs)

    def refresh_schema(self, *, force: bool = False) -> FederatedSchema:
        """Compose the supergraph and publish metadata if required."""

        snapshots = tuple(self._load_subgraphs())
        digest_source = json.dumps(
            [(snapshot.definition.name, snapshot.digest) for snapshot in snapshots],
            sort_keys=True,
        ).encode("utf-8")
        version = hashlib.sha256(digest_source).hexdigest()

        if not force and self._latest and self._latest.version == version:
            return self._latest

        composed_at = self._clock()
        supergraph_sdl = self._compose_supergraph(snapshots, composed_at)
        supergraph_path = self._write_supergraph(version, supergraph_sdl)
        manifest_path = self._write_manifest(version, composed_at, snapshots, supergraph_path)
        schema = FederatedSchema(
            version=version,
            composed_at=composed_at,
            supergraph_sdl=supergraph_sdl,
            supergraph_path=supergraph_path,
            manifest_path=manifest_path,
            subgraphs=snapshots,
        )
        self._latest = schema
        self._operation_catalog = self._build_operation_catalog(snapshot.definition for snapshot in snapshots)
        if self._metrics is not None:
            self._metrics.record_supergraph_version(version)
        return schema

    def publish_contract(self) -> Path:
        schema = self.refresh_schema(force=False)
        return schema.manifest_path

    def validate_rest_mappings(
        self, routes: Iterable[Any]
    ) -> list[str]:
        missing: list[str] = []
        if not self._operation_catalog:
            return [getattr(route, "gateway_path", "") for route in routes]
        for route in routes:
            gateway_path = getattr(route, "gateway_path", "")
            normalized = _normalize_path(gateway_path)
            if normalized not in self._operation_catalog:
                missing.append(gateway_path)
        return missing

    def _load_subgraphs(self) -> Sequence[SubgraphSnapshot]:
        snapshots: list[SubgraphSnapshot] = []
        for definition in self._subgraphs:
            sdl = self._load_sdl(definition)
            digest = hashlib.sha256(sdl.encode("utf-8")).hexdigest()
            snapshots.append(SubgraphSnapshot(definition, sdl, digest))
        return snapshots

    def _load_sdl(self, definition: SubgraphDefinition) -> str:
        if definition.sdl:
            return definition.sdl
        if definition.schema_path:
            return _load_file(Path(definition.schema_path))
        return _request_schema(self._session, definition)

    def _compose_supergraph(
        self, snapshots: Sequence[SubgraphSnapshot], composed_at: datetime
    ) -> str:
        sections = [
            "# Supergraph SDL generated by Meetinity API Gateway",
            f"# composed_at: {composed_at.isoformat()}",
        ]
        for snapshot in snapshots:
            sections.append(f"# Subgraph: {snapshot.definition.name}")
            sections.append(snapshot.sdl.strip())
        return "\n\n".join(sections) + "\n"

    def _write_supergraph(self, version: str, sdl: str) -> Path:
        self._supergraph_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{DEFAULT_SUPERGRAPH_FILENAME}-{version}.graphql"
        path = self._supergraph_dir / filename
        path.write_text(sdl, encoding="utf-8")
        symlink = self._supergraph_dir / f"{DEFAULT_SUPERGRAPH_FILENAME}.graphql"
        try:
            if symlink.exists() or symlink.is_symlink():
                symlink.unlink()
            symlink.symlink_to(path.name)
        except OSError:
            # Filesystems without symlink support are tolerated.
            pass
        return path

    def _write_manifest(
        self,
        version: str,
        composed_at: datetime,
        snapshots: Sequence[SubgraphSnapshot],
        supergraph_path: Path,
    ) -> Path:
        self._contract_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self._contract_dir / "graphql-supergraph.json"
        payload = {
            "version": version,
            "composed_at": composed_at.isoformat(),
            "supergraph_path": str(supergraph_path),
            "subgraphs": [
                {
                    "name": snapshot.definition.name,
                    "routing_url": snapshot.definition.routing_url,
                    "schema_url": snapshot.definition.schema_url,
                    "schema_path": snapshot.definition.schema_path,
                    "rest_mappings": snapshot.definition.normalized_rest_mappings(),
                    "digest": snapshot.digest,
                }
                for snapshot in snapshots
            ],
            "operations": self._build_operation_catalog(
                snapshot.definition for snapshot in snapshots
            ),
        }
        manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return manifest_path

    def _build_operation_catalog(
        self, definitions: Iterable[SubgraphDefinition]
    ) -> dict[str, dict[str, str]]:
        catalog: dict[str, dict[str, str]] = {}
        for definition in definitions:
            for path, field_name in definition.normalized_rest_mappings().items():
                catalog[path] = {
                    "field": field_name,
                    "subgraph": definition.name,
                }
        return catalog

