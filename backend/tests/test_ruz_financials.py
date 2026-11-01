import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.core import circuit_breaker
from backend.app.services import ruz_financials_service as ruz
from backend.app.services.cache_service import cache_service
from backend.app.services.ruz_financials_service import (
    RuzFinancialsService,
    RuzUnavailableError,
    normalize_number,
    parse_statement,
)

FIXTURES = Path(__file__).parent / "fixtures" / "ruz"
V687 = json.loads((FIXTURES / "vykaz_687_sample.json").read_text(encoding="utf-8"))
V699 = json.loads((FIXTURES / "vykaz_699_sample.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    monkeypatch.setattr(ruz, "RETRY_DELAY", 0)
    monkeypatch.delenv("RUZ_STUB_MODE", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_DSN", raising=False)
    circuit_breaker._breakers.clear()
    cache_service.in_memory.clear()
    yield
    circuit_breaker._breakers.clear()
    cache_service.in_memory.clear()


# ---------- parsing ----------

def test_normalize_number():
    assert normalize_number("1 234,50") == 1234.5
    assert normalize_number("-823") == -823.0
    assert normalize_number("") is None
    assert normalize_number(None) is None
    assert normalize_number("abc") is None


def test_parse_699_real_statement():
    m = parse_statement(699, V699["obsah"]["tabulky"])
    assert m["assets"] == 36539.0
    assert m["equity"] == 11715.0
    assert m["liabilities"] == 24824.0
    assert m["net_turnover"] == 47094.0
    assert m["revenue"] == 47094.0
    assert m["profit"] == 823.0
    # súvaha musí sedieť: aktíva = vlastné imanie + záväzky (+ časové rozlíšenie, tu 0)
    assert m["assets"] == m["equity"] + m["liabilities"]


def test_parse_687_real_statement():
    m = parse_statement(687, V687["obsah"]["tabulky"])
    assert m["assets"] == 5000.0
    assert m["equity"] == 5000.0
    assert m["liabilities"] is None
    assert m["revenue"] is None
    assert m["profit"] is None


def test_parse_rejects_unknown_template_and_wrong_shape():
    assert parse_statement(742, V699["obsah"]["tabulky"]) is None
    assert parse_statement(687, V699["obsah"]["tabulky"]) is None  # iný počet buniek
    assert parse_statement(699, []) is None


# ---------- service flow ----------

def _statement(sid, year, typ, upd, reports):
    return {"id": sid, "obdobieOd": f"{year}-01", "obdobieDo": f"{year}-12", "typ": typ,
            "datumPoslednejUpravy": upd, "idUctovnychVykazov": reports}


def make_ruz_handler(fail_first=0, calls=None):
    statements = {
        1: _statement(1, 2024, "Riadna", "2025-05-01", [11]),
        2: _statement(2, 2024, "Mimoriadna", "2025-08-01", [12]),
        3: _statement(3, 2023, "Riadna", "2024-05-01", [99, 13]),
        4: _statement(4, 2025, "Priebežná", "2025-07-01", [14]),
        5: _statement(5, 2022, "Riadna", "2023-05-01", [15]),
    }
    reports = {11: {**V699, "id": 11}, 12: {**V687, "id": 12}, 13: {**V687, "id": 13},
               14: {**V699, "id": 14}, 15: {"id": 15, "idSablony": 742, "obsah": {"tabulky": []}},
               99: {"id": 99, "idSablony": 742, "obsah": {"tabulky": []}}}
    state = {"fails": fail_first}

    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(str(request.url))
        if state["fails"] > 0:
            state["fails"] -= 1
            return httpx.Response(503)
        path = request.url.path.rsplit("/", 1)[-1]
        q = request.url.params
        if path == "uctovne-jednotky":
            return httpx.Response(200, json={"id": [100] if q["ico"] == "12345678" else []})
        if path == "uctovna-jednotka":
            return httpx.Response(200, json={"ico": "12345678", "idUctovnychZavierok": [1, 2, 3, 4, 5]})
        if path == "uctovna-zavierka":
            return httpx.Response(200, json=statements[int(q["id"])])
        if path == "uctovny-vykaz":
            return httpx.Response(200, json=reports[int(q["id"])])
        return httpx.Response(404)

    return handler


async def _fetch(handler, ico="12345678", years=5):
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        return await RuzFinancialsService(c, max_years=years).fetch_financials(ico)


async def test_fetch_builds_latest_and_history():
    r = await _fetch(make_ruz_handler())
    years = [h["year"] for h in r["history"]]
    assert years == [2024, 2023, 2022]                      # priebežná 2025 vynechaná
    assert r["year"] == 2024 and r["template"] == "699"     # riadna pred mimoriadnou
    assert r["assets"] == 36539.0 and r["profit"] == 823.0
    assert r["history"][1]["template"] == "687"             # 2023: prvý výkaz IFRS, druhý 687
    assert r["history"][1]["available"] is True
    assert r["history"][2]["available"] is False            # 2022: len IFRS
    assert r["history"][2]["template"] == "742"
    assert r["source"] == "RUZ"


async def test_max_years_limits_history():
    r = await _fetch(make_ruz_handler(), years=1)
    assert [h["year"] for h in r["history"]] == [2024]


async def test_unknown_ico_returns_none():
    assert await _fetch(make_ruz_handler(), ico="87654321") is None


async def test_invalid_ico_raises():
    with pytest.raises(ValueError):
        await _fetch(make_ruz_handler(), ico="123")


async def test_retry_recovers_from_transient_5xx():
    calls = []
    r = await _fetch(make_ruz_handler(fail_first=2, calls=calls))
    assert r["year"] == 2024
    assert len([c for c in calls if "uctovne-jednotky" in c]) == 3


async def test_persistent_failure_raises_and_opens_breaker():
    calls = []
    handler = make_ruz_handler(fail_first=10_000, calls=calls)
    for _ in range(5):
        with pytest.raises(RuzUnavailableError):
            await _fetch(handler)
    n = len(calls)
    with pytest.raises(RuzUnavailableError):
        await _fetch(handler)
    assert len(calls) == n  # breaker open: RÚZ sa už nevolá


async def test_stub_mode(monkeypatch):
    monkeypatch.setenv("RUZ_STUB_MODE", "1")
    r = await _fetch(make_ruz_handler(fail_first=10_000), ico="52374220")
    assert r["source"] == "RUZ_STUB" and r["year"] == 2023 and len(r["history"]) == 2
    assert await _fetch(make_ruz_handler(), ico="12345678") is None


# ---------- endpoint ----------

@pytest.fixture()
def api():
    from backend.app.main import app
    from backend.app.api.endpoints import search_sk

    holder = {"handler": make_ruz_handler()}

    async def client_override():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: holder["handler"](r))) as c:
            yield c

    app.dependency_overrides[search_sk.get_httpx_client] = client_override
    with TestClient(app) as tc:
        yield tc, holder
    app.dependency_overrides.clear()


def test_endpoint_ok_and_cached(api):
    tc, _ = api
    r = tc.get("/api/sk/company/12345678/financials")
    assert r.status_code == 200
    body = r.json()
    assert body["financials"]["year"] == 2024 and body["cached"] is False and body["atlas_id"] is None
    assert tc.get("/api/sk/company/12345678/financials").json()["cached"] is True


def test_endpoint_errors(api):
    tc, holder = api
    assert tc.get("/api/sk/company/12AB/financials").status_code == 400
    assert tc.get("/api/sk/company/87654321/financials").status_code == 404
    holder["handler"] = make_ruz_handler(fail_first=10_000)
    assert tc.get("/api/sk/company/11112222/financials").status_code == 503
