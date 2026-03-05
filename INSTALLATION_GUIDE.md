# 📦 ILUMINATI SYSTEM v4 - Inštalácia a Spustenie

**Dátum:** 2025-12-20  
**Verzia:** 5.0 Enterprise Edition

---

## 🚀 Rýchly Start

### 1. Rozbalenie projektu

```bash
# Rozbaliť ZIP súbor
unzip v4.zip -d iluminati-system
cd iluminati-system
```

### 2. Backend Setup

```bash
# Prejsť do backend adresára
cd backend

# Vytvoriť virtual environment
python3 -m venv venv

# Aktivovať virtual environment
# Na macOS/Linux:
source venv/bin/activate
# Na Windows:
# venv\Scripts\activate

# Nainštalovať závislosti
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
# Prejsť do frontend adresára
cd ../frontend

# Nainštalovať závislosti
npm install
```

### 4. Databáza Setup

```bash
# Spustiť PostgreSQL (ak nie je nainštalovaný, použite Docker)
# Alebo upraviť DATABASE_URL v .env súbore

# Vytvoriť .env súbor v root adresári projektu:
cp .env.example .env
# Upraviť DATABASE_URL, REDIS_URL, atď.
```

### 5. Spustenie

#### Spôsob 1: Použiť start.sh skript

```bash
# V root adresári projektu
chmod +x start.sh
./start.sh
```

#### Spôsob 2: Manuálne spustenie

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # alebo venv\Scripts\activate na Windows
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 6. Prístup k aplikácii

- **Frontend:** <http://localhost:8009> (alebo <https://localhost:8009> ak máte SSL)
- **Backend API:** <http://localhost:8000> (alebo <https://localhost:8000>)
- **API Dokumentácia:** <http://localhost:8000/api/docs>

---

## 📡 Monitoring Setup (Voliteľné)

### Sentry (Error Tracking)

1. Vytvorte projekty na https://sentry.io (backend: FastAPI, frontend: React).
2. Pridajte DSN do `.env`:
   ```bash
   SENTRY_DSN=https://your-backend-key@sentry.io/project-id
   VITE_SENTRY_DSN=https://your-frontend-key@sentry.io/project-id
   ```

### Prometheus & Grafana (Metriky)

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3001 (predvolené: `admin`/`admin`)

### Overenie

```bash
# Skontrolujte metriky
curl http://localhost:8000/api/metrics

# Skontrolujte detailný health check
curl http://localhost:8000/health/detailed
```

Viac informácií: [MONITORING.md](MONITORING.md)

---

## 📋 Požiadavky

### Backend

- Python 3.10+
- PostgreSQL 14+
- Redis (voliteľné, pre cache)

### Frontend

- Node.js 18+
- npm alebo yarn

### Docker (voliteľné)

- Docker Desktop
- Docker Compose

---

## 🔧 Konfigurácia

### Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/iluminati_db

# Redis (voliteľné)
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-change-in-production

# Stripe (voliteľné)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Frontend URL
FRONTEND_URL=http://localhost:8009
```

---

## 🐳 Docker Setup (Odporúčané)

```bash
# Spustiť všetky služby (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# Zobraziť logy
docker-compose logs -f

# Zastaviť služby
docker-compose down
```

---

## 🧪 Testovanie

### Backend testy

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### Frontend testy

```bash
cd frontend
npm test
```

---

## 📚 Dokumentácia

- **README.md** - Hlavná dokumentácia projektu
- **QUICK_START.md** - Rýchly štart
- **MONITORING.md** - Monitoring (Sentry, Prometheus, Grafana)
- **docs/** - Detailná dokumentácia
- **TEST_REPORT.md** - Test report
- **SPECIAL_TESTS_REPORT.md** - Špeciálne testy

---

## ⚠️ Dôležité Poznámky

1. **SSL Certifikáty:** Ak chcete používať HTTPS, vygenerujte SSL certifikáty (pozri `docs/SSL_SETUP.md`)

2. **Databáza:** Uistite sa, že PostgreSQL beží a databáza je vytvorená

3. **Redis:** Redis je voliteľný, aplikácia funguje aj bez neho (použije in-memory cache)

4. **Porty:**
   - Backend: 8000
   - Frontend: 8009
   - PostgreSQL: 5432
   - Redis: 6379
   - Prometheus: 9090 (ak je spustený monitoring)
   - Grafana: 3001 (ak je spustený monitoring)

---

## 🆘 Riešenie Problémov

### Backend sa nespustí

- Skontrolujte, či je PostgreSQL bežiaci
- Skontrolujte DATABASE_URL v .env
- Skontrolujte, či sú všetky závislosti nainštalované

### Frontend sa nespustí

- Skontrolujte, či je Node.js nainštalovaný
- Vymažte node_modules a nainštalujte znova: `rm -rf node_modules && npm install`

### CORS chyby

- Skontrolujte, či sú správne nastavené CORS origins v `backend/main.py`

---

## 📞 Podpora

Pre viac informácií pozri:

- `README.md`
- `docs/DEVELOPER_GUIDE.md`
- `docs/PRODUCTION_TESTING_PLAN.md`

---

## Úspešné testovanie! 🚀
