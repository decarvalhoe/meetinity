"""Runtime configuration for the payment service."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class ProviderSettings(BaseSettings):
    """Common settings for payment providers."""

    api_key: str = Field(..., alias="API_KEY")
    webhook_secret: str = Field(..., alias="WEBHOOK_SECRET")
    webhook_url: Optional[AnyHttpUrl] = Field(default=None, alias="WEBHOOK_URL")

    model_config = {
        "extra": "ignore",
        "populate_by_name": True,
    }


class StripeSettings(ProviderSettings):
    """Settings for Stripe integration."""

    account_id: Optional[str] = Field(default=None, alias="ACCOUNT_ID")


class PayPalSettings(ProviderSettings):
    """Settings for PayPal integration."""

    client_id: Optional[str] = Field(default=None, alias="CLIENT_ID")
    client_secret: Optional[str] = Field(default=None, alias="CLIENT_SECRET")


class AuditSettings(BaseSettings):
    """Audit log configuration."""

    sink: str = Field(default="stdout", alias="SINK")
    retention_days: int = Field(default=30, alias="RETENTION_DAYS")

    model_config = {
        "extra": "ignore",
        "populate_by_name": True,
    }


class Settings(BaseSettings):
    """Application settings."""

    environment: str = Field(default="local", alias="ENVIRONMENT")
    service_name: str = Field(default="payment-service", alias="SERVICE_NAME")
    stripe: StripeSettings = Field(default_factory=StripeSettings, alias="STRIPE")
    paypal: PayPalSettings = Field(default_factory=PayPalSettings, alias="PAYPAL")
    audit: AuditSettings = Field(default_factory=AuditSettings, alias="AUDIT")
    sandbox_mode: bool = Field(default=True, alias="SANDBOX_MODE")

    model_config = {
        "extra": "ignore",
        "populate_by_name": True,
        "env_nested_delimiter": "__",
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()


__all__ = ["Settings", "get_settings", "StripeSettings", "PayPalSettings", "AuditSettings"]

