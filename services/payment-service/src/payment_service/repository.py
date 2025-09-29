"""Simple in-memory repositories used for the sandbox implementation."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class SubscriptionRecord:
    """Persisted subscription information."""

    subscription_id: str
    customer_id: str
    plan_id: str
    status: str
    metadata: Dict[str, str] = field(default_factory=dict)


class SubscriptionRepository:
    """Thread-safe in-memory store for subscriptions."""

    def __init__(self) -> None:
        self._records: Dict[str, SubscriptionRecord] = {}
        self._lock = threading.Lock()

    def upsert(self, record: SubscriptionRecord) -> SubscriptionRecord:
        with self._lock:
            self._records[record.subscription_id] = record
        return record

    def get(self, subscription_id: str) -> Optional[SubscriptionRecord]:
        with self._lock:
            return self._records.get(subscription_id)


class InvoiceRepository:
    """Thread-safe in-memory store for invoice payloads."""

    def __init__(self) -> None:
        self._records: Dict[str, Dict[str, str]] = {}
        self._lock = threading.Lock()

    def save(self, invoice_id: str, payload: Dict[str, str]) -> Dict[str, str]:
        with self._lock:
            self._records[invoice_id] = payload
        return payload

    def get(self, invoice_id: str) -> Optional[Dict[str, str]]:
        with self._lock:
            return self._records.get(invoice_id)


__all__ = [
    "InvoiceRepository",
    "SubscriptionRecord",
    "SubscriptionRepository",
]

