# Testing Guide

This document explains how to run the end-to-end integration suite that exercises the Meetinity microservices stack through the API gateway.

## Prerequisites

Make sure the following tooling is available locally:

- Docker Engine 24+ with Compose v2 (`docker compose` CLI)
- Python 3.11 or newer
- `pip` to install Python testing dependencies
- Available local ports `5432`, `8080`–`8084`, and `8089` (the Docker stack binds to these during tests)

Before running the suite, install the minimal Python dependencies used by the tests:

```bash
pip install pytest requests PyJWT
```

## Running the integration suite

1. From the repository root, execute the integration tests with pytest:

   ```bash
   pytest -m integration tests/integration -vv
   ```

   The session-scoped fixture defined in `tests/integration/conftest.py` will:

   - Build the service images referenced by `docker-compose.dev.yml`
   - Start the required containers (Postgres, Kafka, User, Event, Matching services, and the API gateway)
   - Seed deterministic reference data using `scripts/dev/sql/seed.sql`
   - Wait for the HTTP health checks on each service before executing the tests

2. After the suite completes, the fixture automatically tears down the stack with `docker compose down -v --remove-orphans`.

### Running individual flows

Each test covers a key user journey:

- `test_login_flow_through_gateway` posts a JWT to `/api/auth/verify` via the gateway and asserts the token is accepted.
- `test_event_registration_roundtrip` registers, lists, and cancels an event registration through the gateway, verifying the registration service behaviour.
- `test_swipe_flow_triggers_match` records a like swipe and asserts the matching service detects the existing mutual match.

You can execute a single test while still reusing the fixture-managed stack:

```bash
pytest tests/integration/test_flows.py::test_swipe_flow_triggers_match -vv
```

## Troubleshooting

| Symptom | Likely cause | Suggested fix |
| --- | --- | --- |
| `docker: command not found` or `Cannot connect to the Docker daemon` | Docker Engine is not installed or not running | Install/start Docker or run the suite on a host with Docker available |
| `Timed out waiting for service at http://localhost:8080/health` | Containers are still starting, or a previous run left ports bound | Retry the test after `docker compose down -v`; ensure no conflicting local services use the same ports |
| `duplicate key value violates unique constraint` during seeding | Database volume persisted between runs | Remove the `meetinity_integration` volumes with `docker compose -f docker-compose.dev.yml down -v --remove-orphans` |
| `pytest` cannot import `jwt` | `PyJWT` dependency missing | Re-run `pip install pytest requests PyJWT` |

If you need to inspect container logs while the suite is running, open a separate terminal and run:

```bash
docker compose -f docker-compose.dev.yml logs -f api-gateway user-service event-service matching-service
```

## Continuous integration

The GitHub Actions workflow (`.github/workflows/ci.yml`) now contains an `Integration Tests` job that provisions the same stack and executes `pytest -m integration` automatically on pull requests.

