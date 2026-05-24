#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/icoatlas"

echo "== ICO Atlas VPS Deploy =="

if [ ! -f "$APP_DIR/.env" ]; then
  echo "ERROR: Missing $APP_DIR/.env"
  echo "Create it from .env.example and chmod 600 it."
  exit 1
fi

cd "$APP_DIR"

echo "Pulling latest code..."
git fetch origin
git checkout main
git pull origin main

echo "Building containers..."
docker compose build --no-cache

echo "Starting services..."
docker compose up -d backend frontend

echo "Service status:"
docker compose ps

echo "Backend health:"
curl -fsS "http://127.0.0.1:8005/health" || {
  echo "Backend healthcheck failed"
  docker compose logs --tail=100 backend
  exit 1
}

echo "Frontend health:"
curl -fsS "http://127.0.0.1:3005/health" || {
  echo "Frontend healthcheck failed"
  docker compose logs --tail=100 frontend
  exit 1
}

echo "Done."
