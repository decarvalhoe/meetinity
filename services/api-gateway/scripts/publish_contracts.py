#!/usr/bin/env python3
"""Generate and publish API gateway contracts for CI/CD workflows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _add_src_to_path() -> None:
    script_path = Path(__file__).resolve()
    project_root = script_path.parents[1]
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))


_add_src_to_path()

from src.app import create_app  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--print-path",
        action="store_true",
        help="Print only the supergraph path for shell scripting.",
    )
    args = parser.parse_args()

    app = create_app()
    federation = app.extensions.get("graphql_federation")
    if federation is None:
        print("GraphQL federation is disabled; nothing to publish", file=sys.stderr)
        return 1

    schema = federation.refresh_schema(force=True)
    manifest_path = federation.publish_contract()

    if args.print_path:
        print(schema.supergraph_path)
    else:
        output = {
            "version": schema.version,
            "supergraph_path": str(schema.supergraph_path),
            "manifest_path": str(manifest_path),
        }
        json.dump(output, sys.stdout, indent=2)
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via integration tests
    raise SystemExit(main())
