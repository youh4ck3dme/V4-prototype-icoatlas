# 🌐 V4 API Integration Guide - Komplexná dokumentácia

**Verzia:** 1.0  
**Dátum:** December 2024  
**Autor:** ILUMINATI SYSTEM Team

---

## 📋 Obsah

1. [Prehľad V4 API ekosystému](#1-prehľad-v4-api-ekosystému)
2. [Slovensko (SK)](#2-slovensko-sk)
3. [Česká republika (CZ)](#3-česká-republika-cz)
4. [Poľsko (PL)](#4-poľsko-pl)
5. [Maďarsko (HU)](#5-maďarsko-hu)
6. [Integračná stratégia](#6-integračná-stratégia)
7. [Implementačné príklady](#7-implementačné-príklady)

---

## 1. Prehľad V4 API ekosystému

### Komparatívna tabuľka

| Krajina | Primárny Register       | Protokol  | Formát   | Autentifikácia    | Identifikátor    | Sync API |
| ------- | ----------------------- | --------- | -------- | ----------------- | ---------------- | -------- |
| 🇸🇰 SK   | RPO (Slovensko.Digital) | REST      | JSON     | API Key           | IČO (8 číslic)   | ✅ Áno   |
| 🇨🇿 CZ   | ARES v2                 | REST      | JSON     | Žiadna/Rate Limit | IČO (8-9 číslic) | ❌ Nie   |
| 🇵🇱 PL   | KRS + CEIDG             | REST/SOAP | JSON/XML | Token             | KRS/NIP/REGON    | ✅ Áno   |
| 🇭🇺 HU   | NAV Online              | REST      | XML      | Crypto Signature  | Adószám          | ❌ Nie   |

---

## 2. Slovensko (SK)

### 2.1 Register právnických osôb (RPO) - Slovensko.Digital

> De facto štandard pre SK integrácie

#### Základné informácie (SK)

- **Base URL:** `https://data.slovensko.sk/api/`
- **Dokumentácia:** <https://ekosystem.slovensko.digital/>
- **Protokol:** REST API cez HTTPS
- **Formát:** JSON
- **Autentifikácia:** API Key (registrácia na portáli)

#### Rate Limiting

- Neautentifikovaný: 60 req/min
- S API Key: vyššie limity
- HTTP hlavičky: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

#### Kľúčové Endpointy (SK)

```bash
# Vyhľadanie podľa IČO
GET /api/legal-subjects?ico={ico}

# Synchronizačné API (pre enterprise)
GET /api/sync?since={timestamp}&last_id={id}

# Optimalizovaná sync (len ID)
GET /api/sync?since={timestamp}&only_ids=true

# Autoform (pre našepkávače)
GET /api/autoform?q={query}
```

#### Príklad Response (SK)

```json
{
  "id": 12345,
  "ico": "35763469",
  "name": "Slovenská sporiteľňa, a.s.",
  "legal_form": "Akciová spoločnosť",
  "address": {
    "street": "Tomášikova 48",
    "city": "Bratislava",
    "postal_code": "832 37"
  },
  "status": "active",
  "registration_date": "1994-01-01"
}
```

### 2.2 Register účtovných závierok (RUZ)

> Finančné dáta pre kreditný scoring

- **Endpoint:** `GET /api/data/ruz/accounting_entities/{id}`
- **Dáta:** Súvahy, výkazy ziskov a strát, poznámky
- **Využitie:** Automatizovaný výpočet bonity, fintech aplikácie

### 2.3 Centrálny register zmlúv (CRZ)

> Transparentnosť verejných financií

```bash
# Synchronizácia zmlúv
GET /api/crz/sync?since={timestamp}

# Vyhľadanie podľa dodávateľa
GET /api/crz/contracts?supplier_ico={ico}
```

### 2.4 Obchodný vestník (OV)

> Včasné varovanie pred insolvenciou

```bash
# Likvidácie
GET /api/ov/likvidator_issues

# Zníženie imania
GET /api/ov/znizenie_imania_issues

# Podania do OR
GET /api/ov/or_podanie_issues
```

### 2.5 Špecializované API

| API                  | Účel                  | Využitie               |
| -------------------- | --------------------- | ---------------------- |
| ITMS2014+            | EÚ fondy              | Dotačná analytika      |
| Slovensko.sk (eDesk) | Elektronické schránky | Automatizované podania |
| Finančná správa      | Daňoví dlžníci        | Risk management        |

---

## 3. Česká republika (CZ)

### 3.1 ARES v2 - Nový štandard

> Najlepšie zdokumentované API v regióne

#### Základné informácie (CZ)

- **Base URL:** `https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/`
- **Dokumentácia:** <https://ares.gov.cz/stranky/dokumentace-api> (Swagger UI)
- **Protokol:** REST
- **Formát:** JSON
- **Autentifikácia:** Žiadna (rate limiting)

#### Kľúčové Endpointy (CZ)

```bash
# Vyhľadanie podľa IČO
POST /ekonomicke-subjekty/vyhledat
Content-Type: application/json
{
  "ico": "27074358"
}

# Vyhľadanie podľa názvu
POST /ekonomicke-subjekty/vyhledat
{
  "obchodniJmeno": "Agrofert",
  "pocet": 10
}

# Vyhľadanie v konkrétnom registri
GET /vyhledat-v-registru?registr=vr&ico={ico}
# Registre: vr (Veřejný), rzp (Živnostenský), res (Ekonomický), szr (Zemědělský)

# Validácia IČO
GET /validace-ico/{ico}
```

#### Rate Limiting (CZ)

- HTTP 429 pri prekročení
- Implementujte exponenciálny backoff
- Odporúčanie: asynchrónne volania na backende

#### Príklad Response (CZ)

```json
{
  "ekonomickeSubjekty": [
    {
      "ico": "27074358",
      "obchodniJmeno": "AGROFERT, a.s.",
      "sidlo": {
        "textovaAdresa": "Pyšelská 2327/2, 149 00 Praha 4"
      },
      "pravniForma": "Akciová společnost",
      "datumVzniku": "1993-07-29"
    }
  ]
}
```

### 3.2 Justice.cz - Otvorené dáta

> Pre analytické účely

- **Typ:** Bulk datasety (XML/CSV)
- **Využitie:** Import do vlastnej DB, komplexné dopyty
- **Zdroje:** Verejný register, Insolvenčný register

### 3.3 Insolvenčný register (ISIR)

> Kritické pre bankový sektor

- **Protokol:** SOAP
- **Aktuálnosť:** Minúty po zverejnení
- **Využitie:** Monitoring veriteľov

### 3.4 ČSÚ - Štatistický úrad

> Číselníky a klasifikácie

```bash
# NACE kódy
GET /api/ciselnik/nace

# Regionálne štatistiky
GET /api/statistiky/region/{kod}
```

---

## 4. Poľsko (PL)

### 4.1 KRS API - Krajowy Rejestr Sądowy

> Pre právnické osoby (s.r.o., a.s., družstvá)

#### Základné informácie (KRS)

- **Base URL:** `https://api-krs.ms.gov.pl/api/krs/`
- **Dokumentácia:** <https://api-krs.ms.gov.pl/>
- **Protokol:** REST
- **Formát:** JSON
- **Autentifikácia:** Žiadna

#### Kľúčové Endpointy (KRS)

```bash
# Aktuálny výpis
GET /OdpisAktualny/{krs_number}?rejestr=P&format=json

# Úplná história (forenzná analýza)
GET /OdpisPelny/{krs_number}?rejestr=P&format=json

# Denný bulletin zmien (SYNC API!)
GET /Biuletyn/{YYYY-MM-DD}
```

#### Príklad Response (KRS)

```json
{
  "odpis": {
    "naglowekA": {
      "numerKRS": "0000028860",
      "nazwa": "ORLEN SPÓŁKA AKCYJNA",
      "formaP": "SPÓŁKA AKCYJNA"
    },
    "adres": {
      "ulica": "Chemików",
      "nrDomu": "7",
      "miejscowosc": "Płock",
      "kodPocztowy": "09-411"
    }
  }
}
```

### 4.2 CEIDG - Živnostníci

> Pre fyzické osoby podnikateľov

#### Základné informácie (CEIDG)

- **Endpoint:** <https://datastore.ceidg.gov.pl/CEIDG.DataStore/Services/NewDataStoreProvider.svc>
- **Protokol:** SOAP (WSDL)
- **Autentifikácia:** Authorization Token

#### SOAP Metódy

```xml
<!-- GetID - zoznam NIP podľa filtrov -->
<GetID>
  <DateFrom>2024-01-01</DateFrom>
  <MigrationDateTo>2024-12-31</MigrationDateTo>
</GetID>

<!-- GetMigrationData201901 - plné detaily -->
<GetMigrationData201901>
  <NIP>5272443955</NIP>
</GetMigrationData201901>
```

### 4.3 Biała Lista VAT

> Kritické pre DPH compliance

#### Základné informácie (Biała Lista)

- **Base URL:** <https://wl-api.mf.gov.pl/>
- **Dokumentácia:** <https://www.podatki.gov.pl/wykaz-podatnikow-vat-api/>
- **Protokol:** REST
- **Formát:** JSON
- **Autentifikácia:** Žiadna

#### Endpointy (Biała Lista)

```bash
# Overenie jedného subjektu
GET /api/search/nip/{nip}?date={YYYY-MM-DD}

# Hromadné overenie (max 30)
GET /api/search/nips/{nip1,nip2,nip3}?date={YYYY-MM-DD}

# Overenie bankového účtu
GET /api/check/nip/{nip}/bank-account/{account}?date={YYYY-MM-DD}
```

#### Príklad Response (Biała Lista)

```json
{
  "result": {
    "subject": {
      "name": "ORLEN S.A.",
      "nip": "7740001454",
      "statusVat": "Czynny",
      "accountNumbers": ["PL12345678901234567890123456"]
    }
  }
}
```

### 4.4 REGON API (GUS)

> Štatistický register

- **Protokol:** SOAP (BIR1)
- **Autentifikácia:** Klucz Użytkownika (e-mailová žiadosť)
- **Využitie:** PKD klasifikácia, záloha pre KRS/CEIDG

### 4.5 Sejm API

> Legislatívny monitoring

- **URL:** <https://api.sejm.gov.pl/>
- **Využitie:** RegTech, sledovanie zmien zákonov

---

## 5. Maďarsko (HU)

### 5.1 Situácia s verejnými API

> ⚠️ Najväčšia výzva v V4

- **e-cegjegyzek.hu:** Webové rozhranie, žiadne verejné API
- **Anti-scraping:** CAPTCHA, blokovanie IP
- **Riešenie:** Licencovaní distribútori (Opten, Microsec, Bisnode)

### 5.2 NAV Online Számla - Jediné spoľahlivé API

> "Backdoor" pre verifikáciu firiem

#### Základné informácie (HU)

- **Verzia:** v3.0
- **Protokol:** REST s XML payloadom
- **Autentifikácia:** Kryptografický podpis (SHA-512)

#### Endpoint queryTaxpayer

```bash
POST /invoiceService/v3/queryTaxpayer
Content-Type: application/xml
```

#### Request štruktúra

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QueryTaxpayerRequest>
  <header>
    <requestId>RID123456789</requestId>
    <timestamp>2024-01-15T10:30:00.000Z</timestamp>
    <requestVersion>3.0</requestVersion>
    <headerVersion>1.0</headerVersion>
  </header>
  <user>
    <login>technicalUser</login>
    <passwordHash>SHA512_HASH</passwordHash>
    <taxNumber>12345678</taxNumber>
    <requestSignature>COMPUTED_SIGNATURE</requestSignature>
  </user>
  <software>
    <softwareId>ILUMINATI-V4</softwareId>
    <softwareName>ILUMINATI SYSTEM</softwareName>
    <softwareOperation>LOCAL_SOFTWARE</softwareOperation>
    <softwareMainVersion>5.0</softwareMainVersion>
    <softwareDevName>ILUMINATI Team</softwareDevName>
    <softwareDevContact>support@iluminati.sk</softwareDevContact>
  </software>
  <taxNumber>12345678</taxNumber>
</QueryTaxpayerRequest>
```

#### Algoritmus podpisu

```python
import hashlib
from datetime import datetime

def compute_request_signature(request_id: str, timestamp: str, signing_key: str) -> str:
    """
    Výpočet SHA-512 podpisu pre NAV API
    """
    # Formát: requestId + timestamp (bez špeciálnych znakov) + signingKey
    timestamp_clean = timestamp.replace("-", "").replace(":", "").replace(".", "").replace("T", "").replace("Z", "")
    data = f"{request_id}{timestamp_clean}{signing_key}"
    return hashlib.sha512(data.encode('utf-8')).hexdigest().upper()
```

#### Response

```xml
<QueryTaxpayerResponse>
  <result>
    <funcCode>OK</funcCode>
  </result>
  <taxpayerValidity>true</taxpayerValidity>
  <taxpayerData>
    <taxpayerName>MAGYAR CÉG KFT.</taxpayerName>
    <taxpayerAddress>
      <countryCode>HU</countryCode>
      <postalCode>1234</postalCode>
      <city>Budapest</city>
      <streetName>Váci út</streetName>
      <publicPlaceCategory>utca</publicPlaceCategory>
      <number>1</number>
    </taxpayerAddress>
  </taxpayerData>
</QueryTaxpayerResponse>
```

### 5.3 e-Beszámoló - Finančné výkazy

- **URL:** <https://e-beszamolo.im.gov.hu/>
- **API:** Žiadne verejné
- **Prístup:** Zmluva s ministerstvom

---

## 6. Integračná stratégia

### 6.1 Architektúra V4 Middleware

```text
┌─────────────────────────────────────────────────────────────┐
│                    ILUMINATI SYSTEM                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │   Frontend  │───▶│  API Layer  │───▶│  Middleware │      │
│  │   (React)   │    │  (FastAPI)  │    │   (Router)  │      │
│  └─────────────┘    └─────────────┘    └──────┬──────┘      │
│                                               │              │
│         ┌─────────────────────────────────────┼──────────┐  │
│         │                                     │          │  │
│         ▼                                     ▼          ▼  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────┐ │
│  │  SK Client  │  │  CZ Client  │  │  PL Client  │  │ HU │ │
│  │ (RPO/RUZ)   │  │  (ARES v2)  │  │ (KRS/CEIDG) │  │NAV │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Normalizovaný dátový model

```python
from dataclasses import dataclass
from typing import Optional, List
from datetime import date

@dataclass
class NormalizedCompany:
    """Jednotný model pre všetky V4 krajiny"""

    # Identifikátory
    country: str  # SK, CZ, PL, HU
    primary_id: str  # IČO, KRS, Adószám
    tax_id: Optional[str] = None  # DIČ, NIP, Adószám
    vat_id: Optional[str] = None  # IČ DPH, EU VAT

    # Základné údaje
    legal_name: str
    legal_form: Optional[str] = None
    status: str  # active, liquidation, bankrupt, dissolved

    # Adresa
    street: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None

    # Dátumy
    registration_date: Optional[date] = None
    dissolution_date: Optional[date] = None

    # Osoby
    executives: List[str] = None
    shareholders: List[str] = None

    # Risk
    risk_score: int = 0
    risk_flags: List[str] = None

    # Metadata
    source_api: str
    fetched_at: str
    raw_data: dict = None
```

### 6.3 Mapovanie identifikátorov

| Krajina | Primárny ID | Formát      | Validácia |
| ------- | ----------- | ----------- | --------- |
| SK      | IČO         | 8 číslic    | Modulo 11 |
| CZ      | IČO         | 8-9 číslic  | Modulo 11 |
| PL      | KRS         | 10 číslic   | -         |
| PL      | NIP         | 10 číslic   | Modulo 11 |
| PL      | REGON       | 9/14 číslic | Modulo 11 |
| HU      | Adószám     | 8-11 číslic | Modulo 11 |

### 6.4 Error Handling

```python
class V4APIError(Exception):
    """Základná chyba pre V4 API"""
    pass

class RateLimitError(V4APIError):
    """HTTP 429 - prekročený limit"""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after

class AuthenticationError(V4APIError):
    """Chyba autentifikácie"""
    pass

class NotFoundError(V4APIError):
    """Subjekt neexistuje"""
    pass

# Exponenciálny backoff
async def fetch_with_retry(url: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = await client.get(url)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise RateLimitError(retry_after)
            return response.json()
        except RateLimitError as e:
            wait_time = e.retry_after * (2 ** attempt)
            await asyncio.sleep(wait_time)
    raise V4APIError("Max retries exceeded")
```

---

## 7. Implementačné príklady

### 7.1 SK - RPO Client

```python
import httpx
from typing import Optional, Dict

class SKRPOClient:
    """Klient pre slovenský Register právnických osôb"""

    BASE_URL = "https://data.slovensko.sk/api"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def search_by_ico(self, ico: str) -> Dict:
        """Vyhľadanie podľa IČO"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/legal-subjects",
                params={"ico": ico},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def sync_changes(self, since: str, only_ids: bool = False) -> Dict:
        """Synchronizácia zmien od určitého času"""
        params = {"since": since}
        if only_ids:
            params["only_ids"] = "true"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/sync",
                params=params,
                headers=self.headers
            )
            return response.json()
```

### 7.2 CZ - ARES Client

```python
class CZARESClient:
    """Klient pre český ARES v2"""

    BASE_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest"

    async def search_by_ico(self, ico: str) -> Dict:
        """Vyhľadanie podľa IČO"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/ekonomicke-subjekty/vyhledat",
                json={"ico": ico},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError(retry_after)

            response.raise_for_status()
            return response.json()

    async def search_by_name(self, name: str, limit: int = 10) -> Dict:
        """Vyhľadanie podľa názvu"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/ekonomicke-subjekty/vyhledat",
                json={"obchodniJmeno": name, "pocet": limit}
            )
            return response.json()
```

### 7.3 PL - KRS Client

```python
class PLKRSClient:
    """Klient pre poľský KRS"""

    BASE_URL = "https://api-krs.ms.gov.pl/api/krs"

    async def get_current_extract(self, krs: str) -> Dict:
        """Aktuálny výpis"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/OdpisAktualny/{krs}",
                params={"rejestr": "P", "format": "json"}
            )
            return response.json()

    async def get_full_history(self, krs: str) -> Dict:
        """Úplná história"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/OdpisPelny/{krs}",
                params={"rejestr": "P", "format": "json"}
            )
            return response.json()

    async def get_daily_bulletin(self, date: str) -> Dict:
        """Denný bulletin zmien (YYYY-MM-DD)"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/Biuletyn/{date}")
            return response.json()
```

### 7.4 PL - Biała Lista Client

```python
class PLBialaListaClient:
    """Klient pre poľskú Bielu listinu VAT"""

    BASE_URL = "https://wl-api.mf.gov.pl"

    async def check_vat_status(self, nip: str, date: str) -> Dict:
        """Overenie VAT statusu"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/api/search/nip/{nip}",
                params={"date": date}
            )
            return response.json()

    async def verify_bank_account(self, nip: str, account: str, date: str) -> Dict:
        """Overenie bankového účtu"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/api/check/nip/{nip}/bank-account/{account}",
                params={"date": date}
            )
            return response.json()
```

### 7.5 HU - NAV Client

```python
import hashlib
from datetime import datetime
import uuid

class HUNAVClient:
    """Klient pre maďarský NAV Online Számla"""

    BASE_URL = "https://api.onlineszamla.nav.gov.hu/invoiceService/v3"

    def __init__(self, login: str, password: str, signing_key: str, tax_number: str):
        self.login = login
        self.password_hash = hashlib.sha512(password.encode()).hexdigest().upper()
        self.signing_key = signing_key
        self.tax_number = tax_number

    def _compute_signature(self, request_id: str, timestamp: str) -> str:
        """Výpočet SHA-512 podpisu"""
        ts_clean = timestamp.replace("-", "").replace(":", "").replace(".", "").replace("T", "").replace("Z", "")
        data = f"{request_id}{ts_clean}{self.signing_key}"
        return hashlib.sha512(data.encode()).hexdigest().upper()

    async def query_taxpayer(self, tax_number: str) -> Dict:
        """Overenie existencie daňovníka"""
        request_id = f"RID{uuid.uuid4().hex[:20].upper()}"
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        signature = self._compute_signature(request_id, timestamp)

        xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
        <QueryTaxpayerRequest xmlns="http://schemas.nav.gov.hu/OSA/3.0/api">
            <header>
                <requestId>{request_id}</requestId>
                <timestamp>{timestamp}</timestamp>
                <requestVersion>3.0</requestVersion>
                <headerVersion>1.0</headerVersion>
            </header>
            <user>
                <login>{self.login}</login>
                <passwordHash>{self.password_hash}</passwordHash>
                <taxNumber>{self.tax_number}</taxNumber>
                <requestSignature>{signature}</requestSignature>
            </user>
            <software>
                <softwareId>ILUMINATI-V4</softwareId>
                <softwareName>ILUMINATI SYSTEM</softwareName>
                <softwareOperation>LOCAL_SOFTWARE</softwareOperation>
                <softwareMainVersion>5.0</softwareMainVersion>
                <softwareDevName>ILUMINATI Team</softwareDevName>
                <softwareDevContact>support@iluminati.sk</softwareDevContact>
            </software>
            <taxNumber>{tax_number}</taxNumber>
        </QueryTaxpayerRequest>"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/queryTaxpayer",
                content=xml_request,
                headers={"Content-Type": "application/xml"}
            )
            return self._parse_xml_response(response.text)
```

---

## 📚 Referencie

1. Slovensko.Digital Ekosystém: <https://ekosystem.slovensko.digital/>
2. ARES v2 Dokumentácia: <https://ares.gov.cz/stranky/dokumentace-api>
3. KRS API: <https://api-krs.ms.gov.pl/>
4. Biała Lista: <https://www.podatki.gov.pl/wykaz-podatnikow-vat-api/>
5. NAV Online Számla: <https://onlineszamla.nav.gov.hu/>

---
