"""
CompanyStore against a disposable Postgres (TEST_DATABASE_URL), migrations applied like production.
"""
import os
from pathlib import Path

import pytest

psycopg2 = pytest.importorskip("psycopg2")

DSN = os.getenv("TEST_DATABASE_URL")
MIGRATIONS = sorted((Path(__file__).resolve().parents[1] / "migrations").glob("*.sql"))

pytestmark = pytest.mark.skipif(not DSN, reason="TEST_DATABASE_URL not set")


@pytest.fixture()
def store():
    from backend.app.services.company_store import CompanyStore

    c = psycopg2.connect(DSN)
    c.autocommit = True
    with c.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        for path in MIGRATIONS:
            cur.execute(path.read_text(encoding="utf-8"))
    c.close()
    s = CompanyStore(DSN)
    yield s
    s.close()


def test_ensure_company_is_idempotent(store):
    a = store.ensure_company("SK", "ICO", "12345678", source="RUZ")
    b = store.ensure_company("SK", "ICO", "12345678", source="RUZ")
    assert a == b
    with store.conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM atlas_companies")
        assert cur.fetchone()["n"] == 1


def test_save_financials_sets_columns_and_audit(store):
    atlas_id = store.ensure_company("SK", "ICO", "12345678", source="RUZ")
    fin = {"ico": "12345678", "year": 2024, "template": "699", "assets": 36539.0, "history": [
        {"year": 2024, "template": "699", "available": True, "assets": 36539.0},
        {"year": 2023, "template": "699", "available": True, "assets": 31840.0},
    ]}
    store.save_financials(atlas_id, fin, request_id="12345678")

    row = store.get_company(atlas_id)
    assert row["last_financial_year"] == 2024
    assert row["financials"]["assets"] == 36539.0
    assert len(row["financials"]["history"]) == 2
    with store.conn.cursor() as cur:
        cur.execute("SELECT source_system FROM company_sources WHERE atlas_id = %s", (atlas_id,))
        assert [r["source_system"] for r in cur.fetchall()] == ["RUZ_FINANCIALS"]


def test_endpoint_persists_when_database_configured(store, monkeypatch):
    import httpx
    from fastapi.testclient import TestClient

    from backend.app.api.endpoints import search_sk
    from backend.app.core import circuit_breaker
    from backend.app.main import app
    from backend.app.services.cache_service import cache_service
    from backend.tests.test_ruz_financials import make_ruz_handler

    monkeypatch.setenv("DATABASE_URL", DSN)
    circuit_breaker._breakers.clear()
    cache_service.in_memory.clear()
    handler = make_ruz_handler()

    async def client_override():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            yield c

    app.dependency_overrides[search_sk.get_httpx_client] = client_override
    try:
        with TestClient(app) as tc:
            body = tc.get("/api/sk/company/12345678/financials").json()
    finally:
        app.dependency_overrides.clear()
        cache_service.in_memory.clear()

    assert body["atlas_id"]
    row = store.get_company(body["atlas_id"])
    assert row["last_financial_year"] == 2024 and row["financials"]["template"] == "699"


def test_save_iban_check_sets_columns_without_personal_names(store):
    atlas_id = store.ensure_company("SK", "ICO", "12345678", source="FS")
    store.save_iban_check(
        atlas_id,
        {"registered": True, "ibans": ["SK3112000000198742637541"], "vat_ids": ["SK2020000000"],
         "list_updated": "2026-11-01", "checked_at": "2026-11-01T00:00:00+00:00", "source": "FS_OPENDATA",
         "attribution": "x", "ico": "12345678"},
        request_id="12345678",
    )
    row = store.get_company(atlas_id)
    assert row["iban_verified"] is True and row["iban_verified_at"] is not None
    with store.conn.cursor() as cur:
        cur.execute("SELECT payload FROM company_sources WHERE atlas_id = %s AND source_system = 'FS_IBAN'", (atlas_id,))
        payload = cur.fetchone()["payload"]
    assert payload["ibans"] == ["SK3112000000198742637541"]
    assert set(payload) == {"ibans", "vat_ids", "list_updated", "checked_at", "source"}


def test_endpoint_cached_response_keeps_atlas_id_and_history_survives_smaller_years(store, monkeypatch):
    import httpx
    from fastapi.testclient import TestClient

    from backend.app.api.endpoints import search_sk
    from backend.app.core import circuit_breaker
    from backend.app.main import app
    from backend.app.services.cache_service import cache_service
    from backend.tests.test_ruz_financials import make_ruz_handler

    monkeypatch.setenv("DATABASE_URL", DSN)
    circuit_breaker._breakers.clear()
    cache_service.in_memory.clear()
    handler = make_ruz_handler()

    async def client_override():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            yield c

    app.dependency_overrides[search_sk.get_httpx_client] = client_override
    try:
        with TestClient(app) as tc:
            first = tc.get("/api/sk/company/12345678/financials").json()
            again = tc.get("/api/sk/company/12345678/financials").json()
            tc.get("/api/sk/company/12345678/financials", params={"years": 1}).json()
    finally:
        app.dependency_overrides.clear()
        cache_service.in_memory.clear()

    assert again["cached"] is True and again["atlas_id"] == first["atlas_id"]
    row = store.get_company(first["atlas_id"])
    assert [h["year"] for h in row["financials"]["history"]] == [2024, 2023, 2022]
    assert row["last_financial_year"] == 2024
