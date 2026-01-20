# 🧪 Testing Guide

## Prehľad

Tento projekt používa komplexnú testovaciu stratégiu pre backend (Python/FastAPI) aj frontend (React/Vite).

## Backend Testy

### Spustenie testov

```bash
cd backend
pip install -r requirements.txt
pytest
```

### S coverage reportom

```bash
pytest --cov=app --cov-report=html
# Otvor htmlcov/index.html v prehliadači
```

### Spustenie konkrétnych testov

```bash
pytest tests/test_auth.py -v
pytest -k "test_login" -v
pytest -m security -v
```

## Frontend Testy

### Spustenie testov

```bash
cd frontend
npm install
npm run test
```

### S coverage

```bash
npm run test:ci
```

### Interaktívny UI

```bash
npm run test:ui
```

## Pre-commit Hooks

### Inštalácia

```bash
pip install pre-commit
pre-commit install
```

### Manuálne spustenie

```bash
pre-commit run --all-files
```

## CI/CD Pipeline

Pipeline sa automaticky spustí pri:
- Push do `main` alebo `develop` branch
- Otvorení Pull Request do `main` alebo `develop`

### Jobs:
1. **backend-test** - Python testy + linting
2. **frontend-test** - JS testy + build check
3. **security-scan** - pip-audit + npm audit
4. **build** - Docker images (len na main)

## Coverage Ciele

| Oblasť | Minimálny Coverage |
|--------|-------------------|
| Backend | 70% |
| Frontend | 70% |

## Písanie Testov

### Backend (pytest)

```python
@pytest.mark.asyncio
async def test_example(client: AsyncClient):
    response = await client.get("/api/endpoint")
    assert response.status_code == 200
```

### Frontend (vitest)

```javascript
import { describe, it, expect } from 'vitest';

describe('Component', () => {
  it('should work', () => {
    expect(true).toBe(true);
  });
});
```

## Testovacia Štruktúra

### Backend

```
backend/tests/
├── __init__.py
├── conftest.py          # Pytest fixtures a konfigurácia
├── test_health.py       # Health check testy
├── test_auth.py         # Autentifikačné testy
├── test_search.py       # Vyhľadávacie testy
└── test_security.py     # Bezpečnostné testy
```

### Frontend

```
frontend/src/test/
├── setup.js                      # Test setup a mocks
├── components/
│   └── SearchBar.test.jsx       # Komponentové testy
└── utils/
    └── export.test.js           # Utility testy
```

## Debugging Testov

### Backend

```bash
# Spustiť testy s výstupom print
pytest -s

# Spustiť len zlyhaný test
pytest --lf

# Zastaviť po prvom zlyhaní
pytest -x
```

### Frontend

```bash
# Spustiť v watch mode
npm run test

# Spustiť konkrétny test
npm run test -- SearchBar

# Spustiť s UI
npm run test:ui
```

## Bežné Problémy

### Backend

**Problem:** SQLAlchemy import error  
**Riešenie:** Uistite sa, že máte správnu verziu SQLAlchemy >=2.0.23

**Problem:** Async test nefunguje  
**Riešenie:** Použite `@pytest.mark.asyncio` dekorátor

### Frontend

**Problem:** Cannot find module '@testing-library/react'  
**Riešenie:** `npm install --save-dev @testing-library/react`

**Problem:** Test timeout  
**Riešenie:** Zvýšte timeout v vitest.config.js

## Continuous Integration

Každý commit do protected branches spustí:

1. **Linting** - Kontrola kódového štýlu
2. **Unit Tests** - Jednotkové testy
3. **Coverage** - Kontrola pokrytia kódu
4. **Security Scan** - Bezpečnostné skenovanie
5. **Build** - Overenie build procesu

Všetky kontroly musia prejsť pred mergnutím PR.

## Lokálne Testovanie CI

Môžete testovať CI workflow lokálne pomocou [act](https://github.com/nektos/act):

```bash
# Install act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run CI locally
act -j backend-test
act -j frontend-test
```

## Best Practices

1. **Píšte testy pred kódom** - TDD approach
2. **Udržujte testy jednoduché** - Jeden test, jedno tvrdenie
3. **Používajte deskriptívne názvy** - `test_user_can_login_with_valid_credentials`
4. **Mock externe závislosti** - DB, API, etc.
5. **Testujte edge cases** - Null, empty, invalid data
6. **Udržujte vysoké pokrytie** - Min. 70%

## Ďalšie Zdroje

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
