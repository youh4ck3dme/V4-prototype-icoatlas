#!/bin/bash
# Backup Production Postgres Database
# Outputs a timestamped .sql.gz file without printing secrets.

set -e

BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/icoatlas_db_${TIMESTAMP}.sql.gz"

echo "Starting production database backup..."

# Use docker exec to run pg_dump inside the container. 
# It relies on the environment variables already securely injected by Docker Compose.
docker exec -i icoatlas-db-1 sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -F p' | gzip > "$BACKUP_FILE"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "Backup completed successfully: $BACKUP_FILE"
else
    echo "Backup failed!"
    rm -f "$BACKUP_FILE"
    exit 1
fi
