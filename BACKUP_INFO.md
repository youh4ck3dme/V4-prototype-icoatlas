# Backup Information

## Latest Backup

**Date:** 2025-12-21 13:01:23  
**File:** `V4-prototype-icoatlas-backup-20251221_130123.tar.gz`  
**Size:** 2.2 MB  
**Location:** `~/Desktop/`

## What's Included in Backup

### Source Code

- ✅ Backend (Python/FastAPI) - 38 services
- ✅ Frontend (React/Vite) - 17+ components
- ✅ Routers (v4, auth, api_keys)
- ✅ V4 Clients (SK, CZ, PL, HU)
- ✅ ERP Integrations (SAP, Pohoda, Money S3)

### Configuration

- ✅ `.env.example` - Environment template
- ✅ `requirements.txt` - Python dependencies
- ✅ `package.json` - Node dependencies
- ✅ `docker-compose.yml` - Docker configuration
- ✅ All config files

### Documentation

- ✅ `README.md` - Main documentation
- ✅ `SETUP.md` - Setup guide
- ✅ `TROUBLESHOOTING.md` - Troubleshooting
- ✅ `docs/` - 25+ documentation files

### Scripts

- ✅ `check_services.sh` - Health check
- ✅ `start_dev.sh` - Development startup
- ✅ `install_services.sh` - Services installer
- ✅ `create_backup.sh` - Backup script
- ✅ All utility scripts

### Templates & Data

- ✅ JSON templates (SK, CZ, PL, HU)
- ✅ Example data files
- ✅ Database schema
- ✅ Migrations

### Tests

- ✅ Backend tests (13 files)
- ✅ Integration tests
- ✅ Test configuration

## What's Excluded

To keep backup size small, the following are excluded:

- ❌ `node_modules/` - Can be reinstalled with `npm install`
- ❌ `venv/` - Can be recreated with `python -m venv venv`
- ❌ `__pycache__/` - Python cache (auto-generated)
- ❌ `dist/` - Build output (can be rebuilt)
- ❌ `*.log` - Log files
- ❌ `.coverage` - Test coverage data

## How to Restore

### Quick Restore (Automated)

```bash
# Run the restore script
~/Desktop/V4-prototype-icoatlas-backup-20251221_130123-restore.sh
```

### Manual Restore

```bash
# 1. Extract backup
cd ~/Downloads
tar -xzf ~/Desktop/V4-prototype-icoatlas-backup-20251221_130123.tar.gz
cd V4-prototype-icoatlas

# 2. Install backend dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Install frontend dependencies
cd ../frontend
npm install

# 4. Configure environment
cd ..
cp .env.example backend/.env
# Edit backend/.env with your settings

# 5. Start application
./start_dev.sh
```

## Creating New Backups

### Using Backup Script

```bash
./create_backup.sh
```

This will create:

- Compressed archive (`.tar.gz`)
- Info file (`.info`)
- Restore script (`-restore.sh`)

All files saved to: `~/Desktop/ICO-Atlas-Backups/`

### Manual Backup

```bash
tar -czf backup-$(date +%Y%m%d).tar.gz \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    .
```

## Backup Best Practices

1. **Regular Backups**

   - Create backup before major changes
   - Weekly backups recommended
   - Before deployment to production

2. **Multiple Locations**

   - Keep backup on Desktop
   - Upload to cloud storage (Google Drive, Dropbox)
   - Store on external drive

3. **Version Control**

   - Use git for code versioning
   - Commit regularly
   - Push to remote repository

4. **Test Restores**
   - Periodically test restore process
   - Verify backup integrity
   - Ensure all dependencies install correctly

## Backup History

| Date             | File                                                | Size   | Location   |
| ---------------- | --------------------------------------------------- | ------ | ---------- |
| 2025-12-21 13:01 | V4-prototype-icoatlas-backup-20251221_130123.tar.gz | 2.2 MB | ~/Desktop/ |

## Emergency Recovery

If something goes wrong:

1. **Stop all services**

   ```bash
   pkill -f uvicorn
   pkill -f vite
   ```

2. **Restore from backup**

   ```bash
   ~/Desktop/V4-prototype-icoatlas-backup-TIMESTAMP-restore.sh
   ```

3. **Verify restoration**

   ```bash
   cd restored-directory
   ./check_services.sh
   ```

4. **Start application**
   ```bash
   ./start_dev.sh
   ```

## Additional Backup Options

### Git Backup

```bash
# Commit all changes
git add .
git commit -m "Backup: $(date)"

# Push to remote (if configured)
git push origin main
```

### Database Backup

```bash
# SQLite
cp backend/sql_app.db backend/sql_app.db.backup

# PostgreSQL (if using)
pg_dump iluminati_db > backup.sql
```

### Environment Backup

```bash
# Backup .env file separately (contains secrets)
cp backend/.env backend/.env.backup.$(date +%Y%m%d)
```

## Cloud Storage Recommendations

1. **Google Drive**

   - Install Google Drive desktop app
   - Move backup to Google Drive folder
   - Automatic sync

2. **Dropbox**

   - Similar to Google Drive
   - Good for team sharing

3. **GitHub Private Repo**

   - Create private repository
   - Push code regularly
   - Free for personal use

4. **External Drive**
   - Copy backup to USB drive
   - Store in safe location
   - Update monthly

## Support

If you need help restoring:

1. Check `TROUBLESHOOTING.md`
2. Review `SETUP.md`
3. Run `./check_services.sh` to diagnose issues

---

**Last Updated:** 2025-12-21 13:01:23  
**Backup Script Version:** 1.0
