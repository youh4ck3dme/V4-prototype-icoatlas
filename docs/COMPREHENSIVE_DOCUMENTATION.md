# 📚 ICO Atlas - Komplexná Projektová Dokumentácia

Vítajte v hlavnom manuáli a technickej dokumentácii projektu **ICO Atlas (V4-prototype-icoatlas)**. Tento dokument slúži ako centrálny a autoritatívny zdroj pravdy pre vývoj, testovanie, deployment, databázové operácie a business logiku pre všetky krajiny Vyšehradskej štvorky (V4).

---

## 📋 Obsah

1. [Prehľad a Architektúra Systému](#1-prehľad-a-architektúra-systému)
2. [Štruktúra Projektu](#2-štruktúra-projektu)
3. [Integrácie Registrov & Firemné Identifikátory (DIČ/NIP/Adószám)](#3-integrácie-registrov--firemné-identifikátory-dičnipadószám)
4. [Databáza a Migrácia Grafu (Graph DB)](#4-databáza-a-migrácia-grafu-graph-db)
5. [Lokálny Vývoj a Spustenie](#5-lokálny-vývoj-a-spustenie)
6. [Testovací Suite](#6-testovací-suite)
7. [VPS Deployment & Operations Runbook (icoatlas.sk)](#7-vps-deployment--operations-runbook-icoatlassk)
8. [Mobilné Responsívne CSS Úpravy (Dynamic Viewport)](#8-mobilné-responsívne-css-úpravy-dynamic-viewport)
9. [Riešenie Problémov & Núdzový Rollback](#9-riešenie-problémov--núdzový-rollback)

---

## 1. Prehľad a Architektúra Systému

Projekt **ICO Atlas** je moderná aplikácia pre vyhľadávanie a vizualizáciu prepojení medzi firmami, štatutármi a adresami v krajinách V4 (Slovensko, Česko, Poľsko, Maďarsko).

### Architektonická Schéma

```text
┌─────────────────────────────────────────────────────────────────┐
│                         KLIENTSKÁ VRSTVA                        │
│                                                                 │
│  ┌──────────────┐          ┌──────────────┐          ┌─────────┐│
│  │   Browser    │          │  Mobil/iOS   │          │ Externé ││
│  │  (React App) │          │  (Safari)    │          │   API   ││
│  └──────┬───────┘          └──────┬───────┘          └────┬────┘│
└─────────┼─────────────────────────┼───────────────────────┼─────┘
          │ HTTPS                   │ HTTPS                 │ HTTPS
┌─────────▼─────────────────────────▼───────────────────────▼─────┐
│                      REVERZNÝ PROXY (nginx / caddy)             │
└───────────────────────────────────┬─────────────────────────────┘
                                    │ HTTP
┌───────────────────────────────────▼─────────────────────────────┐
│                     APLIKAČNÁ VRSTVA (FastAPI)                  │
│                                                                 │
│  - /api/v4/search  -> Vyhľadávanie v registroch s grafom        │
│  - /api/health     -> Monitorovanie zdravia (env=production)    │
│  - /api/metrics    -> Zber systémových metrík                   │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     Služby a Klienti                      │  │
│  │  - sk_rpo.py (Autoform API)  - cz_ares.py (ARES v2 REST)  │  │
│  │  - pl_krs.py (KRS REST)      - hu_nav.py (NAV XML API)    │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬─────────────────────────────┘
                                    │ SQL / TCP
┌───────────────────────────────────▼─────────────────────────────┐
│                       DÁTOVÁ VRSTVA                             │
│                                                                 │
│  ┌──────────────────────────────┐  ┌──────────────────────────┐ │
│  │      PostgreSQL (Cache)      │  │      PostgreSQL Graph    │ │
│  │  - Rýchla in-memory cache    │  │  - graph_nodes table     │ │
│  │  - Tabuľka lokálnej cache    │  │  - graph_edges table     │ │
│  └──────────────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Štruktúra Projektu

```text
V4-prototype-icoatlas/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/      # API routy (/search, /health, /metrics)
│   │   ├── db/                 # Databázové pripojenie a modely
│   │   ├── models/             # SQLAlchemy a Pydantic schémy
│   │   ├── services/           # Služby a scrapery (Autoform, ARES, KRS, NAV)
│   │   └── main.py             # Hlavný vstupný bod FastAPI
│   ├── migrations/             # SQL súbory pre úpravu schémy
│   ├── tests/                  # Backend unit/integrácia testy
│   └── requirements.txt        # Python dependencie
├── frontend/
│   ├── src/
│   │   ├── components/         # Znovupoužiteľné UI (IcoAtlasLogo, ForceGraph, atď.)
│   │   ├── pages/              # Stránky (HomePageNew, Dashboard, Analytics, Profile)
│   │   └── App.jsx             # Router a smerovanie
│   ├── Dockerfile.prod         # Produkčný Dockerfile (uzamknutý na Node 20)
│   └── package.json            # Node.js dependencie
├── docker-compose.prod.yml      # Produkčná orchestrácia (Nginx, Backend, DB)
├── backup_production_db.sh      # Skript na bezpečné zálohovanie Postgresu
├── run_production_migrations.sh # Bezpečný spúšťač DB migrácií
└── run_tests.sh                 # Spúšťač testovacieho suite
```

---

## 3. Integrácie Registrov & Firemné Identifikátory (DIČ/NIP/Adószám)

Každá krajina má špecifické pravidlá na získavanie a spracovanie firemných dát a najmä daňových identifikátorov (DIČ/NIP/Adószám). **Tieto pravidlá sú kritické pre ochranu integrity dát a predchádzanie regresiám.**

### 🇸🇰 Slovensko (SK)
- **Zdroj dát:** Autoform API (Slovensko.Digital) a záložné scrapery.
- **Pravidlo pre DIČ (TIN):** Musí sa korektne parsovať kľúč `tin` priamo z Autoform API payloadu, prípadne sa očistí prefix `SK` zo stringu `vatin`.
- **Implementácia:** `backend/app/services/sk_rpo.py`

### 🇨🇿 Česká republika (CZ)
- **Zdroj dát:** ARES v2 REST API (`https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat`).
- **Pravidlo pre DIČ:** Systém must zachovať kompletnú raw odpoveď z API ARES a extrahovať pole `dic` priamo z odpovede bez akejkoľvek degradácie formátu.
- **Implementácia:** `backend/app/services/cz_ares.py`

### 🇵🇱 Poľsko (PL)
- **Zdroj dát:** Krajowy Rejestr Sądowy (KRS) a Playwright scraper pre CEIDG / Biała Lista VAT.
- **Pravidlo pre NIP (Daňové číslo):** NIP sa získava pomocou regulárnych výrazov z HTML výstupu a povinne prechádza validáciou kontrolného checksumu (Modulo 11).
- **Implementácia:** `backend/app/services/pl_krs.py`

### 🇭🇺 Maďarsko (HU)
- **Zdroj dát:** NAV Online Számla XML API.
- **Pravidlo pre Adószám:** Extrahovaný identifikátor musí striktne dodržať maďarský formát `XXXXXXXX-Y-ZZ` (8 číslic daňového čísla, 1 číslica DPH kódu, 2 číslice kódu oblasti).
- **Implementácia:** `backend/app/services/hu_nav.py`

### 🖥️ Frontend Mapovanie v Reacte
V súbore `frontend/src/pages/HomePageNew.jsx` pri parsovaní výsledkov vyhľadávania musí mapovanie v rámci fallbacku pre grafové uzly striktne priraďovať parameter `dic` z backend payloadu:
```javascript
// Správne priradenie na frontende
dic: companyData.dic || companyData.vat_id || companyData.tax_id
```

---

## 4. Databáza a Migrácia Grafu (Graph DB)

Vztahy medzi entitami sú uložené v dvoch hlavných relačných tabuľkách pre vizualizáciu grafu: `graph_nodes` a `graph_edges`.

### Databázová Schéma (Idempotentná)

```sql
-- Tabuľka pre Uzly (Node)
CREATE TABLE IF NOT EXISTS graph_nodes (
    id VARCHAR(100) PRIMARY KEY,
    label VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- company, person, address
    country VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabuľka pre Hrany (Edge)
CREATE TABLE IF NOT EXISTS graph_edges (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(100) REFERENCES graph_nodes(id) ON DELETE CASCADE,
    target_id VARCHAR(100) REFERENCES graph_nodes(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL, -- executive, shareholder, address_match
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_source_target_type UNIQUE (source_id, target_id, type)
);
```

---

## 5. Lokálny Vývoj a Spustenie

### Predpoklady
- Python 3.10+ (odporúčané 3.11)
- Node.js 20+
- PostgreSQL 16+

### Postup spustenia:

1. **Konfigurácia `.env` súboru:**
   Vytvorte súbor `.env` v root adresári podľa šablóny `.env.example`. Očakávaný formát databázovej URL:
   `DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost:5432/<db_name>`

2. **Spustenie celého stacku jedným príkazom:**
   Aplikácia disponuje skriptom `./start_dev.sh`, ktorý naštartuje lokálnu databázu, prepojí backend a spustí Vite pre frontend:
   ```bash
   ./start_dev.sh
   ```

---

## 6. Testovací Suite

Pred akýmkoľvek pushom na produkciu alebo zlúčením kódu je **povinné** spustiť testy, aby sa overilo, že žiadne integrácie registrov alebo daňových identifikátorov neboli porušené.

### Spustenie testov:
```bash
./run_tests.sh
```

Zvláštna pozornosť sa venuje testu `backend/tests/test_v4_dic_fields.py`, ktorý verifikuje parsovanie a zachovanie DIČ/NIP/Adószám pre všetky 4 krajiny. Tento test musí zakaždým prejsť s výsledkom **OK**.

---

## 7. VPS Deployment & Operations Runbook (icoatlas.sk)

Nasadenie na produkčný VPS server `fantastic4-vps` prebieha pomocou Docker Compose s minimálnym výpadkom.

### 7.1 Frontend Deploy (Zápis zmien a build)
1. **Lokálne overenie a push:**
   ```bash
   cd frontend
   npm run build
   cd ..
   git status
   git add frontend/src frontend/Dockerfile.prod PRODUCTION_OPS_GUIDE.md
   git commit -m "fix(frontend): improve mobile and iPhone responsiveness"
   git push origin main
   ```
2. **Aktualizácia na VPS:**
   ```bash
   ssh fantastic4-vps
   cd /opt/icoatlas
   git pull origin main
   docker compose -f docker-compose.prod.yml build frontend
   docker compose -f docker-compose.prod.yml up -d --no-deps frontend nginx
   ```

### 7.2 Backend Deploy a Databázové Operácie
Pred nasadením nového backendu je **povinné** spraviť zálohu produkčnej databázy:
```bash
ssh fantastic4-vps
cd /opt/icoatlas
# 1. Záloha databázy (idempotentný skript, neexportuje heslá na konzolu)
./backup_production_db.sh

# 2. Stiahnutie najnovšieho kódu
git pull origin main

# 3. Spustenie databázových migrácií pre Grafovú databázu
./run_production_migrations.sh

# 4. Build a reštart backend kontajnera
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d --no-deps backend
```

---

## 8. Mobilné Responsívne CSS Úpravy (Dynamic Viewport)

Z dôvodu zabezpečenia plnej kompatibility s iOS (Safari/WebKit) a Android mobilnými prehliadačmi boli aplikované tieto štandardy:
- **Dynamic Viewport Height (`100dvh` / `min-h-[100dvh]`):** Nahrádza klasické `100vh` vo všetkých komponentoch, čím predchádza odrezaniu spodnej časti obrazovky pod lištou prehliadača na iPhone.
- **Flex Wrap & Widths:** Tlačidlá vyhľadávania a filtre majú nastavené responsívne šírky `w-full md:w-auto`, aby v portrait zobrazení nedochádzalo k ich stláčaniu.

---

## 9. Riešenie Problémov & Núdzový Rollback

### Zobrazenie logov:
```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### Núdzový Rollback (Návrat k predchádzajúcemu commitu):
Ak nová verzia vykáže neočakávané chyby, vráťte VPS do funkčného stavu:
```bash
ssh fantastic4-vps
cd /opt/icoatlas
# Zobrazenie histórie commitov
git log --oneline -10
# Návrat k poslednému bezchybnému commitu
git checkout <good-commit-sha>
# Rebuild a spustenie frontend/backend kontajnerov
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```
