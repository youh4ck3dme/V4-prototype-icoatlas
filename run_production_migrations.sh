#!/bin/bash
# Run Production Graph DB Migrations
# Safely loops through backend/migrations/*.sql and applies them idempotently
# to the production Postgres database inside the Docker network.

set -e

MIGRATIONS_DIR="backend/migrations"

if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "Error: Migrations directory '$MIGRATIONS_DIR' not found."
    exit 1
fi

echo "Starting migration runner for production database..."

# Ensure we have sql files
shopt -s nullglob
SQL_FILES=("$MIGRATIONS_DIR"/*.sql)

if [ ${#SQL_FILES[@]} -eq 0 ]; then
    echo "No SQL migrations found in $MIGRATIONS_DIR."
    exit 0
fi

# Loop through and apply
for file in "${SQL_FILES[@]}"; do
    echo "Applying migration: $file"
    # Using docker exec -i to stream the sql file directly to psql, 
    # relying on the container's securely injected POSTGRES_USER and POSTGRES_DB env vars.
    docker exec -i icoatlas-db-1 sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1' < "$file"
done

echo "All migrations applied successfully."
