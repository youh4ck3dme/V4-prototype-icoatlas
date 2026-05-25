# ILUMINATI SYSTEM API Documents

## Monitoring Endpoints

### Health Check

```
GET /health
```

Returns basic application status.

**Response:**
```json
{
  "status": "ok",
  "env": "development",
  "version": "5.0.0"
}
```

### Detailed Health Check

```
GET /health/detailed
```

Returns detailed status of all dependencies (database, Redis, Sentry, external APIs).

**Response:**
```json
{
  "status": "ok",
  "env": "development",
  "version": "5.0.0",
  "checks": {
    "database": { "status": "ok", "message": "Database is reachable" },
    "redis": { "status": "skipped", "message": "Redis not configured" },
    "sentry": { "status": "ok", "message": "Sentry is configured" },
    "external_apis": {
      "ares": { "status": "ok", "message": "ARES is reachable" },
      "krs": { "status": "ok", "message": "KRS is reachable" }
    }
  }
}
```

### Prometheus Metrics

```
GET /api/metrics
```

Returns Prometheus-formatted metrics for scraping. Includes:
- `http_requests_total` — Total HTTP requests (labels: method, endpoint, status)
- `http_request_duration_seconds` — Request latency histogram (labels: method, endpoint)
- `active_connections` — Current active connections
- `search_requests_total` — Search requests by country and status
- `cache_hits_total` / `cache_misses_total` — Cache performance
- `db_queries_total` / `db_query_duration_seconds` — Database query metrics

---

## Phase 17: Deep SK Intelligence

Extended company profile fields for Slovak entities (Source: ORSR, RUV, ZRSR).

### Company Object (Node)

The `Node` object in `/api/search` response now includes the following additional fields:

| Field                  | Type        | Description                                                         |
| :--------------------- | :---------- | :------------------------------------------------------------------ |
| `executives`           | `List[str]` | List of company executives (Statutárny orgán).                      |
| `shareholders`         | `List[str]` | List of shareholders (Spoločníci).                                  |
| `establishment_date`   | `string`    | Date of establishment (ISO 8601: YYYY-MM-DD).                       |
| `legal_form`           | `string`    | Legal form of the entity (e.g., "Spoločnosť s ručením obmedzeným"). |
| `activity_codes`       | `List[str]` | NACE activity codes.                                                |
| `financials`           | `Dict`      | Financial indicators (Revenue, Profit, Assets).                     |
| `employees_count`      | `int`       | Number of employees.                                                |
| `contact_email`        | `string`    | Contact email address.                                              |
| `contact_phone`        | `string`    | Contact phone number.                                               |
| `website`              | `string`    | Company website URL.                                                |
| `status`               | `string`    | Company status (e.g., "Aktívna", "Likvidácia").                     |
| `registration_id`      | `string`    | Registration ID (Vložka číslo).                                     |
| `registration_section` | `string`    | Registration Section (Oddiel).                                      |
| `capital`              | `string`    | Registered capital (Základné imanie).                               |

### Example Response

```json
{
  "id": "sk_35763469",
  "label": "Slovenská sporiteľňa, a.s.",
  "executives": ["Ing. Peter Krutil", "Mgr. Pavel Cetkovský"],
  "shareholders": ["Erste Group Bank AG"],
  "financials": {
    "revenue": 1000000,
    "currency": "EUR"
  },
  "status": "Aktívna"
}
```
