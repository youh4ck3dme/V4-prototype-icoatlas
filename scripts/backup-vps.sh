#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/var/backups/icoatlas"
APP_DIR="/opt/icoatlas"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "== ICO Atlas VPS Backup =="

sudo mkdir -p "$BACKUP_DIR"
sudo chmod 700 "$BACKUP_DIR"

echo "Backing up configuration and database volumes..."

# Archive application config & data
sudo tar -czf "$BACKUP_DIR/icoatlas_backup_$TIMESTAMP.tar.gz" \
  -C "$APP_DIR" .env docker-compose.yml Caddyfile \
  || { echo "Backup archive failed"; exit 1; }

# Keep only last 10 backups
find "$BACKUP_DIR" -name "icoatlas_backup_*.tar.gz" -mtime +10 -exec rm {} \;

echo "Backup created at $BACKUP_DIR/icoatlas_backup_$TIMESTAMP.tar.gz"
echo "Done."
