"""Automated filters combining heuristics, Redis counters, and optional ML."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Mapping

from redis.client import Redis

from ..clients.ml import ModerationMLClient
from ..config import ModerationConfig

DEFAULT_BANNED_TERMS = {
    "spam",
    "scam",
    "fraud",
    "terror",
    "abuse",
}


@dataclass(slots=True)
class FilterResult:
    status: str
    score: float
    labels: dict[str, Any]
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "score": self.score,
            "labels": self.labels,
            "reasons": self.reasons,
        }


class AutomatedFilterEngine:
    """Evaluate raw content using heuristics, rate limits, and ML signals."""

    def __init__(
        self,
        config: ModerationConfig,
        redis_client: Redis,
        ml_client: ModerationMLClient,
    ) -> None:
        self.config = config
        self.redis = redis_client
        self.ml_client = ml_client

    def evaluate(self, text: str, context: Mapping[str, Any] | None = None) -> FilterResult:
        context = context or {}
        normalized = text.lower()
        counters = Counter(normalized.split())

        reasons: list[str] = []
        labels: dict[str, Any] = {"heuristics": {}}

        banned_hits = {term: counters[term] for term in DEFAULT_BANNED_TERMS if counters[term]}
        if banned_hits:
            reasons.append("Contenu contient des termes prohibés.")
            labels["heuristics"]["banned_terms"] = banned_hits

        if len(text) > 2000:
            reasons.append("Le texte dépasse 2000 caractères.")
            labels.setdefault("heuristics", {})["length"] = len(text)

        score = 0.0
        if banned_hits:
            score = max(score, 0.95)

        user_id = context.get("user_id") if isinstance(context, Mapping) else None
        if user_id is not None:
            key = f"moderation:messages:user:{user_id}"
            messages = int(self.redis.incr(key))
            self.redis.expire(key, 3600)
            if messages > 50:
                reasons.append("Utilisateur dépasse le quota horaire de messages.")
                labels.setdefault("heuristics", {})["rate_limit"] = messages
                score = max(score, 0.65)

        if self.ml_client.is_enabled():
            ml_payload = {"text": text, "context": context}
            try:
                ml_result = self.ml_client.score(ml_payload)
            except Exception as exc:  # pragma: no cover - network failure path
                reasons.append(f"Classifier indisponible: {exc}")
            else:
                ml_score = float(ml_result.get("score", 0.0))
                score = max(score, ml_score)
                labels["ml"] = ml_result
                if ml_result.get("flagged"):
                    reasons.append("Le modèle ML a signalé le contenu.")

        status = "approved"
        if score >= self.config.auto_block_threshold:
            status = "blocked"
            reasons.append("Score automatique au-dessus du seuil de blocage.")
        elif score >= self.config.auto_approve_threshold:
            status = "needs_review"
            reasons.append("Score automatique nécessite une revue humaine.")

        return FilterResult(status=status, score=round(score, 4), labels=labels, reasons=reasons)


__all__ = ["AutomatedFilterEngine", "FilterResult"]
