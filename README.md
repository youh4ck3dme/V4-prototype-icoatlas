## 🦾 Copilot/AI Review Prompt & Blueprint (V4-prototype-icoatlas)

Použi tento prompt na rýchle zadanie pre AI asistenta v GitHub Copilot alebo GPT, keď chceš získať praktické odporúčania v projekte **V4-prototype-icoatlas**:

### 💡 Prompt pre Copilot AI / ChatGPT / Review agenta:

```markdown
Analyzuj projekt V4-prototype-icoatlas (repo: youh4ck3dme/V4-prototype-icoatlas).
1. Zameraj sa na:
   - Funkcionalitu – navrhni konkrétne zlepšenia podľa existujúceho kódu, testov, dokumentácie, TODO zoznamov.
   - Bezpečnosť – navrhni zlepšenia podľa best practices kódovania, deploymentu, infraštruktúry, storage citlivých údajov, GDPR, monitoring, audit.
2. Priprav sumarizáciu konkrétnych krokov, odporúčania na refaktoring, rozšírenie, testovanie, čo chýba.
3. Odpoveď formátuj vo forme prehľadného checklistu.

**Kontext – Project Audit:**
- Rozšíriť DB model (executives, financials, atď.), API exporty (CSV/JSON/Excel).
- Jednotkové, integračné, E2E a bezpečnostné testy (min. 90% coverage).
- CI/CD pipeline, pre-commit hooks, monitoring (Sentry/Prometheus).
- Vylepšiť dashboard, offline support, dokumentáciu, React optimalizáciu.
- SSL/TLS povinné, credentials len v .env, HMAC na webhooks, rate limiting podľa tiera.
- CORS protection, GDPR compliance, pravidelné bezpečnostné audity.

_Na tvoju odpoveď čakám vo forme checklistu pre funkcionalitu aj bezpečnosť. Odpoveď nech je stručná, konkrétna a actionable pre developera v tomto projekte._
```

---

### 📘 Blueprint - AI Auditing/Improvement Workflow

1. Skopíruj vyššie prompt.
2. Spusti ho v AI nástroji (GitHub Copilot, ChatGPT, ...).
3. Použi checklist na systematické zlepšenie kódu, bezpečnosti a funkcionality.
4. Po každom kroku aktualizuj README/todo/test coverage.
5. Opakuj audit po veľkých zmenách, merge, deploy.

---

## 📡 Monitoring & Observability

The project includes integrated monitoring with **Sentry** (error tracking) and **Prometheus + Grafana** (metrics and dashboards).

- **Sentry**: Captures backend and frontend errors with context, filters sensitive data, and provides performance tracing.
- **Prometheus**: Collects HTTP request metrics, search counts, cache performance, and database query stats from the backend.
- **Grafana**: Visualizes Prometheus metrics with customizable dashboards.

### Quick Setup

1. Set `SENTRY_DSN` and `VITE_SENTRY_DSN` in `.env` (see `.env.example`).
2. Start the monitoring stack:
   ```bash
   docker-compose -f docker-compose.monitoring.yml up -d
   ```
3. Access Grafana at http://localhost:3001 (default credentials: `admin`/`admin`).

For full details, see [MONITORING.md](MONITORING.md).

---