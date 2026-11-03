"""
Používatelia, API kľúče, história vyhľadávaní a obľúbené firmy (tabuľky z 2026_11_03_users_and_auth.sql).

Synchrónne (psycopg) ako company_store.py; z async endpointov volať cez run_in_threadpool.
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from .company_store import PSYCOPG_VERSION, _normalize_dsn

if PSYCOPG_VERSION == 3:  # pragma: no cover - závisí od prostredia
    import psycopg
    from psycopg.rows import dict_row
else:
    import psycopg2
    from psycopg2.extras import RealDictCursor


class EmailTakenError(Exception):
    pass


def _iso(v: Any) -> Any:
    return v.isoformat() if isinstance(v, datetime) else v


def public_user(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "email": row["email"],
        "full_name": row.get("full_name"),
        "tier": row["tier"],
        "is_active": row["is_active"],
        "is_verified": row["is_verified"],
    }


def public_api_key(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "prefix": row["prefix"],
        "permissions": list(row.get("permissions") or []),
        "created_at": _iso(row["created_at"]),
        "expires_at": _iso(row.get("expires_at")),
        "last_used_at": _iso(row.get("last_used_at")),
        "is_active": row.get("revoked_at") is None,
    }


def public_favorite(row: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: row.get(k) for k in ("id", "company_identifier", "company_name", "country", "company_data",
                                   "risk_score", "risk_factors", "notes")}
    out["created_at"] = _iso(row.get("created_at"))
    out["updated_at"] = _iso(row.get("updated_at"))
    return out


def public_history(row: Dict[str, Any]) -> Dict[str, Any]:
    ts = _iso(row["created_at"])
    # Dashboard.jsx číta `timestamp`, legacy API vracalo `search_timestamp`
    return {"id": row["id"], "query": row["query"], "country": row.get("country"),
            "atlas_id": row.get("atlas_id"), "result_count": row.get("result_count"),
            "timestamp": ts, "search_timestamp": ts}


class UserStore:
    def __init__(self, dsn: Optional[str] = None):
        dsn = dsn or os.getenv("DATABASE_URL") or os.getenv("DB_DSN")
        if not dsn:
            raise RuntimeError("Missing DATABASE_URL / DB_DSN for UserStore")
        dsn = _normalize_dsn(dsn)
        if PSYCOPG_VERSION == 3:  # pragma: no cover
            self.conn = psycopg.connect(dsn, row_factory=dict_row)
        else:
            self.conn = psycopg2.connect(dsn, cursor_factory=RealDictCursor)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "UserStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _one(self, sql: str, params: tuple, commit: bool = False) -> Optional[Dict[str, Any]]:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone() if cur.description else None
        if commit:
            self.conn.commit()
        return dict(row) if row else None

    def _all(self, sql: str, params: tuple) -> List[Dict[str, Any]]:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    # ---------- users ----------
    def create_user(self, email: str, password_hash: str, full_name: Optional[str], consent_given: bool,
                    consent_ip: Optional[str], consent_user_agent: Optional[str],
                    document_versions: Optional[Dict[str, str]]) -> Dict[str, Any]:
        try:
            return self._one(
                """
                INSERT INTO users (email, password_hash, full_name, consent_given, consent_at,
                                   consent_ip, consent_user_agent, document_versions)
                VALUES (%s, %s, %s, %s, CASE WHEN %s THEN now() END, %s, %s, %s::jsonb)
                RETURNING *
                """,
                (email.strip(), password_hash, full_name, consent_given, consent_given, consent_ip,
                 consent_user_agent, json.dumps(document_versions) if document_versions else None),
                commit=True,
            )
        except Exception as e:  # unique violation (psycopg2/3 majú rôzne triedy)
            self.conn.rollback()
            if getattr(e, "pgcode", None) == "23505" or getattr(e, "sqlstate", None) == "23505":
                raise EmailTakenError(email) from e
            raise

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return self._one("SELECT * FROM users WHERE lower(email) = lower(%s)", (email.strip(),))

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self._one("SELECT * FROM users WHERE id = %s", (user_id,))

    def touch_login(self, user_id: int) -> None:
        self._one("UPDATE users SET last_login_at = now() WHERE id = %s", (user_id,), commit=True)

    # ---------- API keys ----------
    def create_api_key(self, user_id: int, name: str, prefix: str, key_hash: str,
                       permissions: List[str], expires_days: Optional[int]) -> Dict[str, Any]:
        return self._one(
            """
            INSERT INTO api_keys (user_id, name, prefix, key_hash, permissions, expires_at)
            VALUES (%s, %s, %s, %s, %s, CASE WHEN %s::int IS NULL THEN NULL
                                             ELSE now() + make_interval(days => %s::int) END)
            RETURNING *
            """,
            (user_id, name, prefix, key_hash, permissions, expires_days, expires_days),
            commit=True,
        )

    def list_api_keys(self, user_id: int) -> List[Dict[str, Any]]:
        return self._all("SELECT * FROM api_keys WHERE user_id = %s ORDER BY created_at DESC", (user_id,))

    def revoke_api_key(self, user_id: int, key_id: int) -> bool:
        row = self._one(
            "UPDATE api_keys SET revoked_at = now() WHERE id = %s AND user_id = %s AND revoked_at IS NULL "
            "RETURNING id",
            (key_id, user_id), commit=True,
        )
        return row is not None

    def user_for_api_key(self, key_hash: str) -> Optional[Dict[str, Any]]:
        row = self._one(
            """
            UPDATE api_keys SET last_used_at = now()
            WHERE key_hash = %s AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now())
            RETURNING user_id
            """,
            (key_hash,), commit=True,
        )
        return self.get_user(row["user_id"]) if row else None

    # ---------- history ----------
    def add_history(self, user_id: int, query: str, country: Optional[str], atlas_id: Optional[str],
                    result_count: Optional[int]) -> None:
        self._one(
            "INSERT INTO search_history (user_id, query, country, atlas_id, result_count) VALUES (%s,%s,%s,%s,%s)",
            (user_id, query[:200], country, atlas_id, result_count), commit=True,
        )

    def list_history(self, user_id: int, limit: int, country: Optional[str]) -> List[Dict[str, Any]]:
        if country:
            return self._all(
                "SELECT * FROM search_history WHERE user_id = %s AND country = %s ORDER BY created_at DESC LIMIT %s",
                (user_id, country.upper(), limit),
            )
        return self._all(
            "SELECT * FROM search_history WHERE user_id = %s ORDER BY created_at DESC LIMIT %s", (user_id, limit)
        )

    # ---------- favorites ----------
    def upsert_favorite(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._one(
            """
            INSERT INTO favorite_companies
              (user_id, company_identifier, company_name, country, company_data, risk_score, risk_factors, notes)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, %s)
            ON CONFLICT (user_id, company_identifier, country) DO UPDATE SET
              company_name = EXCLUDED.company_name,
              company_data = COALESCE(EXCLUDED.company_data, favorite_companies.company_data),
              risk_score = COALESCE(EXCLUDED.risk_score, favorite_companies.risk_score),
              risk_factors = COALESCE(EXCLUDED.risk_factors, favorite_companies.risk_factors),
              notes = COALESCE(EXCLUDED.notes, favorite_companies.notes),
              updated_at = now()
            RETURNING *
            """,
            (user_id, data["company_identifier"], data["company_name"], data["country"],
             json.dumps(data["company_data"]) if data.get("company_data") is not None else None,
             data.get("risk_score"),
             json.dumps(data["risk_factors"]) if data.get("risk_factors") is not None else None,
             data.get("notes")),
            commit=True,
        )

    def list_favorites(self, user_id: int, limit: Optional[int]) -> List[Dict[str, Any]]:
        return self._all(
            "SELECT * FROM favorite_companies WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit or 1000),
        )

    def remove_favorite(self, user_id: int, favorite_id: int) -> bool:
        return self._one("DELETE FROM favorite_companies WHERE id = %s AND user_id = %s RETURNING id",
                         (favorite_id, user_id), commit=True) is not None

    def is_favorite(self, user_id: int, identifier: str, country: str) -> bool:
        return self._one(
            "SELECT 1 AS x FROM favorite_companies WHERE user_id = %s AND company_identifier = %s AND country = %s",
            (user_id, identifier, country.upper()),
        ) is not None

    def update_favorite_notes(self, user_id: int, favorite_id: int, notes: str) -> Optional[Dict[str, Any]]:
        return self._one(
            "UPDATE favorite_companies SET notes = %s, updated_at = now() WHERE id = %s AND user_id = %s RETURNING *",
            (notes, favorite_id, user_id), commit=True,
        )
