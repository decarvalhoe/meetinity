"""Configuration for the search service."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Sequence

from pydantic import AnyHttpUrl, Field, ConfigDict, field_validator
from pydantic_settings import BaseSettings


class SearchSettings(BaseSettings):
    """Runtime settings for the search service."""

    nodes: Sequence[AnyHttpUrl] | None = Field(
        default=None,
        alias="SEARCH_NODES",
        description="Comma separated Elasticsearch/OpenSearch nodes.",
    )
    username: str | None = Field(default=None, alias="SEARCH_USERNAME")
    password: str | None = Field(default=None, alias="SEARCH_PASSWORD")
    verify_certs: bool = Field(default=True, alias="SEARCH_VERIFY_CERTS")
    timeout: int = Field(default=10, alias="SEARCH_TIMEOUT")
    use_in_memory_backend: bool = Field(
        default=False,
        alias="SEARCH_USE_IN_MEMORY",
        description="Enable the in-memory backend for development/testing.",
    )

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        populate_by_name=True,
    )

    @field_validator("nodes", mode="before")
    @classmethod
    def _split_nodes(cls, value: str | Sequence[str] | None) -> Sequence[AnyHttpUrl] | None:
        if value is None or isinstance(value, (list, tuple)):
            return value  # type: ignore[return-value]
        parts = [part.strip() for part in value.split(",") if part.strip()]
        return parts  # type: ignore[return-value]

    def hosts(self) -> List[str]:
        if self.nodes:
            return [str(node) for node in self.nodes]
        return ["http://localhost:9200"]


@lru_cache(maxsize=1)
def get_settings() -> SearchSettings:
    return SearchSettings()


__all__ = ["SearchSettings", "get_settings"]
