# Analýza stavu projektu (2026-11-01)

Cieľ: zistiť, na čom stavať financials, IBAN, CZ ARES a PL KRS.

## 1. Ktorý backend beží

- Nasadzuje sa `backend/app` (v5). Dôkaz: `Dockerfile.backend` spúšťa `uvicorn backend.app.main:app`.
- `backend_legacy_20251229_195800/` je archív starého backendu (sync `requests`, Alembic, auth, API kľúče, webhooky).
  v5 z neho nič neimportuje (`grep sk_ruz_provider|risk_intelligence|circuit_breaker backend/` = 0 výsledkov).
- v5 nemá Alembic ani SQLAlchemy model firmy. `backend/app/models/company.py` je Pydantic model (`ico, name, address, status, raw_data`).
  Tabuľky sú v SQL súboroch `backend/migrations/2025_12_29_identity_graph.sql` a `2025_12_30_relationship_graph.sql`
  (`atlas_companies`, `company_identifiers`, `company_sources`, ...). Tabuľka `companies` neexistuje.

## 2. `backend_legacy_.../services/sk_ruz_provider.py`

| Zistenie | Dôsledok |
|---|---|
| `API_URL = .../cruz-public/api/uctovne-zavierky?ico=` | Endpoint neexistuje, RÚZ vracia 403 „Request Rejected“ (overené 2026-11-01). Provider v praxi vždy padá na HTML scraping alebo vracia `None`. |
| Parsuje len `obrat` a `zisk` | Žiadna súvaha, žiadne aktíva/pasíva/vlastný kapitál. |
| `self.session.verify = False` + potlačenie SSL warningov | Vypnuté overovanie TLS. Neprenášať. |
| Circuit breaker | V provideri nie je. `circuit_breaker.py` existuje, ale RÚZ ho nevolá. |
| Stub mode | `STUB_MODE` + `_stub_financial_statements` (len IČO 52374220). |
| Sync `requests` | v5 je async (`httpx.AsyncClient`), kód sa nedá priamo použiť. |

`backend/app/services/ruz_service.py` (v5) financials nerieši vôbec: Autoform → fallback scraping HTML detailu (názov, adresa, dátum vzniku, stav).

## 3. Skutočné otvorené RÚZ API (overené)

Reťazec: `GET /cruz-public/api/uctovne-jednotky?zmenene-od=2000-01-01&ico={ico}` → `{"id": [...]}`
→ `/api/uctovna-jednotka?id=` (obsahuje `idUctovnychZavierok`)
→ `/api/uctovna-zavierka?id=` (`obdobieOd/Do`, `idUctovnychVykazov`)
→ `/api/uctovny-vykaz?id=` (`idSablony`, `obsah.tabulky[].data`)
→ `/api/sablona?id=` (definícia riadkov).

Šablóny:
- **687 = „Úč MUJ“** (mikro účtovné jednotky): Strana aktív 23 riadkov, Strana pasív 22, Výkaz ziskov a strát 38, 2 dátové stĺpce.
- Väčšie firmy podávajú inú šablónu (napr. „Úč POD“). IFRS výkazy (napr. Slovnaft, šablóna 742) nemajú štruktúrované tabuľky, iba PDF.
- Záver: samotná 687 pokryje mikro firmy. Pre pokrytie SK trhu treba mapovať aspoň 687 + POD šablónu.

## 4. CZ a PL v v5 už existujú

- `backend/app/services/ares_service.py`: ARES REST (`/ekonomicke-subjekty/{ico}`), endpoint `GET /api/company/{ico}`.
- `backend/app/services/krs_service.py`: oficiálne KRS API (`api-krs.ms.gov.pl/api/krs/OdpisPelny/{krs}`).
  Endpoint `/api/pl/company/{krs}` však používa Playwright variant (`krs_playwright_service.py`).
- Oba služby zapisovali pri každom requeste debug súbor na disk; odstránené v tomto PR.

## 5. Frontend vs. backend

- Frontend (`frontend/src/config/api.js`, `contexts/AuthContext.jsx`) volá `/api/auth/*`, `/api/search/history`,
  `/api/user/favorites`, `/api/export/excel`. Tieto endpointy sú len v legacy backende, v5 ich nemá.
  Prihlásenie, história, obľúbené a Excel export proti nasadenému v5 nefungujú.
- TanStack Query nie je nainštalovaný.

## 6. Testy (stav na `main`)

`pytest backend/tests`: 9 passed, 2 failed (`test_v4_person_graph.py::test_person_graph_end_to_end`,
`::test_papi_hair_design_enrichment`, adresa konateľa sa parsuje ako dátum narodenia). Frontend `vite build` prejde.

## 7. Bezpečnosť

- Repo je verejné. `backend_legacy_.../sql_app.db` bola commitnutá; všetky tabuľky prázdne (0 riadkov). Odstránená z indexu, `*.db` v `.gitignore`. V histórii gitu ostáva.
- Lokálne `.env` súbory nie sú v gite (`.gitignore` ich pokrýva). Nikdy ich necommitovať.
