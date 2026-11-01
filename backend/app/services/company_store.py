"""
Zápis obohatených dát (financials, risk, IBAN) do atlas_companies.

Firma sa nájde cez company_identifiers (country, id_type, value_digits).
Ak ešte neexistuje, založí sa minimálny riadok + identifikátor, aby bolo kam dáta uložiť.
Surová odpoveď zdroja ide do company_sources (audit).

Synchrónne (psycopg), rovnako ako identity_graph.py / graph_service.py.
Z async endpointov volať cez run_in_threadpool.
"""
import json
import os
import re
from typing import Any, Dict, Optional

try:
    import psycopg
    from psycopg.rows import dict_row
    PSYCOPG_VERSION = 3
except ImportError:  # pragma: no cover - závisí od prostredia
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG_VERSION = 2


def database_configured() -> bool:
    """Zápis len ak je DATABASE_URL / DB_DSN explicitne nastavené (settings má localhost default)."""
    return bool(os.getenv("DATABASE_URL") or os.getenv("DB_DSN"))


def _normalize_dsn(dsn: str) -> str:
    for prefix in ("postgresql+asyncpg://", "postgres+asyncpg://"):
        if dsn.startswith(prefix):
            return "postgresql://" + dsn[len(prefix):]
    return dsn


def _digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")


class CompanyStore:
    def __init__(self, dsn: Optional[str] = None):
        dsn = dsn or os.getenv("DATABASE_URL") or os.getenv("DB_DSN")
        if not dsn:
            raise RuntimeError("Missing DATABASE_URL / DB_DSN for CompanyStore")
        dsn = _normalize_dsn(dsn)
        if PSYCOPG_VERSION == 3:
            self.conn = psycopg.connect(dsn, row_factory=dict_row)
        else:
            self.conn = psycopg2.connect(dsn, cursor_factory=RealDictCursor)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "CompanyStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def ensure_company(self, country: str, id_type: str, value: str,
                       legal_name: Optional[str] = None, source: Optional[str] = None) -> str:
        digits = _digits(value)
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT atlas_id FROM company_identifiers WHERE country=%s AND id_type=%s AND value_digits=%s",
                (country, id_type, digits),
            )
            row = cur.fetchone()
            if row:
                return str(row["atlas_id"])

            cur.execute(
                """
                INSERT INTO atlas_companies (country, legal_name, source_api, fetched_at, updated_at)
                VALUES (%s, %s, %s, now(), now())
                RETURNING atlas_id
                """,
                (country, legal_name, source),
            )
            atlas_id = str(cur.fetchone()["atlas_id"])
            cur.execute(
                """
                INSERT INTO company_identifiers (atlas_id, country, id_type, value, value_digits, is_primary, source)
                VALUES (%s, %s, %s, %s, %s, true, %s)
                ON CONFLICT (country, id_type, value_digits) DO NOTHING
                """,
                (atlas_id, country, id_type, value, digits, source),
            )
            if cur.rowcount == 0:
                # súbežný zápis vyhral; použi jeho firmu
                self.conn.rollback()
                return self.ensure_company(country, id_type, value, legal_name, source)
        self.conn.commit()
        return atlas_id

    def _add_source(self, cur, atlas_id: str, source_system: str, request_id: str, payload: Any) -> None:
        cur.execute(
            """
            INSERT INTO company_sources (atlas_id, source_system, source_ref, request_id, http_status, payload)
            VALUES (%s, %s, %s, %s, 200, %s::jsonb)
            """,
            (atlas_id, source_system, f"/{source_system.lower()}/{request_id}", request_id, json.dumps(payload)),
        )

    def save_financials(self, atlas_id: str, financials: Dict[str, Any], request_id: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE atlas_companies
                SET financials = %s::jsonb, last_financial_year = %s, updated_at = now()
                WHERE atlas_id = %s
                """,
                (json.dumps(financials), financials.get("year"), atlas_id),
            )
            self._add_source(cur, atlas_id, "RUZ_FINANCIALS", request_id, financials)
        self.conn.commit()

    def get_company(self, atlas_id: str) -> Optional[Dict[str, Any]]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM atlas_companies WHERE atlas_id = %s", (atlas_id,))
            row = cur.fetchone()
            return dict(row) if row else None
