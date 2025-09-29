"""Base ingestion pipeline primitives."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping, Sequence


class IngestionPipeline(ABC):
    """Abstract ingestion pipeline that normalises documents before indexing."""

    name: str
    index_name: str

    def __init__(self, name: str, index_name: str) -> None:
        self.name = name
        self.index_name = index_name

    @property
    @abstractmethod
    def mappings(self) -> Mapping[str, Any]:
        """Return index mapping definition."""

    @property
    def settings(self) -> Mapping[str, Any]:
        return {
            "analysis": {
                "analyzer": {
                    "rebuilt_french": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "asciifolding",
                            "french_stop",
                            "french_elision",
                            "french_stemmer",
                        ],
                    }
                }
            }
        }

    def lifecycle_policy(self) -> Mapping[str, Any]:
        return {
            "policy": {
                "phases": {
                    "hot": {"actions": {"rollover": {"max_size": "20gb", "max_age": "30d"}}},
                    "warm": {"actions": {"forcemerge": {"max_num_segments": 1}}},
                    "delete": {"min_age": "180d", "actions": {"delete": {}}},
                }
            }
        }

    def prepare_documents(self, items: Sequence[Mapping[str, Any]]) -> Iterable[Mapping[str, Any]]:
        return [self.transform_document(item) for item in items]

    @abstractmethod
    def transform_document(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """Normalise a single payload."""


__all__ = ["IngestionPipeline"]
