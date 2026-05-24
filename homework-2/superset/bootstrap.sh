#!/usr/bin/env bash
set -e

pip install --no-cache-dir psycopg2-binary >/dev/null 2>&1 || true

superset db upgrade

superset fab create-admin \
    --username "${ADMIN_USERNAME:-admin}" \
    --firstname Admin \
    --lastname User \
    --email "${ADMIN_EMAIL:-admin@example.com}" \
    --password "${ADMIN_PASSWORD:-admin}" || true

superset init

exec gunicorn \
    --bind "0.0.0.0:8088" \
    --workers 4 \
    --worker-class gthread \
    --threads 20 \
    --timeout 60 \
    --keep-alive 2 \
    "superset.app:create_app()"
