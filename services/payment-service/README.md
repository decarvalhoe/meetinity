# Payment Service

This service provides subscription lifecycle orchestration, invoicing, refunds, and
payment provider webhooks for Meetinity. It exposes a FastAPI application with
sandbox implementations of Stripe and PayPal adapters. The service focuses on
structured audit logging and predictable reconciliation hooks so that it can be
safely rolled out before production credentials are available.

## Features

- REST endpoints for subscription creation/cancellation, invoice generation, and
  refund processing.
- Sandbox Stripe and PayPal adapters using shared interfaces to ease future SDK
  integrations.
- Structured audit logging via `structlog` with environment metadata.
- In-memory repositories suitable for contract and sandbox integration tests.
- Configuration provided through environment variables (compatible with
  External Secrets).

## Running locally

```bash
pip install -r requirements.txt
uvicorn payment_service.app:app --reload --port 8080
```

## Environment variables

The service expects provider secrets to be mounted as environment variables
using the `STRIPE__*` and `PAYPAL__*` prefixes. When deployed, these are sourced
from External Secrets backed by Vault.

## API surface

The FastAPI OpenAPI specification can be generated via:

```bash
python -m payment_service.app --generate-openapi
```

Alternatively, run the service locally and visit `/docs` for interactive API
exploration.
