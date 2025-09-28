# Service Inventory (docker-compose.dev)

This document captures the development docker-compose stack and highlights build/runtime metadata needed for containerization work.

| Service | Repository / Image | Build Command | Runtime Entrypoint | Environment Variables | System Dependencies |
|---------|--------------------|---------------|--------------------|-----------------------|---------------------|
| `postgres` | `docker.io/postgres:15` | _Prebuilt image (no local build)_ | Default `docker-entrypoint.sh postgres` | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (defaults provided in compose) | Binds `${POSTGRES_PORT:-5432}` to host, persistent volume `postgres-data`, healthcheck `pg_isready`, requires `meetinity-net` bridge |
| `zookeeper` | `docker.io/bitnami/zookeeper:3.9` | _Prebuilt image_ | Bitnami default entrypoint (`/opt/bitnami/scripts/zookeeper/run.sh`) | `ZOO_ENABLE_AUTH=no`, `ALLOW_ANONYMOUS_LOGIN=yes` | Exposes `2181`, mounts `zookeeper-data`, joins `meetinity-net` |
| `kafka` | `docker.io/bitnami/kafka:3.5` | _Prebuilt image_ | Bitnami default entrypoint (`/opt/bitnami/scripts/kafka/run.sh`) | `KAFKA_BROKER_ID=1`, `KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181`, `KAFKA_CFG_LISTENERS=PLAINTEXT://:9092`, `KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092`, `ALLOW_PLAINTEXT_LISTENER=yes` | Maps `${KAFKA_PORT:-9092}`, persistent volume `kafka-data`, depends on `zookeeper`, healthcheck `kafka-topics.sh --list`, network `meetinity-net` |
| `kafka-ui` | `docker.io/provectuslabs/kafka-ui:latest` | _Prebuilt image_ | Default entrypoint (`/docker-entrypoint.sh`) serving web UI | `KAFKA_CLUSTERS_0_NAME=meetinity`, `KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS=kafka:9092` | Publishes `${KAFKA_UI_PORT:-8085}`, depends on healthy `kafka`, network `meetinity-net` |
| `api-gateway` | `../meetinity-api-gateway` (Dockerfile) | `docker build -f Dockerfile ../meetinity-api-gateway` | _Unknown – Dockerfile not available in this repo_ | Loads `.env.dev` (not in repo); runtime variables pending repo access | Binds `${API_GATEWAY_PORT:-8080}`, depends on healthy `postgres` & `kafka`, volume mount `../meetinity-api-gateway:/app`, network `meetinity-net` |
| `user-service` | `../meetinity-user-service` (Dockerfile) | `docker build -f Dockerfile ../meetinity-user-service` | _Unknown – Dockerfile not available in this repo_ | Loads `.env.dev`; service-specific variables need confirmation | Binds `${USER_SERVICE_PORT:-8081}`, depends on healthy `postgres` & `kafka`, volume mount `../meetinity-user-service:/app`, network `meetinity-net` |
| `matching-service` | `../meetinity-matching-service` (Dockerfile) | `docker build -f Dockerfile ../meetinity-matching-service` | _Unknown – Dockerfile not available in this repo_ | Loads `.env.dev`; service-specific variables need confirmation | Binds `${MATCHING_SERVICE_PORT:-8082}`, depends on healthy `postgres` & `kafka`, volume mount `../meetinity-matching-service:/app`, network `meetinity-net` |
| `event-service` | `../meetinity-event-service` (Dockerfile) | `docker build -f Dockerfile ../meetinity-event-service` | _Unknown – Dockerfile not available in this repo_ | Loads `.env.dev`; service-specific variables need confirmation | Binds `${EVENT_SERVICE_PORT:-8083}`, depends on healthy `postgres` & `kafka`, volume mount `../meetinity-event-service:/app`, network `meetinity-net` |

## Notes & Follow-ups
- The application services (`api-gateway`, `user-service`, `matching-service`, `event-service`) reference sibling repositories that are not present in this workspace. Their Dockerfiles, entrypoints, and environment contracts require verification once those repositories are accessible.
- Shared `.env.dev` is referenced for all Meetinity application services but is not committed here; environment variable documentation must be extracted from that file or upstream repos.
- System dependency inventory should be revisited after auditing the missing Dockerfiles to capture package/runtime requirements beyond container ports and volumes.

## External Repository Dockerfile Review
| Repository | Dockerfile Location | Observations | Follow-up |
|------------|---------------------|--------------|-----------|
| `meetinity-api-gateway` | `Dockerfile` at repository root (referenced in compose) | Source repository unavailable in current workspace; unable to confirm build stages, base image hardening, or non-root user usage. | Open TODO/issue in `meetinity-api-gateway` repository to audit Dockerfile for multi-stage build, dependency caching, and runtime user drop once accessible. |
| `meetinity-user-service` | `Dockerfile` at repository root | Repository missing locally; runtime stack, entrypoint, and security posture unknown. | Track follow-up in `meetinity-user-service` repo to review Dockerfile, ensure multi-stage builds, and add non-root execution. |
| `meetinity-matching-service` | `Dockerfile` at repository root | No access to Dockerfile; need to validate dependency installation and runtime entrypoint. | Create TODO in `meetinity-matching-service` project requesting Dockerfile audit aligned with platform standards. |
| `meetinity-event-service` | `Dockerfile` at repository root | Dockerfile not available for review; healthchecks and user permissions remain undocumented. | File issue/PR in `meetinity-event-service` repo to document Dockerfile, add security best practices, and expose health command. |

> _Note_: Links to PRs/TODOs will be added once the corresponding repositories are reachable; placeholders above capture the actions that must be opened externally.
