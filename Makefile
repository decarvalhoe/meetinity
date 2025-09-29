DEV_COMPOSE_FILE := docker-compose.dev.yml
DEV_ENV_FILE := .env.dev

.PHONY: dev-up dev-down dev-logs dev-seed

dev-up:
	@if [ ! -f $(DEV_ENV_FILE) ]; then \
		echo "[warn] $(DEV_ENV_FILE) introuvable. Les valeurs par défaut seront utilisées."; \
	fi
	docker compose --env-file $(DEV_ENV_FILE) -f $(DEV_COMPOSE_FILE) up -d --build

dev-down:
	docker compose --env-file $(DEV_ENV_FILE) -f $(DEV_COMPOSE_FILE) down --remove-orphans

dev-logs:
	docker compose --env-file $(DEV_ENV_FILE) -f $(DEV_COMPOSE_FILE) logs -f --tail=100


dev-seed:
	./scripts/dev/seed.sh
