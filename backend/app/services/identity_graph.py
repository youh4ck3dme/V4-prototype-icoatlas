"""
V4 Identity Graph System
Resolves company lookups with multi-identifier support, caching, and merge logic.
Uses PostgreSQL for persistent storage.
"""
import os
import re
import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List, Tuple

try:
    import psycopg
    from psycopg.rows import dict_row
    PSYCOPG_VERSION = 3
except ImportError:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG_VERSION = 2


# -----------------------------
#  Canonicalization helpers
# -----------------------------

def normalize(s: str) -> str:
    s = s.strip().upper()
    s = re.sub(r"[\s\u00A0]+", "", s)
    return s

def digits_only(s: str) -> str:
    return re.sub(r"\D+", "", s)

def pl_nip_checksum_ok(nip10: str) -> bool:
    if not re.fullmatch(r"\d{10}", nip10):
        return False
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    total = sum(int(nip10[i]) * weights[i] for i in range(9))
    chk = total % 11
    if chk == 10:
        return False
    return chk == int(nip10[9])


@dataclass
class Candidate:
    country: str
    id_type: str
    value: str
    confidence: float


@dataclass
class ClassifiedInput:
    raw: str
    normalized: str
    digits: str
    primary: Optional[Candidate]
    candidates: List[Candidate]


def classify_v4(value: str, country_hint: Optional[str] = None) -> ClassifiedInput:
    raw = value
    s = normalize(value)
    d = digits_only(s)
    hint = country_hint.upper() if country_hint else None

    cands: List[Candidate] = []

    # VAT prefix (hard match)
    if re.fullmatch(r"SK\d{10}", s):
        return ClassifiedInput(raw, s, d, Candidate("SK", "VAT", s, 1.0), [])
    if re.fullmatch(r"CZ\d{8,10}", s):
        return ClassifiedInput(raw, s, d, Candidate("CZ", "VAT", s, 1.0), [])
    if re.fullmatch(r"PL\d{10}", s):
        return ClassifiedInput(raw, s, d, Candidate("PL", "VAT", s, 1.0), [])

    # HU explicit patterns
    if re.fullmatch(r"\d{8}-\d-\d{2}", s):
        return ClassifiedInput(raw, s, d, Candidate("HU", "ADOSZAM", s, 1.0), [])
    if re.fullmatch(r"\d{2}-\d{2}-\d{6}", s):
        return ClassifiedInput(raw, s, d, Candidate("HU", "CEGJEGYZEKSZAM", s, 1.0), [])

    # digits-only HU Adószám (11)
    if re.fullmatch(r"\d{11}", d):
        value_fmt = f"{d[:8]}-{d[8]}-{d[9:]}"
        primary = Candidate("HU", "ADOSZAM", value_fmt, 0.9 if (not hint or hint == "HU") else 0.6)
        return ClassifiedInput(raw, s, d, primary, [])

    # 8 digits => SK/CZ ICO collision
    if re.fullmatch(r"\d{8}", d):
        if hint in ("SK", "CZ"):
            primary = Candidate(hint, "ICO", d, 0.8)
            cands = [Candidate("SK", "ICO", d, 0.8 if hint == "SK" else 0.2),
                     Candidate("CZ", "ICO", d, 0.8 if hint == "CZ" else 0.2)]
            return ClassifiedInput(raw, s, d, primary, cands)

        cands = [Candidate("SK", "ICO", d, 0.55), Candidate("CZ", "ICO", d, 0.45)]
        return ClassifiedInput(raw, s, d, None, cands)

    # PL REGON
    if re.fullmatch(r"\d{9}", d) or re.fullmatch(r"\d{14}", d):
        return ClassifiedInput(raw, s, d, Candidate("PL", "REGON", d, 0.95), [])

    # 10 digits => PL NIP/KRS OR SK DIC (ambiguous)
    if re.fullmatch(r"\d{10}", d):
        if hint == "SK":
            return ClassifiedInput(raw, s, d, Candidate("SK", "DIC", d, 0.75),
                                   [Candidate("SK", "DIC", d, 0.75), Candidate("PL", "NIP", d, 0.20), Candidate("PL", "KRS", d, 0.05)])

        if hint == "PL":
            if pl_nip_checksum_ok(d):
                return ClassifiedInput(raw, s, d, Candidate("PL", "NIP", d, 0.9), [])
            return ClassifiedInput(raw, s, d, Candidate("PL", "KRS", d, 0.65),
                                   [Candidate("PL", "KRS", d, 0.65), Candidate("PL", "NIP", d, 0.25), Candidate("SK", "DIC", d, 0.10)])

        if pl_nip_checksum_ok(d):
            return ClassifiedInput(raw, s, d, Candidate("PL", "NIP", d, 0.85), [])
        return ClassifiedInput(raw, s, d, None,
                               [Candidate("PL", "KRS", d, 0.50), Candidate("SK", "DIC", d, 0.35), Candidate("PL", "NIP", d, 0.15)])

    return ClassifiedInput(raw, s, d, None, [])


