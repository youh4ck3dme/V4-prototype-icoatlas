# ICO Atlas Production Operations Guide

This document outlines the standard operational procedures for managing the production Graph Database.

## 1. Running Migrations Safely

To ensure the production Graph Database schema is up to date, run the safe migration runner script. This script automatically loops through all SQL files in `backend/migrations/` and applies them to the production database securely.

### Command
```bash
./run_production_migrations.sh
```

**How it works:**
- It uses `docker exec` to execute the SQL files against the running `icoatlas-db-1` container.
- It dynamically reads the secure credentials (`POSTGRES_USER` and `POSTGRES_DB`) already present in the container's environment. No secrets are ever printed or passed via CLI args.
- All migration scripts are written to be **idempotent** (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`), meaning you can run this script repeatedly without destroying existing data.

## 2. Backing up the Database

To create a secure, compressed snapshot of the production database without exposing credentials:

### Command
```bash
./backup_production_db.sh
```

**How it works:**
- Runs `pg_dump` securely inside the docker network.
- Compresses the output into a timestamped file format: `backups/icoatlas_db_YYYYMMDD_HHMMSS.sql.gz`.
- The backup is stored on the host filesystem and can be transferred safely.

## 3. Verifying the Graph DB

After deployments or migrations, verify the health and connectivity of the backend and the Graph DB using standard cURL commands:

**Check Health:**
```bash
curl -k "https://api.icoatlas.sk/health"
# Expected: {"status":"ok","env":"production","version":"5.0.0"}
```

**Check Graph Search Endpoint:**
```bash
curl -k "https://api.icoatlas.sk/api/v4/search/31677517?country=SK&graph=1"
```
**Expected Outcome:**
You should see a full JSON response containing the company data. At the end of the JSON, the `graph` object must contain `nodes` and `edges` (or be an empty structure if no relationships exist), but it **MUST NOT** contain `connection to server at "127.0.0.1" failed` or `relation "graph_nodes" does not exist`.

## 4. Deployment Process

### Frontend deploy:
1. **Locally:**
   ```bash
   cd frontend
   npm run build
   cd ..
   git status
   git add frontend/src frontend/Dockerfile.prod PRODUCTION_OPS_GUIDE.md
   git commit -m "fix(frontend): improve mobile and iPhone responsiveness"
   git push origin main
   ```
2. **On VPS:**
   ```bash
   ssh fantastic4-vps
   cd /opt/icoatlas
   git pull origin main
   docker compose -f docker-compose.prod.yml build frontend
   docker compose -f docker-compose.prod.yml up -d --no-deps frontend nginx
   ```
3. **Smoke test:**
   ```bash
   curl -I https://icoatlas.sk
   curl -s -k https://api.icoatlas.sk/health
   ```

### Backend deploy:
1. **On VPS:**
   ```bash
   ssh fantastic4-vps
   cd /opt/icoatlas
   ./backup_production_db.sh
   git pull origin main
   ./run_production_migrations.sh
   docker compose -f docker-compose.prod.yml build backend
   docker compose -f docker-compose.prod.yml up -d --no-deps backend
   ```
2. **Verification:**
   ```bash
   curl -s -k https://api.icoatlas.sk/health
   curl -s -k "https://api.icoatlas.sk/api/v4/search/31677517?country=SK&graph=1"
   ```

### Emergency rollback:
1. **On VPS:**
   ```bash
   ssh fantastic4-vps
   cd /opt/icoatlas
   git log --oneline -10
   git checkout <previous-good-commit>
   docker compose -f docker-compose.prod.yml build frontend
   docker compose -f docker-compose.prod.yml up -d --no-deps frontend nginx
   ```
