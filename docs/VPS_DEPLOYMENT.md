# VPS Deployment Guide for ICO Atlas V4

This guide details the steps to set up, deploy, and manage the dockerized ICO Atlas V4 stack on a VPS.

## Prerequisites

- Clean Ubuntu VPS (tested on 22.04 LTS or newer)
- Public domains configured (A records) mapping to the VPS IP address:
  - `icoatlas.sk`
  - `api.icoatlas.sk`

## 1. VPS Host Hardening

Update dependencies and install required base packages:

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
  ca-certificates \
  curl \
  gnupg \
  ufw \
  fail2ban \
  git
```

### Configure UFW Firewall

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

### Install Docker Engine

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

---

## 2. Secrets Vault Initialization

Set up the directory structure and create the production `.env` file on the VPS:

```bash
sudo mkdir -p /opt/icoatlas
sudo chown -R $USER:$USER /opt/icoatlas
chmod 700 /opt/icoatlas

# Create production secrets
nano /opt/icoatlas/.env
chmod 600 /opt/icoatlas/.env
```

Ensure `/opt/icoatlas/.env` contains the required domains and environment config:

```env
PUBLIC_APP_DOMAIN=icoatlas.sk
PUBLIC_API_DOMAIN=api.icoatlas.sk
PUBLIC_API_URL=https://api.icoatlas.sk

ENVIRONMENT=production
LOG_LEVEL=info

# Optional provider/API secrets
ICOATLAS_API_KEY=YOUR_PRODUCTION_API_KEY
SENTRY_DSN=
```

---

## 3. Initial Stack Setup & Clone

Clone the repository directly into the `/opt/icoatlas` folder:

```bash
git clone https://github.com/youh4ck3dme/V4-prototype-icoatlas.git /opt/icoatlas
```

---

## 4. Run Build & Startup

Deploy using docker-compose:

```bash
cd /opt/icoatlas
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Verify internal health checks:

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:3000/health
```

---

## 5. Deployment Scripts

Automated deploy and backup scripts are available in the `./scripts` folder.

- **Deploy Script**: `./scripts/deploy-vps.sh` (pulls main branch, builds, starts, and runs health checks).
- **Backup Script**: `./scripts/backup-vps.sh` (creates compressed backup of configuration and `.env` in `/var/backups/icoatlas`).

To schedule automated daily backups, configure a cron job:

```bash
sudo crontab -e
```

Add the following entry to run the backup every night at 2:00 AM:

```txt
0 2 * * * /opt/icoatlas/scripts/backup-vps.sh > /dev/null 2>&1
```

---

## 6. Rollback Protocol

If the deployment has issues, perform a quick rollback:

```bash
cd /opt/icoatlas
git log --oneline -5
git checkout <previous-good-commit-hash>
docker compose build
docker compose up -d
```
