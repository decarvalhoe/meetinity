"""Configuration helpers for the moderation service."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from flask import Flask


@dataclass(slots=True)
class ModerationConfig:
    """Runtime configuration derived from the Flask app."""

    database_url: str
    redis_url: str
    kafka_bootstrap: str | None
    moderation_topic: str
    kafka_schema_registry_url: str | None
    kafka_security_protocol: str | None
    kafka_sasl_mechanism: str | None
    kafka_sasl_username: str | None
    kafka_sasl_password: str | None
    kafka_dead_letter_topic: str | None
    ml_classifier_url: str | None
    auto_approve_threshold: float
    auto_block_threshold: float

    @classmethod
    def from_app(cls, app: Flask) -> "ModerationConfig":
        config: Mapping[str, Any] = app.config
        return cls(
            database_url=config["DATABASE_URL"],
            redis_url=config["REDIS_URL"],
            kafka_bootstrap=config.get("KAFKA_BOOTSTRAP_SERVERS"),
            moderation_topic=config.get("KAFKA_MODERATION_TOPIC", "moderation.events"),
            kafka_schema_registry_url=config.get("KAFKA_SCHEMA_REGISTRY_URL"),
            kafka_security_protocol=config.get("KAFKA_SECURITY_PROTOCOL"),
            kafka_sasl_mechanism=config.get("KAFKA_SASL_MECHANISM"),
            kafka_sasl_username=config.get("KAFKA_SASL_USERNAME"),
            kafka_sasl_password=config.get("KAFKA_SASL_PASSWORD"),
            kafka_dead_letter_topic=config.get("KAFKA_DLQ_TOPIC"),
            ml_classifier_url=config.get("ML_CLASSIFIER_URL"),
            auto_approve_threshold=float(config.get("AUTO_APPROVE_THRESHOLD", 0.55)),
            auto_block_threshold=float(config.get("AUTO_BLOCK_THRESHOLD", 0.9)),
        )


__all__ = ["ModerationConfig"]
