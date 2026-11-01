# Troubleshooting Guide

Common issues and solutions for ICO Atlas V4.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Service Connection Issues](#service-connection-issues)
- [Runtime Errors](#runtime-errors)
- [Performance Issues](#performance-issues)
- [Data Quality Issues](#data-quality-issues)

---

## Installation Issues

### Python Version Error

**Symptom:**

```text
ERROR: This package requires Python 3.14 or higher
```

**Solution:**

```bash
# Check Python version
python3 --version

# Install Python 3.14+ (macOS)
brew install python@3.14

# Install Python 3.14+ (Linux)
sudo apt install python3.14
```

### Virtual Environment Creation Failed

**Symptom:**

```text
Error: Command '['venv/bin/python3', '-Im', 'ensurepip']' returned non-zero exit status
```

**Solution:**

```bash
# Remove old venv
rm -rf backend/venv

# Create new venv
python3 -m venv backend/venv

# If still fails, install venv package
sudo apt install python3-venv  # Linux
```

### npm Install Fails

**Symptom:**

```text
npm ERR! code EACCES
npm ERR! syscall access
```

**Solution:**

```bash
# Fix npm permissions
sudo chown -R $(whoami) ~/.npm
sudo chown -R $(whoami) /usr/local/lib/node_modules

# Or use nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

---

## Service Connection Issues

### Redis Connection Refused

**Symptom:**

```text
⚠️ Redis nie je dostupný: Error 61 connecting to localhost:6379. Connection refused.
   Používa sa in-memory cache fallback
```

**Impact:** Non-critical. App uses in-memory cache instead.

**Solution (if you want Redis):**

```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt install redis-server
sudo systemctl start redis-server

# Verify
redis-cli ping  # Should return "PONG"
```

### PostgreSQL Connection Error

**Symptom:**

```text
sqlalchemy.exc.OperationalError: could not connect to server
```

**Impact:** Non-critical. App uses SQLite instead.

**Solution (if you want PostgreSQL):**

```bash
# macOS
brew install postgresql@16
brew services start postgresql@16
createdb iluminati_db

# Linux
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb iluminati_db

# Update .env
DATABASE_URL=postgresql://$(whoami)@localhost:5432/iluminati_db
```

### Backend API Not Responding

**Symptom:**

```text
curl: (7) Failed to connect to localhost port 8000: Connection refused
```

**Solution:**

```bash
# Check if backend is running
ps aux | grep uvicorn

# Check logs
tail -f logs/backend.log

# Restart backend
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Can't Connect to Backend

**Symptom:**

```text
Network Error: Failed to fetch
CORS policy: No 'Access-Control-Allow-Origin' header
```

**Solution:**

1. Check backend is running: `curl http://localhost:8000/api/health`

2. Update CORS origins in `backend/.env`:

```bash
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000", "http://localhost:8009"]
```

3. Restart backend

---

## Runtime Errors

### Import Error: Module Not Found

**Symptom:**

```text
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**

```bash
# Ensure venv is activated
cd backend
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; print(fastapi.__version__)"
```

### Database Locked Error

**Symptom:**

```text
sqlite3.OperationalError: database is locked
```

**Solution:**

```bash
# Stop all backend processes
pkill -f "uvicorn main:app"

# Wait a moment
sleep 2

# Restart backend
cd backend && source venv/bin/activate && uvicorn main:app --reload
```

### Port Already in Use

**Symptom:**

```text
ERROR: [Errno 48] Address already in use
```

**Solution:**

```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn main:app --port 8001
```

### JWT Token Expired

**Symptom:**

```text
401 Unauthorized: Token has expired
```

**Solution:**

```bash
# Frontend: Clear localStorage and re-login
localStorage.clear()

# Backend: Increase token expiration in .env
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
```

---

## Performance Issues

### Slow Search Results

**Possible Causes:**

1. No Redis cache (using in-memory)
2. First-time scraping (no cache)
3. External API rate limiting

**Solutions:**

1. **Install Redis for persistent cache:**

```bash
brew install redis && brew services start redis
# Update .env: REDIS_URL=redis://localhost:6379/0
```

2. **Check cache stats:**

```bash
curl http://localhost:8000/api/cache/stats
```

3. **Pre-warm cache for common searches:**

```bash
# Search for popular companies to cache results
curl "http://localhost:8000/api/search?query=36421928&country=SK"
```

### High Memory Usage

**Symptom:** Backend using excessive RAM

**Solutions:**

1. **Clear in-memory cache:**

```bash
# Restart backend
pkill -f uvicorn && cd backend && uvicorn main:app
```

2. **Use Redis instead of in-memory cache**

3. **Reduce cache TTL in code:**

```python
# services/cache.py
DEFAULT_TTL = timedelta(hours=6)  # Reduce from 12
```

### Frontend Build Slow

**Symptom:** `npm run build` takes too long

**Solutions:**

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Use faster package manager
npm install -g pnpm
pnpm install
pnpm build
```

---

## Data Quality Issues

### Company Not Found

**Symptom:** Search returns no results for valid company ID

**Possible Causes:**

1. Company doesn't exist in register
2. Scraping failed
3. API rate limiting

**Solutions:**

1. **Verify company exists:**

   - SK: <https://www.orsr.sk>
   - CZ: <https://ares.gov.cz>
   - PL: <https://ekrs.ms.gov.pl>
   - HU: <https://www.e-cegjegyzek.hu>

2. **Check backend logs:**

```bash
tail -f logs/backend.log | grep -i error
```

3. **Force refresh (bypass cache):**

```bash
curl "http://localhost:8000/api/search?query=36421928&country=SK&force_refresh=true"
```

### Incomplete Company Data

**Symptom:** Missing fields (executives, shareholders, etc.)

**Causes:**

1. Data not available in source register
2. Scraping parser needs update
3. API response format changed

**Solutions:**

1. **Check source register manually**

2. **Enable debug logging:**

```python
# backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

3. **Update parser if needed** (check provider files in `backend/services/`)

### Wrong Risk Score

**Symptom:** Risk score seems incorrect

**Explanation:** Risk scoring is based on:

- Company age
- Legal form
- Debt records
- Financial indicators
- Beneficial ownership

**Solutions:**

1. **Review risk factors:**

```bash
curl http://localhost:8000/api/search?query=36421928&country=SK | jq '.nodes[0].risk_factors'
```

2. **Adjust risk scoring logic in:**
   - `backend/services/risk_intelligence.py`
   - `backend/services/sk_rpo.py`
   - `backend/services/pl_krs.py`
   - `backend/services/hu_nav.py`

---

## Debugging Tips

### Enable Debug Mode

**Backend:**

```bash
# In backend/.env
LOG_LEVEL=DEBUG

# Or run with debug flag
uvicorn main:app --log-level debug
```

**Frontend:**

```javascript
// In browser console
localStorage.setItem("debug", "true");
```

### View API Requests

**Browser DevTools:**

1. Open DevTools (F12)
2. Go to Network tab
3. Filter by "Fetch/XHR"
4. Perform search
5. Click request to see details

**Backend Logs:**

```bash
# Real-time logs
tail -f logs/backend.log

# Search for errors
grep -i error logs/backend.log

# Search for specific company
grep "36421928" logs/backend.log
```

### Test Individual Components

**Backend API:**

```bash
# Health check
curl http://localhost:8000/api/health

# Search endpoint
curl "http://localhost:8000/api/search?query=test&country=SK"

# Cache stats
curl http://localhost:8000/api/cache/stats
```

**Database:**

```bash
# SQLite
sqlite3 backend/sql_app.db "SELECT * FROM company_cache LIMIT 5;"

# PostgreSQL
psql iluminati_db -c "SELECT * FROM company_cache LIMIT 5;"
```

---

## Getting Help

If you're still experiencing issues:

1. **Check logs:** `logs/backend.log` and `logs/frontend.log`
2. **Run health check:** `./check_services.sh`
3. **Review API docs:** <http://localhost:8000/api/docs>
4. **Check GitHub issues:** Search for similar problems
5. **Create new issue:** Include logs, error messages, and steps to reproduce

## Useful Commands

```bash
# Full restart
pkill -f uvicorn && pkill -f vite && ./start_dev.sh

# Check all services
./check_services.sh

# View logs
tail -f logs/*.log

# Clear cache and restart
rm -rf backend/__pycache__ backend/services/__pycache__
pkill -f uvicorn && cd backend && uvicorn main:app

# Reset database
rm backend/sql_app.db
cd backend && python -c "from services.database import init_database; init_database()"

# Fresh install
rm -rf backend/venv frontend/node_modules
# Then follow SETUP.md
```
