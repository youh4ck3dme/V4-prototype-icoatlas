# Monitoring Guide - Sentry & Prometheus

This guide explains how to set up and use the monitoring infrastructure for the ILUMINATI SYSTEM v5.

## Overview

The monitoring stack consists of:
- **Sentry**: Error tracking and performance monitoring for backend and frontend
- **Prometheus**: Metrics collection and time-series database
- **Grafana**: Metrics visualization and dashboards

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Sentry Setup](#sentry-setup)
3. [Prometheus & Grafana Setup](#prometheus--grafana-setup)
4. [Backend Monitoring](#backend-monitoring)
5. [Frontend Monitoring](#frontend-monitoring)
6. [Available Metrics](#available-metrics)
7. [Health Checks](#health-checks)
8. [Grafana Dashboards](#grafana-dashboards)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker and Docker Compose installed
- Sentry account (free tier available at https://sentry.io)
- Backend and frontend applications running

## Sentry Setup

### 1. Create Sentry Projects

1. Sign up at https://sentry.io (or use your existing account)
2. Create two projects:
   - **Backend Project**: Select "FastAPI" as platform
   - **Frontend Project**: Select "React" as platform

### 2. Get DSN Keys

After creating projects, copy the DSN (Data Source Name) for each:
- Backend DSN: Found in Settings → Projects → [Your Backend Project] → Client Keys (DSN)
- Frontend DSN: Found in Settings → Projects → [Your Frontend Project] → Client Keys (DSN)

### 3. Configure Environment Variables

Update your `.env` file (create from `.env.example` if needed):

```bash
# Backend Sentry
SENTRY_DSN=https://[YOUR_BACKEND_KEY]@[SENTRY_ORG].ingest.sentry.io/[PROJECT_ID]
SENTRY_TRACES_SAMPLE_RATE=0.1

# Frontend Sentry
VITE_SENTRY_DSN=https://[YOUR_FRONTEND_KEY]@[SENTRY_ORG].ingest.sentry.io/[PROJECT_ID]
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1
```

**Note**: `TRACES_SAMPLE_RATE` controls the percentage of transactions sent to Sentry:
- `0.1` = 10% (recommended for production)
- `1.0` = 100% (recommended for development)
- `0.0` = disabled

### 4. Verify Sentry Integration

Backend:
```bash
cd backend
python -c "import sentry_sdk; sentry_sdk.init(dsn='YOUR_DSN'); sentry_sdk.capture_message('Test message')"
```

Frontend: The frontend will automatically initialize Sentry on startup. Check browser console for "Sentry initialized successfully".

## Prometheus & Grafana Setup

### 1. Start Monitoring Stack

```bash
# Start Prometheus and Grafana
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services are running
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Access Services

- **Prometheus UI**: http://localhost:9090
- **Grafana UI**: http://localhost:3001
  - Default username: `admin`
  - Default password: `admin` (or value from `GRAFANA_PASSWORD` env var)

### 3. Configure Grafana

1. Open Grafana at http://localhost:3001
2. Log in with admin credentials
3. Add Prometheus data source:
   - Go to Configuration → Data Sources → Add data source
   - Select "Prometheus"
   - URL: `http://prometheus:9090`
   - Click "Save & Test"

## Backend Monitoring

### Available Endpoints

#### Metrics Endpoint
```
GET /api/metrics
```
Returns Prometheus-formatted metrics for scraping.

#### Health Check Endpoints
```
GET /health
```
Basic health check returning status, environment, and version.

```
GET /health/detailed
```
Detailed health check including:
- Database connectivity
- Redis connectivity
- Sentry configuration status
- External APIs availability

### Monitored Metrics

The backend automatically tracks:

1. **HTTP Requests**: Total count by method, endpoint, and status
2. **Request Latency**: Response time distribution
3. **Search Requests**: Count by country and status
4. **Cache Performance**: Hits and misses
5. **Active Connections**: Current number of active connections
6. **Database Queries**: Count and latency by operation

### Using Monitoring in Code

```python
from app.core.monitoring import (
    capture_exception,
    capture_message,
    SEARCH_COUNT,
    CACHE_HITS,
    CACHE_MISSES
)

# Capture an exception
try:
    # Your code
    pass
except Exception as e:
    capture_exception(e, context={"user_id": "123"})

# Capture a message
capture_message("Important event occurred", level="warning")

# Increment metrics
SEARCH_COUNT.labels(country="CZ", status="success").inc()
CACHE_HITS.inc()
```

## Frontend Monitoring

### Initialization

Sentry is automatically initialized in `frontend/src/main.jsx`.

### Error Boundary

The app uses a React Error Boundary to catch rendering errors:

```jsx
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      {/* Your app components */}
    </ErrorBoundary>
  );
}
```

### Using Monitoring in Code

```javascript
import {
  captureException,
  captureMessage,
  setUser,
  addBreadcrumb
} from './utils/monitoring';

// Capture an exception
try {
  // Your code
} catch (error) {
  captureException(error, {
    extra: { userId: user.id }
  });
}

// Capture a message
captureMessage('User performed action', 'info');

// Set user context
setUser({
  id: user.id,
  email: user.email,
  username: user.username
});

// Add breadcrumb
addBreadcrumb({
  message: 'User clicked button',
  category: 'ui.click',
  level: 'info',
  data: { buttonId: 'submit' }
});
```

## Available Metrics

### HTTP Metrics

- `http_requests_total`: Total HTTP requests (labels: method, endpoint, status)
- `http_request_duration_seconds`: Request latency histogram (labels: method, endpoint)
- `active_connections`: Current active connections

### Application Metrics

- `search_requests_total`: Search requests count (labels: country, status)
- `cache_hits_total`: Cache hit count
- `cache_misses_total`: Cache miss count

### Database Metrics

- `db_queries_total`: Database queries count (labels: operation)
- `db_query_duration_seconds`: Database query latency (labels: operation)

## Health Checks

### Basic Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "env": "development",
  "version": "5.0.0"
}
```

### Detailed Health Check

```bash
curl http://localhost:8000/health/detailed
```

Response:
```json
{
  "status": "ok",
  "env": "development",
  "version": "5.0.0",
  "checks": {
    "database": {
      "status": "ok",
      "message": "Database is reachable"
    },
    "redis": {
      "status": "ok",
      "message": "Redis is reachable"
    },
    "sentry": {
      "status": "ok",
      "message": "Sentry is configured"
    },
    "external_apis": {
      "ares": {
        "status": "ok",
        "message": "ARES is reachable"
      },
      "krs": {
        "status": "ok",
        "message": "KRS is reachable"
      }
    }
  }
}
```

## Grafana Dashboards

### Creating a Dashboard

1. Open Grafana at http://localhost:3001
2. Click "+" → "Dashboard" → "Add new panel"
3. Select Prometheus as data source

### Example Queries

**Request Rate**:
```promql
rate(http_requests_total[5m])
```

**Request Latency (p95)**:
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Error Rate**:
```promql
rate(http_requests_total{status=~"5.."}[5m])
```

**Active Connections**:
```promql
active_connections
```

**Cache Hit Ratio**:
```promql
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

### Recommended Panels

1. **Request Rate**: Line graph showing requests per second
2. **Response Time**: Line graph showing p50, p95, p99 latencies
3. **Error Rate**: Line graph showing 4xx and 5xx errors
4. **Active Connections**: Gauge showing current connections
5. **Search Activity**: Bar chart showing searches by country
6. **Cache Performance**: Pie chart showing hit/miss ratio

## Troubleshooting

### Backend: Sentry Not Receiving Events

1. Verify DSN is correct in `.env`
2. Check Sentry project settings allow events from your environment
3. Verify network connectivity: `curl https://sentry.io`
4. Check backend logs for Sentry initialization errors

### Frontend: Sentry Not Working

1. Verify `VITE_SENTRY_DSN` is set in `.env`
2. Rebuild frontend: `npm run build`
3. Check browser console for Sentry initialization messages
4. Verify CSP headers allow Sentry domain

### Prometheus: Not Scraping Metrics

1. Verify backend is running: `curl http://localhost:8000/api/metrics`
2. Check Prometheus targets: http://localhost:9090/targets
3. Verify `monitoring/prometheus.yml` configuration
4. Check Docker network connectivity

### Grafana: No Data

1. Verify Prometheus data source is configured correctly
2. Check Prometheus is scraping metrics successfully
3. Verify time range in Grafana query
4. Check query syntax in panel editor

### Health Check Failures

If `/health/detailed` shows errors:

- **Database error**: Verify PostgreSQL is running and connection string is correct
- **Redis error**: Verify Redis is running (or set to optional)
- **External API errors**: Check network connectivity and API status

## Best Practices

1. **Set appropriate sample rates**: Use lower rates (0.1-0.2) in production to reduce costs
2. **Filter sensitive data**: Ensure passwords, tokens, and secrets are filtered
3. **Set up alerts**: Configure alerts in Grafana for critical metrics
4. **Regular monitoring**: Review Sentry issues and Grafana dashboards regularly
5. **Update dependencies**: Keep Sentry SDK and Prometheus client up to date
6. **Use environments**: Separate dev/staging/prod in Sentry for better organization

## Support

For issues or questions:
- Sentry documentation: https://docs.sentry.io
- Prometheus documentation: https://prometheus.io/docs
- Grafana documentation: https://grafana.com/docs

## License

This monitoring setup is part of the ILUMINATI SYSTEM v5 project.