# -----------------------------
#  Identity Graph Store
# -----------------------------

class IdentityGraph:
    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn or os.getenv("DATABASE_URL") or os.getenv("DB_DSN")
        if not self.dsn:
            raise RuntimeError("Missing DATABASE_URL / DB_DSN for IdentityGraph")
        
        if PSYCOPG_VERSION == 3:
            self.conn = psycopg.connect(self.dsn, row_factory=dict_row)
        else:
            self.conn = psycopg2.connect(self.dsn, cursor_factory=RealDictCursor)

    def close(self):
        self.conn.close()

    def _cursor(self):
        if PSYCOPG_VERSION == 3:
            return self.conn.cursor()
        else:
            return self.conn.cursor(cursor_factory=RealDictCursor)

    def find_atlas_id(self, country: str, id_type: str, value_digits: str) -> Optional[str]:
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT atlas_id
                FROM company_identifiers
                WHERE country = %s AND id_type = %s AND value_digits = %s
                """,
                (country, id_type, value_digits),
            )
            row = cur.fetchone()
            return str(row["atlas_id"]) if row else None

    def get_company(self, atlas_id: str) -> Optional[Dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM atlas_companies WHERE atlas_id = %s", (atlas_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_identifiers(self, atlas_id: str) -> List[Dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT country, id_type, value, value_digits, is_primary, source FROM company_identifiers WHERE atlas_id = %s",
                (atlas_id,)
            )
            return [dict(r) for r in cur.fetchall()]

    def completeness_score(self, company_row: Dict[str, Any]) -> int:
        fields = ["legal_name", "status", "legal_form", "registration_number", "street", "city", "postal_code", "region",
                  "capital_amount", "capital_currency", "employees_range", "nace_codes"]
        score = 0
        for f in fields:
            v = company_row.get(f)
            if v is None:
                continue
            if isinstance(v, str) and v.strip() == "":
                continue
            score += 1
        return score

    def merge(self, survivor: str, merged: str, reason: str = "identifier_conflict"):
        with self._cursor() as cur:
            cur.execute(
                "UPDATE company_identifiers SET atlas_id = %s, last_seen_at = now() WHERE atlas_id = %s",
                (survivor, merged),
            )
            cur.execute(
                "UPDATE company_sources SET atlas_id = %s WHERE atlas_id = %s",
                (survivor, merged),
            )
            cur.execute(
                "INSERT INTO company_merges (survivor_atlas_id, merged_atlas_id, reason) VALUES (%s, %s, %s)",
                (survivor, merged, reason),
            )
            cur.execute("DELETE FROM atlas_companies WHERE atlas_id = %s", (merged,))
        self.conn.commit()

    def upsert_company(
        self,
        country: str,
        company: Dict[str, Any],
        identifiers: List[Tuple[str, str, str, str, bool, str]],
        source_payload: Optional[Dict[str, Any]] = None,
        source_system: Optional[str] = None,
        source_ref: Optional[str] = None,
        request_id: Optional[str] = None,
        http_status: Optional[int] = None,
    ) -> str:
        """
        Insert/Update company + identifiers.
        Conflict detection triggers merge.
        """
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO atlas_companies
                  (country, legal_name, status, legal_form, registration_number,
                   street, city, postal_code, region,
                   capital_amount, capital_currency, employees_range,
                   nace_codes, source_api, fetched_at, updated_at)
                VALUES
                  (%s, %s, %s, %s, %s,
                   %s, %s, %s, %s,
                   %s, %s, %s,
                   %s, %s, now(), now())
                RETURNING atlas_id
                """,
                (
                    country,
                    company.get("legal_name"),
                    company.get("status"),
                    company.get("legal_form"),
                    company.get("registration_number"),
                    company.get("street"),
                    company.get("city"),
                    company.get("postal_code"),
                    company.get("region"),
                    company.get("capital_amount"),
                    company.get("capital_currency"),
                    company.get("employees_range"),
                    company.get("nace_codes"),
                    company.get("source_api"),
                ),
            )
            atlas_id = str(cur.fetchone()["atlas_id"])

            if source_payload is not None and source_system:
                payload_json = json.dumps(source_payload) if isinstance(source_payload, dict) else source_payload
                cur.execute(
                    """
                    INSERT INTO company_sources (atlas_id, source_system, source_ref, request_id, http_status, payload)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (atlas_id, source_system, source_ref, request_id, http_status, payload_json),
                )

            for (icountry, itype, ival, idigits, is_primary, src) in identifiers:
                cur.execute(
                    """
                    SELECT atlas_id FROM company_identifiers
                    WHERE country=%s AND id_type=%s AND value_digits=%s
                    """,
                    (icountry, itype, idigits),
                )
                existing = cur.fetchone()
                if existing and str(existing["atlas_id"]) != atlas_id:
                    existing_company = self.get_company(str(existing["atlas_id"]))
                    existing_score = self.completeness_score(existing_company) if existing_company else 0
                    new_score = sum(1 for k, v in company.items() if v not in (None, "", []))

                    survivor = str(existing["atlas_id"]) if existing_score >= new_score else atlas_id
                    merged = atlas_id if survivor == str(existing["atlas_id"]) else str(existing["atlas_id"])

                    self.conn.commit()
                    self.merge(survivor, merged, reason=f"identifier_conflict:{icountry}:{itype}:{idigits}")
                    return survivor

                cur.execute(
                    """
                    INSERT INTO company_identifiers
                      (atlas_id, country, id_type, value, value_digits, is_primary, source, first_seen_at, last_seen_at)
                    VALUES
                      (%s, %s, %s, %s, %s, %s, %s, now(), now())
                    ON CONFLICT (country, id_type, value_digits)
                    DO UPDATE SET
                      atlas_id = EXCLUDED.atlas_id,
                      value = EXCLUDED.value,
                      is_primary = EXCLUDED.is_primary OR company_identifiers.is_primary,
                      source = COALESCE(EXCLUDED.source, company_identifiers.source),
                      last_seen_at = now()
                    """,
                    (atlas_id, icountry, itype, ival, idigits, is_primary, src),
                )

        self.conn.commit()
        return atlas_id


# -----------------------------
#  Provider Fetch Glue (V4 Services)
# -----------------------------

async def v4_provider_fetch(country: str, id_type: str, value: str) -> Tuple[Optional[Dict], List[Tuple], Optional[Dict], Dict]:
    """
    Fetch company from V4 providers.
    Returns: (company_dict, identifiers_list, source_payload, meta)
    """
    from ..services.ruz_service import RuzService
    from ..services.ares_service import AresService
    from ..services.krs_playwright_service import KRSPlaywrightService
    from ..services.nav_playwright_service import NAVPlaywrightService
    import httpx
    
    company_dict = None
    identifiers = []
    source_payload = None
    meta = {"source_system": None, "source_ref": None, "http_status": None}
    
    try:
        if country == "SK":
            async with httpx.AsyncClient() as client:
                service = RuzService(client)
                result = await service.fetch_company(value)
            
            company_dict = {
                "legal_name": result.name,
                "status": result.status,
                "street": result.address,
                "source_api": "RUZ",
            }
            identifiers = [
                (country, id_type, value, digits_only(value), True, "RUZ"),
            ]
            source_payload = result.raw_data if hasattr(result, "raw_data") else None
            meta = {"source_system": "RUZ", "source_ref": f"/ruz/{value}", "http_status": 200}
        
        elif country == "CZ":
            async with httpx.AsyncClient() as client:
                service = AresService(client)
                result = await service.fetch_company(value)
            
            company_dict = {
                "legal_name": result.name,
                "status": result.status,
                "street": result.address,
                "source_api": "ARES",
            }
            identifiers = [
                (country, id_type, value, digits_only(value), True, "ARES"),
            ]
            source_payload = result.raw_data if hasattr(result, "raw_data") else None
            meta = {"source_system": "ARES", "source_ref": f"/ares/{value}", "http_status": 200}
        
        elif country == "PL":
            service = KRSPlaywrightService()
            result = await service.fetch_company(value)
            
            company_dict = {
                "legal_name": result.name,
                "status": result.status,
                "street": result.address,
                "source_api": "biznes.gov.pl",
            }
            identifiers = [
                (country, id_type, value, digits_only(value), True, "biznes.gov.pl"),
            ]
            source_payload = result.raw_data if hasattr(result, "raw_data") else None
            meta = {"source_system": "biznes.gov.pl", "source_ref": f"/pl/{value}", "http_status": 200}
        
        elif country == "HU":
            service = NAVPlaywrightService()
            # Format for HU Cégjegyzékszám
            formatted_value = value
            if id_type == "CEGJEGYZEKSZAM" and len(digits_only(value)) == 10:
                d = digits_only(value)
                formatted_value = f"{d[:2]}-{d[2:4]}-{d[4:]}"
            
            result = await service.fetch_company(formatted_value)
            
            company_dict = {
                "legal_name": result.name,
                "status": result.status,
                "street": result.address,
                "source_api": "companyregister.hu",
            }
            identifiers = [
                (country, id_type, formatted_value, digits_only(value), True, "companyregister.hu"),
            ]
            source_payload = result.raw_data if hasattr(result, "raw_data") else None
            meta = {"source_system": "companyregister.hu", "source_ref": f"/hu/{formatted_value}", "http_status": 200}
    
    except Exception as e:
        meta["http_status"] = 404
        return None, [], None, meta
    
    return company_dict, identifiers, source_payload, meta


# -----------------------------
#  Resolver orchestration
# -----------------------------

async def resolve_company_v4(
    input_value: str,
    country_hint: Optional[str] = None,
    db_dsn: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main resolver: classify -> cache lookup -> provider fetch -> upsert.
    Returns: {atlas_id, company, detected, used_fallback, tried, identifiers}
    """
    
    classified = classify_v4(input_value, country_hint)
    
    tried: List[Dict[str, Any]] = []
    used_fallback = False
    
    # Check if we have DB configured
    has_db = bool(db_dsn or os.getenv("DATABASE_URL") or os.getenv("DB_DSN"))
    
    if has_db:
        graph = IdentityGraph(db_dsn)
        try:
            # Cache lookup first
            if classified.primary:
                cand = classified.primary
                aid = graph.find_atlas_id(cand.country, cand.id_type, digits_only(cand.value))
                tried.append({"mode": "cache_lookup", "country": cand.country, "id_type": cand.id_type, "hit": bool(aid)})
                if aid:
                    return {
                        "atlas_id": aid,
                        "company": graph.get_company(aid),
                        "identifiers": graph.get_identifiers(aid),
                        "detected": asdict(cand),
                        "used_fallback": False,
                        "tried": tried,
                    }

            for cand in classified.candidates:
                aid = graph.find_atlas_id(cand.country, cand.id_type, digits_only(cand.value))
                tried.append({"mode": "cache_lookup", "country": cand.country, "id_type": cand.id_type, "hit": bool(aid)})
                if aid:
                    return {
                        "atlas_id": aid,
                        "company": graph.get_company(aid),
                        "identifiers": graph.get_identifiers(aid),
                        "detected": asdict(cand),
                        "used_fallback": True,
                        "tried": tried,
                    }
        finally:
            graph.close()

    # Provider fetch
    fetch_plan: List[Candidate] = []
    if classified.primary:
        fetch_plan.append(classified.primary)
    fetch_plan.extend(classified.candidates)

    for i, cand in enumerate(fetch_plan):
        company, id_list, raw_payload, meta = await v4_provider_fetch(cand.country, cand.id_type, cand.value)
        tried.append({"mode": "provider_fetch", "country": cand.country, "id_type": cand.id_type, "ok": bool(company)})

        if not company:
            continue

        used_fallback = (i > 0)
        
        # Upsert to DB if available
        atlas_id = None
        identifiers = []
        if has_db:
            graph = IdentityGraph(db_dsn)
            try:
                atlas_id = graph.upsert_company(
                    country=cand.country,
                    company=company,
                    identifiers=id_list,
                    source_payload=raw_payload,
                    source_system=meta.get("source_system"),
                    source_ref=meta.get("source_ref"),
                    request_id=input_value,
                    http_status=meta.get("http_status"),
                )
                identifiers = graph.get_identifiers(atlas_id)
                company = graph.get_company(atlas_id)
            finally:
                graph.close()

        return {
            "atlas_id": atlas_id,
            "company": company,
            "identifiers": identifiers or id_list,
            "detected": asdict(cand),
            "used_fallback": used_fallback,
            "tried": tried,
        }

    return {
        "atlas_id": None,
        "company": None,
        "identifiers": [],
        "detected": None,
        "used_fallback": False,
        "tried": tried,
        "error": "NOT_FOUND"
    }
