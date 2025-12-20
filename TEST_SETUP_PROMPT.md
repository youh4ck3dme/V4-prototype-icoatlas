# 🧪 ILUMINATI SYSTEM v4 - Kompletný Testovací Prompt

**Dátum vytvorenia:** 2025-12-20
**Účel:** Systematické testovanie projektu od začiatku do konca

---

## 📋 POSTUPNOSŤ TESTOVANIA

### FÁZA 1: Príprava Prostredia

```bash
# 1.1 Prejsť do projektu
cd /Users/youh4ck3dme/Downloads/V4-prototype-icoatlas

# 1.2 Backend - Virtual Environment
cd backend
python3 -m venv venv
source venv/bin/activate

# 1.3 Nainštalovať závislosti
pip install -r requirements.txt
pip install pytest pytest-cov
```

### FÁZA 2: Databáza

```bash
# 2.1 Skontrolovať PostgreSQL
brew services list | grep postgresql
# Ak nebeží: brew services start postgresql

# 2.2 Vytvoriť databázu (ak neexistuje)
createdb iluminati_db 2>/dev/null || echo "DB už existuje"

# 2.3 Inicializovať schému
cd /Users/youh4ck3dme/Downloads/V4-prototype-icoatlas/backend
source venv/bin/activate
python -c "from services.database import init_database; init_database()"
```

### FÁZA 3: Backend Testy

```bash
# 3.1 Spustiť všetky testy s coverage
cd /Users/youh4ck3dme/Downloads/V4-prototype-icoatlas
source backend/venv/bin/activate
pytest backend/tests/ -v --tb=short

# 3.2 Spustiť s coverage reportom
pytest backend/tests/ --cov=backend/services --cov-report=term-missing
```

### FÁZA 4: Backend API Server

```bash
# 4.1 Spustiť backend server
cd /Users/youh4ck3dme/Downloads/V4-prototype-icoatlas/backend
source venv/bin/activate
python main.py
# Server beží na http://localhost:8000
```

### FÁZA 5: Frontend

```bash
# 5.1 V NOVOM TERMINÁLI - Frontend setup
cd /Users/youh4ck3dme/Downloads/V4-prototype-icoatlas/frontend
npm install

# 5.2 Spustiť frontend
npm run dev
# Frontend beží na http://localhost:8009
```

### FÁZA 6: Verifikácia

| Test         | URL/Príkaz                                                       | Očakávaný výsledok       |
| ------------ | ---------------------------------------------------------------- | ------------------------ |
| Backend API  | [http://localhost:8000/api/docs](http://localhost:8000/api/docs) | Swagger dokumentácia     |
| Frontend     | [http://localhost:8009](http://localhost:8009)                   | Hlavná stránka aplikácie |
| Health check | `curl http://localhost:8000/health`                              | `{"status": "ok"}`       |

---

## 🔄 JEDNORIADKOVÝ QUICK START

```bash
cd /Users/youh4ck3dme/Downloads/V4-prototype-icoatlas && \
source backend/venv/bin/activate && \
pytest backend/tests/ -v && \
echo "✅ Testy OK" || echo "❌ Testy zlyhali"
```

---

## 📊 CHECKLIST

- [ ] Virtual environment aktivovaný
- [ ] Závislosti nainštalované
- [ ] PostgreSQL beží
- [ ] Databáza vytvorená
- [ ] Backend testy prechádzajú
- [ ] Backend server beží (port 8000)
- [ ] Frontend beží (port 8009)
- [ ] API dokumentácia dostupná

---

## ⚠️ RIEŠENIE PROBLÉMOV

| Problém               | Riešenie                             |
| --------------------- | ------------------------------------ |
| `ModuleNotFoundError` | `pip install -r requirements.txt`    |
| PostgreSQL nebeží     | `brew services start postgresql`     |
| Port 8000 obsadený    | `lsof -i :8000` a zabiť proces       |
| Frontend CORS         | Skontrolovať `FRONTEND_URL` v `.env` |

---

## Pripravené ## Úspešné testovanie! 🚀
