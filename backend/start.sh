#!/usr/bin/env bash
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting Celery worker in background..."
celery -A app.worker.celery_app worker --loglevel=info --concurrency=2 &

echo "Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"