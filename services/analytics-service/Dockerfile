# Multi-stage build for Meetinity Analytics Service
FROM python:3.11-slim as builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim as runtime

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN groupadd -r meetinity && useradd -r -g meetinity -s /bin/bash meetinity

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --chown=meetinity:meetinity . .

RUN mkdir -p /app/logs && \
    chown -R meetinity:meetinity /app

USER meetinity

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=src.main:create_app \
    APP_PORT=8080

CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "src.main:create_app()"]
