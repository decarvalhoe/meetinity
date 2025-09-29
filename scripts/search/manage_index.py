#!/usr/bin/env python3
"""Utility helpers for managing Meetinity search indexes."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from elasticsearch import Elasticsearch


def _client(args: argparse.Namespace) -> Elasticsearch:
    auth = None
    if args.username:
        auth = (args.username, args.password or "")
    return Elasticsearch(
        hosts=[args.host],
        verify_certs=not args.skip_tls_verify,
        basic_auth=auth,
        request_timeout=args.timeout,
    )


def command_create(args: argparse.Namespace) -> None:
    client = _client(args)
    body = {}
    if args.schema:
        body = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    if client.indices.exists(index=args.index):
        print(f"Index {args.index} already exists", file=sys.stderr)
        return
    client.indices.create(index=args.index, **body)
    print(f"Created index {args.index}")


def command_delete(args: argparse.Namespace) -> None:
    client = _client(args)
    client.indices.delete(index=args.index, ignore_unavailable=True)
    print(f"Deleted index {args.index}")


def command_reindex(args: argparse.Namespace) -> None:
    client = _client(args)
    payload = {
        "source": {"index": args.source},
        "dest": {"index": args.destination, "op_type": "create"},
    }
    response = client.reindex(body=payload, wait_for_completion=not args.async_mode)
    print(json.dumps(response, indent=2))


def command_synonyms(args: argparse.Namespace) -> None:
    client = _client(args)
    synonyms = [line.strip() for line in Path(args.file).read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = {
        "analysis": {
            "filter": {
                "meetinity_synonyms": {
                    "type": "synonym_graph",
                    "synonyms": synonyms,
                }
            },
            "analyzer": {
                "meetinity_text": {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "meetinity_synonyms"],
                }
            },
        }
    }
    client.indices.close(index=args.index)
    client.indices.put_settings(index=args.index, settings=payload)
    client.indices.open(index=args.index)
    print(f"Updated synonyms for {args.index} using {args.file}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="https://search.meetinity.com", help="Search cluster endpoint")
    parser.add_argument("--username", help="Basic auth username")
    parser.add_argument("--password", help="Basic auth password")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument("--skip-tls-verify", action="store_true", help="Disable TLS verification")

    sub = parser.add_subparsers(dest="command", required=True)

    create_cmd = sub.add_parser("create", help="Create an index from an optional schema JSON file")
    create_cmd.add_argument("index")
    create_cmd.add_argument("--schema", help="Path to schema JSON containing mappings/settings")
    create_cmd.set_defaults(func=command_create)

    delete_cmd = sub.add_parser("delete", help="Delete an index")
    delete_cmd.add_argument("index")
    delete_cmd.set_defaults(func=command_delete)

    reindex_cmd = sub.add_parser("reindex", help="Reindex from one index into another")
    reindex_cmd.add_argument("source")
    reindex_cmd.add_argument("destination")
    reindex_cmd.add_argument("--async-mode", action="store_true", help="Return before completion")
    reindex_cmd.set_defaults(func=command_reindex)

    synonyms_cmd = sub.add_parser("synonyms", help="Update synonyms filter from file")
    synonyms_cmd.add_argument("index")
    synonyms_cmd.add_argument("file", help="File containing synonym definitions")
    synonyms_cmd.set_defaults(func=command_synonyms)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
