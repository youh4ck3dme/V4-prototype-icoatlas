import io
import os
import secrets
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core import security
from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    generate_api_key,
    hash_api_key,
    hash_password,
    password_problem,
    verify_password,
)

DSN = os.getenv("TEST_DATABASE_URL")

# Testovacie heslá sa generujú pri spustení, aby v repozitári nebol žiadny reťazec pripomínajúci heslo.
PW = secrets.token_urlsafe(16)
PW_OTHER = secrets.token_urlsafe(16)
PW_SHORT = PW[:5]
MIGRATIONS = sorted((Path(__file__).resolve().parents[1] / "migrations").glob("*.sql"))


# ---------- security (bez DB) ----------

def test_password_hash_roundtrip_and_salt():
    h1, h2 = hash_password(PW), hash_password(PW)
    assert h1 != h2 and h1.startswith("scrypt$")
    assert verify_password(PW, h1)
    assert not verify_password(PW_OTHER, h1)
    assert not verify_password("x", "garbage")
    assert password_problem(PW_SHORT) and password_problem("x" * 300) and password_problem(PW) is None


def test_jwt_roundtrip_expiry_and_tamper():
    tok = create_access_token(42, "pro")
    assert decode_access_token(tok)["sub"] == "42"
    assert decode_access_token(tok + "x") is None
    assert decode_access_token(create_access_token(1, "free", ttl=timedelta(seconds=-1))) is None


def test_secret_key_required_in_production(monkeypatch):
    from backend.app.core.config import settings

    monkeypatch.setattr(settings, "ENV", "production")
    monkeypatch.setattr(settings, "SECRET_KEY", None)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        create_access_token(1, "free")
    monkeypatch.setattr(settings, "SECRET_KEY", "short")
    with pytest.raises(RuntimeError):
        create_access_token(1, "free")
    monkeypatch.setattr(settings, "SECRET_KEY", "CHANGE_ME_use_openssl_rand_hex_32")  # z .env.production.example
    with pytest.raises(RuntimeError):
        create_access_token(1, "free")
    monkeypatch.setattr(settings, "SECRET_KEY", "x" * 40)
    assert decode_access_token(create_access_token(1, "free"))["sub"] == "1"


def test_api_key_format():
    full, prefix, h = generate_api_key()
    assert full.startswith("ica_") and full.startswith(prefix) and len(prefix) == 12
    assert h == hash_api_key(full) and full not in h


def test_excel_export_neutralizes_formulas():
    from openpyxl import load_workbook

    from backend.app.services.export_service import export_batch_to_excel, export_to_excel

    graph = {"nodes": [{"id": "1", "type": "company", "label": "=HYPERLINK(\"http://x\")", "country": "SK"}],
             "edges": []}
    for content in (export_to_excel(graph),
                    export_batch_to_excel([{"company_name": "=1+1", "company_identifier": "12345678",
                                            "country": "SK"}])):
        wb = load_workbook(io.BytesIO(content))
        values = [c.value for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value is not None]
        assert not any(isinstance(v, str) and v.startswith("=") for v in values)
        assert any(isinstance(v, str) and v.startswith("'=") for v in values)


def test_endpoints_require_database(monkeypatch):
    from backend.app.main import app

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_DSN", raising=False)
    with TestClient(app) as tc:
        assert tc.post("/api/auth/register", json={"email": "a@b.sk", "password": PW}).status_code == 503
        assert tc.get("/api/auth/me").status_code == 401  # bez tokenu


# ---------- end-to-end s Postgresom ----------

@pytest.fixture()
def api(monkeypatch):
    if not DSN:
        pytest.skip("TEST_DATABASE_URL not set")
    psycopg2 = pytest.importorskip("psycopg2")
    c = psycopg2.connect(DSN)
    c.autocommit = True
    with c.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        for path in MIGRATIONS:
            cur.execute(path.read_text(encoding="utf-8"))
    monkeypatch.setenv("DATABASE_URL", DSN)
    from backend.app.main import app

    with TestClient(app) as tc:
        yield tc, c
    c.close()


def _register_and_login(tc, email="Jana@Firma.sk", password=PW):
    r = tc.post("/api/auth/register", json={"email": email, "password": password, "full_name": "Jana"})
    assert r.status_code == 200, r.text
    assert "password_hash" not in r.json()
    tok = tc.post("/api/auth/token", data={"username": email.lower(), "password": password})
    assert tok.status_code == 200, tok.text
    return tok.json()["access_token"]


def test_register_login_me_limits(api):
    tc, _ = api
    token = _register_and_login(tc)
    h = {"Authorization": f"Bearer {token}"}
    me = tc.get("/api/auth/me", headers=h).json()
    assert me["email"] == "Jana@Firma.sk" and me["tier"] == "free"
    assert tc.get("/api/auth/tier/limits", headers=h).json()["searches_per_day"] == 10
    # /auth/login funguje rovnako ako /auth/token
    assert tc.post("/api/auth/login", data={"username": "jana@firma.sk",
                                            "password": PW}).status_code == 200


def test_register_and_login_errors(api):
    tc, _ = api
    _register_and_login(tc)
    dup = tc.post("/api/auth/register", json={"email": "JANA@firma.SK", "password": PW_OTHER})
    assert dup.status_code == 400
    assert tc.post("/api/auth/register", json={"email": "zly-email", "password": PW}).status_code == 400
    assert tc.post("/api/auth/register", json={"email": "x@y.sk", "password": PW_SHORT}).status_code == 400
    bad = tc.post("/api/auth/token", data={"username": "jana@firma.sk", "password": PW_OTHER})
    assert bad.status_code == 401
    assert tc.post("/api/auth/token", data={"username": "nikto@x.sk", "password": PW}).status_code == 401


