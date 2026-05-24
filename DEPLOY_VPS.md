# V4 ICO Atlas – VPS Deployment Runbook

> **Target server:** `tapfast` · IPv4 `194.182.87.6` · Ubuntu 24.04 LTS

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Install Docker & Docker Compose](#2-install-docker--docker-compose)
3. [Firewall setup (ufw)](#3-firewall-setup-ufw)
4. [Clone the repository](#4-clone-the-repository)
5. [Configure environment](#5-configure-environment)
6. [Build and start the stack](#6-build-and-start-the-stack)
7. [Smoke tests](#7-smoke-tests)
8. [Enable TLS with Let's Encrypt](#8-enable-tls-with-lets-encrypt)
9. [Autostart with systemd](#9-autostart-with-systemd)
10. [Updating the application](#10-updating-the-application)
11. [Rollback](#11-rollback)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

| Item | Version |
|------|---------|
| Ubuntu | 24.04 LTS |
| Docker Engine | 26+ |
| Docker Compose plugin | v2.27+ |
| Git | 2.x |
| (Optional) Domain | pointed to `194.182.87.6` |

All commands below are run as a non-root user with `sudo` access.

---

## 2. Install Docker & Docker Compose

```bash
# Remove any old Docker packages
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Install dependencies
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key and repo
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine + Compose plugin
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
                        docker-buildx-plugin docker-compose-plugin

# Allow current user to run Docker without sudo
sudo usermod -aG docker "$USER"
newgrp docker            # reload group in current session

# Verify
docker --version
docker compose version
```

---

## 3. Firewall setup (ufw)

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status
```

> **Note:** Ports 5432 (Postgres) and 6379 (Redis) are **not** opened — they are
> accessible only inside the Docker network.

---

## 4. Clone the repository

```bash
# Install to /opt for system-wide access
sudo mkdir -p /opt/v4-icoatlas
sudo chown "$USER":"$USER" /opt/v4-icoatlas

git clone https://github.com/youh4ck3dme/V4-prototype-icoatlas.git /opt/v4-icoatlas
cd /opt/v4-icoatlas
```

---

## 5. Configure environment

```bash
cd /opt/v4-icoatlas

# Create the production env file from the template
cp .env.production.example .env.production

# Edit and fill in all secrets
nano .env.production
```

**Minimum required values to change:**

| Variable | Action |
|----------|--------|
| `POSTGRES_PASSWORD` | `openssl rand -hex 32` |
| `SECRET_KEY` | `openssl rand -hex 32` |
| `CORS_ORIGINS` | Your domain, e.g. `https://yourdomain.com` (or `http://194.182.87.6` if no domain) |
| `VITE_API_URL` | `/api` (default, leave as-is when nginx is on the same host) |

```bash
# Verify no placeholder remains
grep "CHANGE_ME" .env.production && echo "⚠ Fill in all CHANGE_ME values!" || echo "✓ Looks good"
```

---

## 6. Build and start the stack

```bash
cd /opt/v4-icoatlas

# Build images and start all services in detached mode
docker compose -f docker-compose.prod.yml up -d --build

# Watch logs during first start
docker compose -f docker-compose.prod.yml logs -f
```

Expected output – all four containers should reach "healthy" / "running":

```
backend-1   | [gunicorn] Booting worker with pid: ...
frontend-1  | /docker-entrypoint.sh: Configuration complete; ready for start up
nginx-1     | ... start worker processes
db-1        | database system is ready to accept connections
redis-1     | Ready to accept connections
```

---

## 7. Smoke tests

Replace `194.182.87.6` with your domain if you have one.

```bash
# 1. Backend health check
curl -s http://194.182.87.6/health | python3 -m json.tool
# Expected: {"status": "ok", "env": "production", ...}

# 2. API responds
curl -s http://194.182.87.6/api/
# Expected: JSON (FastAPI root or 404 with detail)

# 3. Frontend loads
curl -sI http://194.182.87.6/ | grep "HTTP/"
# Expected: HTTP/1.1 200 OK

# 4. Container health status
docker compose -f docker-compose.prod.yml ps
# All services should show "healthy" or "running"
```

---

## 8. Enable TLS with Let's Encrypt

> Requires a domain name pointing to `194.182.87.6` via DNS A record.

### 8a. Install certbot

```bash
sudo apt-get install -y certbot
```

### 8b. Obtain a certificate (standalone, port 80 must be free)

```bash
# Temporarily stop nginx to free port 80
docker compose -f /opt/v4-icoatlas/docker-compose.prod.yml stop nginx

# Get certificate
sudo certbot certonly --standalone \
  -d yourdomain.com -d www.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos --non-interactive

# Restart nginx
docker compose -f /opt/v4-icoatlas/docker-compose.prod.yml start nginx
```

### 8c. Enable HTTPS in nginx config

Edit `deploy/nginx/default.conf` and uncomment the HTTPS server block at the
bottom of the file, then replace `yourdomain.com` with your actual domain.

```bash
nano /opt/v4-icoatlas/deploy/nginx/default.conf
```

Also update `CORS_ORIGINS` in `.env.production` to use `https://`.

Reload nginx:

```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### 8d. Auto-renew (cron)

```bash
# Test renewal
sudo certbot renew --dry-run

# Add renewal cron (runs twice daily)
echo "0 3,15 * * * root certbot renew --quiet --post-hook \
  'docker compose -f /opt/v4-icoatlas/docker-compose.prod.yml exec nginx nginx -s reload'" \
  | sudo tee /etc/cron.d/certbot-renew
```

---

## 9. Autostart with systemd

The service file in `deploy/systemd/v4-icoatlas.service` starts Docker Compose
automatically on boot.

```bash
# Install the service
sudo cp /opt/v4-icoatlas/deploy/systemd/v4-icoatlas.service \
        /etc/systemd/system/v4-icoatlas.service

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable v4-icoatlas.service
sudo systemctl start  v4-icoatlas.service

# Check status
sudo systemctl status v4-icoatlas.service
```

---

## 10. Updating the application

```bash
cd /opt/v4-icoatlas

# Pull latest code
git pull origin main

# Rebuild changed images and restart (zero-downtime as much as possible)
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans

# Remove dangling images to free disk space
docker image prune -f
```

---

## 11. Rollback

### Option A – Roll back to a specific git commit

```bash
cd /opt/v4-icoatlas

# Find the commit to roll back to
git log --oneline -10

# Check out that commit
git checkout <commit-sha>

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build
```

### Option B – Roll back to a previous Docker image

Docker Compose keeps the previously built image until `docker image prune` is
run. To restart with the old image without rebuilding:

```bash
# Stop current stack
docker compose -f docker-compose.prod.yml down

# Re-tag or use the previous image ID
docker images | grep v4-icoatlas

# Start without --build to use the cached (previous) image
docker compose -f docker-compose.prod.yml up -d
```

---

## 12. Troubleshooting

### View logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Single service
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Container won't start / health-check failing

```bash
# Inspect health details
docker inspect v4-icoatlas-backend-1 | python3 -m json.tool | grep -A 20 '"Health"'

# Open a shell inside the container
docker compose -f docker-compose.prod.yml exec backend /bin/sh
```

### Postgres connection refused

```bash
# Check if db container is healthy
docker compose -f docker-compose.prod.yml ps db

# Check POSTGRES_PASSWORD matches in .env.production
grep POSTGRES_PASSWORD .env.production
```

### nginx 502 Bad Gateway

Usually means the backend or frontend container is not running/healthy.

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs backend
```

### Rebuild from scratch (data loss – use with care)

```bash
docker compose -f docker-compose.prod.yml down -v   # removes volumes!
docker compose -f docker-compose.prod.yml up -d --build
```

---

*Generated for server `tapfast` (194.182.87.6) · Ubuntu 24.04 LTS*
