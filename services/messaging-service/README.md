# Messaging Service

The Meetinity messaging service exposes conversation and message APIs aligned with `contracts/openapi.yaml`.

## Endpoints

- `GET /conversations` — list authenticated user's conversations with unread counts.
- `POST /conversations` — create a direct conversation with another participant. Optionally includes an initial message.
- `GET /conversations/{id}/messages` — retrieve the ordered message history for a conversation.
- `POST /conversations/{id}/messages` — send a new message within a conversation.
- `POST /conversations/{id}/read` — mark the conversation as read for the authenticated user.

## Running locally

```bash
pip install -r requirements.txt
FLASK_APP=src.main:create_app FLASK_DEBUG=1 python -m flask run --host=0.0.0.0 --port 8080
```

The service persists data in Postgres when the `DATABASE_URL`/`DB_*` variables are set. Without configuration it falls back to a SQLite database for local experimentation and tests.