def test_token_in_query_string_is_not_accepted(api):
    tc, _ = api
    token = _register_and_login(tc)
    assert tc.get(f"/api/auth/me?token={token}").status_code == 401


def test_inactive_user_is_rejected(api):
    tc, conn = api
    token = _register_and_login(tc)
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET is_active = false")
    assert tc.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    assert tc.post("/api/auth/token", data={"username": "jana@firma.sk",
                                            "password": PW}).status_code == 401


def test_favorites_crud_and_isolation(api):
    tc, _ = api
    h1 = {"Authorization": f"Bearer {_register_and_login(tc)}"}
    h2 = {"Authorization": f"Bearer {_register_and_login(tc, 'iny@firma.sk')}"}
    body = {"company_identifier": "27082440", "company_name": "Alza.cz a.s.", "country": "cz",
            "company_data": {"x": 1}, "risk_score": 2, "risk_factors": []}
    fav = tc.post("/api/user/favorites", json=body, headers=h1).json()["favorite"]
    assert fav["country"] == "CZ"
    tc.post("/api/user/favorites", json=body, headers=h1)  # duplicita = upsert
    lst = tc.get("/api/user/favorites", headers=h1).json()
    assert lst["count"] == 1 and lst["favorites"][0]["company_name"] == "Alza.cz a.s."
    assert tc.get("/api/user/favorites/check/27082440/CZ", headers=h1).json()["is_favorite"] is True
    assert tc.get("/api/user/favorites/check/27082440/CZ", headers=h2).json()["is_favorite"] is False
    # iný používateľ nemôže meniť ani mazať cudziu obľúbenú
    assert tc.put(f"/api/user/favorites/{fav['id']}/notes", json={"notes": "x"}, headers=h2).status_code == 404
    assert tc.delete(f"/api/user/favorites/{fav['id']}", headers=h2).status_code == 404
    upd = tc.put(f"/api/user/favorites/{fav['id']}/notes", json={"notes": "overiť IBAN"}, headers=h1).json()
    assert upd["favorite"]["notes"] == "overiť IBAN"
    assert tc.delete(f"/api/user/favorites/{fav['id']}", headers=h1).status_code == 200
    assert tc.get("/api/user/favorites", headers=h1).json()["count"] == 0
    assert tc.get("/api/user/favorites").status_code == 401


def test_api_keys_lifecycle(api):
    tc, conn = api
    h = {"Authorization": f"Bearer {_register_and_login(tc)}"}
    assert tc.post("/api/api-keys", json={"name": "ERP"}, headers=h).status_code == 403  # free tier
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET tier = 'enterprise'")
    created = tc.post("/api/api-keys", json={"name": "ERP", "permissions": ["read", "admin"]}, headers=h).json()
    key = created["key"]
    assert key.startswith("ica_") and created["permissions"] == ["read"]
    listed = tc.get("/api/api-keys", headers=h).json()
    assert len(listed) == 1 and "key" not in listed[0] and listed[0]["is_active"] is True
    with conn.cursor() as cur:
        cur.execute("SELECT key_hash FROM api_keys")
        assert cur.fetchone()[0] != key  # uložený je len hash
    assert tc.get("/api/auth/me", headers={"X-API-Key": key}).json()["email"] == "Jana@Firma.sk"
    assert tc.get("/api/auth/me", headers={"Authorization": f"Bearer {key}"}).status_code == 200
    assert tc.delete(f"/api/api-keys/{created['id']}", headers=h).status_code == 200
    assert tc.get("/api/auth/me", headers={"X-API-Key": key}).status_code == 401
    assert tc.delete(f"/api/api-keys/{created['id']}", headers=h).status_code == 404


def test_search_history_recorded_only_for_logged_in_user(api, monkeypatch):
    tc, _ = api
    from backend.app.models.company import Company
    from backend.app.services.ares_service import ARESService
    from backend.app.services.cache_service import cache_service

    async def fake_fetch(self, ico):
        return Company(ico=ico, name="Alza.cz a.s.", address="Praha", status="AKTIVNI", raw_data={})

    monkeypatch.setattr(ARESService, "fetch_company", fake_fetch)
    cache_service.in_memory.clear()
    h = {"Authorization": f"Bearer {_register_and_login(tc)}"}
    assert tc.get("/api/v4/search/27082440", params={"country": "CZ"}).status_code == 200  # anonym
    assert tc.get("/api/v4/search/27082440", params={"country": "CZ"}, headers=h).status_code == 200
    cache_service.in_memory.clear()
    hist = tc.get("/api/search/history", headers=h).json()
    assert len(hist) == 1 and hist[0]["query"] == "27082440" and hist[0]["country"] == "CZ"
    assert hist[0]["timestamp"] == hist[0]["search_timestamp"]
    assert tc.get("/api/search/history").status_code == 401


def test_batch_export_limit_and_excel(api):
    tc, _ = api
    h = {"Authorization": f"Bearer {_register_and_login(tc)}"}
    rows = [{"company_name": f"Firma {i}", "company_identifier": str(i), "country": "SK"} for i in range(6)]
    assert tc.post("/api/export/batch-excel", json=rows, headers=h).status_code == 403  # free: 5
    ok = tc.post("/api/export/batch-excel", json=rows[:5], headers=h)
    assert ok.status_code == 200 and ok.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    assert tc.post("/api/export/excel", json={"nodes": [], "edges": []}).status_code == 200
