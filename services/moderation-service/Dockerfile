FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=src.main:app \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=8080

EXPOSE 8080

CMD ["flask", "run", "--host=0.0.0.0", "--port", "8080"]
