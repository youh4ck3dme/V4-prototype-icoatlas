# ICO Atlas V4 - Setup Guide

Complete setup instructions for the ICO Atlas V4 project.

## Prerequisites

### Required

- **Python 3.14+** - Backend runtime
- **Node.js 18+** - Frontend build tools
- **npm or yarn** - Package manager

### Optional (Recommended for Production)

- **Redis 7+** - Caching layer (fallback: in-memory cache)
- **PostgreSQL 16+** - Database (fallback: SQLite)

## Quick Start (Development)

### 1. Clone Repository

```bash
git clone <repository-url>
cd V4-prototype-icoatlas
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env

# Generate secret key
python -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')" >> .env

# Initialize database
python -c "from services.database import init_database; init_database()"
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Create .env file (optional)
echo "VITE_API_URL=http://localhost:8000" > .env
```

### 4. Start Application

**Option A: Manual Start (Two Terminals)**

Terminal 1 - Backend:

```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 - Frontend:

```bash
cd frontend
npm run dev
```

**Option B: Using Start Script**

```bash
chmod +x start_dev.sh
./start_dev.sh
```

### 5. Access Application

- **Frontend**: http://localhost:5173 (or port shown in terminal)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

## Optional: Install Redis & PostgreSQL

### macOS (Homebrew)

```bash
# Install services
brew install redis postgresql@16

# Start services
brew services start redis
brew services start postgresql@16

# Create database
createdb iluminati_db

# Update .env
DATABASE_URL=postgresql://$(whoami)@localhost:5432/iluminati_db
REDIS_URL=redis://localhost:6379/0
```

### Linux (Ubuntu/Debian)

```bash
# Install services
sudo apt update
sudo apt install redis-server postgresql postgresql-contrib

# Start services
sudo systemctl start redis-server
sudo systemctl start postgresql

# Create database
sudo -u postgres createdb iluminati_db
sudo -u postgres createuser $(whoami)

# Update .env
DATABASE_URL=postgresql://$(whoami)@localhost:5432/iluminati_db
REDIS_URL=redis://localhost:6379/0
```

### Docker (All Platforms)

```bash
# Start Redis and PostgreSQL
docker-compose up -d redis postgres

# Services will be available at:
# Redis: localhost:6379
# PostgreSQL: localhost:5432
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Required Settings:**

- `SECRET_KEY` - JWT secret (generate with `openssl rand -hex 32`)
- `DATABASE_URL` - Database connection string

**Optional Settings:**

- `REDIS_URL` - Redis connection string
- `CORS_ORIGINS` - Allowed frontend origins
- `SENTRY_DSN` - Backend Sentry DSN for error tracking
- `SENTRY_TRACES_SAMPLE_RATE` - Sentry traces sample rate (0.0 to 1.0)
- `VITE_SENTRY_DSN` - Frontend Sentry DSN for error tracking
- `VITE_SENTRY_TRACES_SAMPLE_RATE` - Frontend Sentry traces sample rate
- `GRAFANA_PASSWORD` - Grafana admin password
- External API keys for enhanced data

See `.env.example` for all available options.

## Database Migrations

### Initialize Database

```bash
cd backend
source venv/bin/activate
python -c "from services.database import init_database; init_database()"
```

### Run Migrations (if using Alembic)

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

## Verification

### Check Services

```bash
chmod +x check_services.sh
./check_services.sh
```

### Test Backend

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{
  "status": "healthy",
  "cache": {"redis_enabled": false, "in_memory": {...}},
  "features": {...}
}
```

### Test Frontend

Open http://localhost:5173 in browser and try searching for a company.

## Development Workflow

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run with auto-reload
uvicorn main:app --reload

# Run tests
pytest

# Run with coverage
pytest --cov=services --cov-report=html
```

### Frontend Development

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm test
```

## Monitoring Setup (Optional)

The project includes Sentry error tracking and Prometheus metrics collection.

### Sentry

1. Create projects at https://sentry.io for backend (FastAPI) and frontend (React).
2. Add DSN values to `.env`:
   ```bash
   SENTRY_DSN=https://your-backend-key@sentry.io/project-id
   VITE_SENTRY_DSN=https://your-frontend-key@sentry.io/project-id
   ```

### Prometheus & Grafana

```bash
# Start Prometheus and Grafana
docker-compose -f docker-compose.monitoring.yml up -d
```

- **Prometheus UI**: http://localhost:9090
- **Grafana UI**: http://localhost:3001 (default: `admin`/`admin`)

### Verify Monitoring

```bash
# Check metrics endpoint
curl http://localhost:8000/api/metrics

# Check health endpoint
curl http://localhost:8000/health/detailed
```

For full monitoring documentation, see [MONITORING.md](MONITORING.md).

## Production Deployment

### Build Frontend

```bash
cd frontend
npm run build
# Output: dist/ directory
```

### Run Backend (Production)

```bash
cd backend
source venv/bin/activate

# With Gunicorn (recommended)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or with Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Environment

- Set `ENVIRONMENT=production` in `.env`
- Use PostgreSQL instead of SQLite
- Use Redis for caching
- Configure proper CORS origins
- Use strong SECRET_KEY
- Enable HTTPS

## Troubleshooting

### Redis Connection Refused

**Symptom**: Warning message about Redis not being available

**Solution**: This is normal if Redis is not installed. The app will use in-memory cache.

To install Redis:

```bash
# macOS
brew install redis && brew services start redis

# Linux
sudo apt install redis-server && sudo systemctl start redis-server
```

### PostgreSQL Connection Error

**Symptom**: Database connection errors

**Solution**: The app will fallback to SQLite. To use PostgreSQL:

1. Install PostgreSQL
2. Create database: `createdb iluminati_db`
3. Update `DATABASE_URL` in `.env`

### Port Already in Use

**Symptom**: `Address already in use` error

**Solution**:

```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn main:app --port 8001
```

### CORS Errors

**Symptom**: Frontend can't connect to backend

**Solution**: Add frontend URL to `CORS_ORIGINS` in `.env`:

```bash
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

### Import Errors

**Symptom**: `ModuleNotFoundError`

**Solution**:

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Additional Resources

- **API Documentation**: http://localhost:8000/api/docs
- **Monitoring Guide**: [MONITORING.md](MONITORING.md)
- **Project README**: [README.md](README.md)
- **Troubleshooting Guide**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Architecture Overview**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Support

For issues and questions:

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review API documentation at `/api/docs`
3. Check application logs
4. Open an issue on GitHub
