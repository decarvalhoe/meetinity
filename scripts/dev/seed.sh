#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/docker-compose.dev.yml"
ENV_FILE="${REPO_ROOT}/.env.dev"
COMPOSE_CMD=(docker compose -f "${COMPOSE_FILE}")

if [[ -f "${ENV_FILE}" ]]; then
  COMPOSE_CMD+=(--env-file "${ENV_FILE}")
else
  echo "[info] Aucun fichier .env.dev détecté, les valeurs par défaut seront utilisées." >&2
fi

# Exécute les migrations des services dépendants pour garantir que les tables existent.
for service in user-service event-service matching-service; do
  echo "[seed] Application des migrations pour ${service}"
  "${COMPOSE_CMD[@]}" exec "${service}" alembic upgrade head >/dev/null
done

# Lancement du job de seed dédié (profil 'seed').
echo "[seed] Injection des données de démonstration dans PostgreSQL"
"${COMPOSE_CMD[@]}" --profile seed run --rm seed-data

echo "[seed] Données de démonstration chargées avec succès."
