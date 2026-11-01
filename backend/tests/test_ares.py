import copy
import json
from pathlib import Path

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.core import circuit_breaker
from backend.app.services import ares_service
from backend.app.services.ares_service import (
    STATUS_ACTIVE,
    STATUS_DISSOLVED,
    ARESService,
    AresService,
    ares_status,
    normalize_ares,
    normalize_cz_ico,
)

ALZA = json.loads((Path(__file__).parent / "fixtures" / "ares" / "ares_27082440.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    monkeypatch.setattr(ares_service, "RETRY_DELAY", 0)
    circuit_breaker._breakers.clear()
    yield
    circuit_breaker._breakers.clear()


def test_normalize_real_response():
    n = normalize_ares(ALZA)
    assert n["legal_name"] == "Alza.cz a.s."
    assert n["status"] == STATUS_ACTIVE
    assert n["legal_form"] == "121"
    assert n["street"] == "Jankovcova 1522/53"
    assert n["city"] == "Praha"
    assert n["postal_code"] == "17000"
    assert n["region"] == "Hlavní město Praha"
    assert n["dic"] == "CZ27082440"
    assert n["founded"] == "2003-08-26"
    assert "47250" in n["nace_codes"]


def test_status_mapping():
    assert ares_status({**ALZA, "datumZaniku": "2020-01-01"}) == STATUS_DISSOLVED
    assert ares_status({"seznamRegistraci": {"stavZdrojeVr": "ZANIKLY"}}) == STATUS_DISSOLVED
    assert ares_status({}) == "NEZNÁMY"


def test_normalize_cz_ico():
    assert normalize_cz_ico("27082440") == "27082440"
    assert normalize_cz_ico("25596641") == "25596641"
    assert normalize_cz_ico("123") == "00000123"
    assert normalize_cz_ico("270 824 40") == "27082440"
    assert normalize_cz_ico("123456789") is None
    assert normalize_cz_ico("") is None


def test_alias_used_by_identity_graph_and_id_router():
    assert AresService is ARESService


def handler_factory(fail_first=0, calls=None):
    state = {"fails": fail_first}

    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(str(request.url))
        if state["fails"] > 0:
            state["fails"] -= 1
            return httpx.Response(503)
        ico = request.url.path.rsplit("/", 1)[-1]
        if ico == "27082440":
            return httpx.Response(200, json=copy.deepcopy(ALZA))
        return httpx.Response(404, json={"kod": "NENALEZENO"})

    return handler


async def _fetch(handler, ico):
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        return await ARESService(c).fetch_company(ico)


async def test_fetch_company_maps_common_model():
    c = await _fetch(handler_factory(), "27082440")
    assert c.ico == "27082440" and c.name == "Alza.cz a.s." and c.status == STATUS_ACTIVE
    assert c.address == "Jankovcova 1522/53, Holešovice, 17000 Praha 7"
    assert c.raw_data["dic"] == "CZ27082440"           # search_v4 číta dic z raw_data
    assert c.raw_data["normalized"]["city"] == "Praha"


async def test_not_found_and_invalid():
    with pytest.raises(HTTPException) as e:
        await _fetch(handler_factory(), "12345678")
    assert e.value.status_code == 404
    with pytest.raises(HTTPException) as e:
        await _fetch(handler_factory(), "123456789")
    assert e.value.status_code == 400


async def test_retry_and_breaker():
    calls = []
    assert (await _fetch(handler_factory(fail_first=2, calls=calls), "27082440")).name == "Alza.cz a.s."
    assert len(calls) == 3

    always_down = handler_factory(fail_first=10_000, calls=calls)
    for _ in range(5):
        with pytest.raises(HTTPException) as e:
            await _fetch(always_down, "27082440")
        assert e.value.status_code == 502
    with pytest.raises(HTTPException) as e:
        await _fetch(always_down, "27082440")
    assert e.value.status_code == 503  # circuit breaker otvorený


def test_cz_endpoint_and_v4_search(monkeypatch):
    from backend.app.api.endpoints import search
    from backend.app.main import app

    async def client_override():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler_factory())) as c:
            yield c

    app.dependency_overrides[search.get_httpx_client] = client_override

    # /v4/search si vytvára vlastného klienta; vrátime rovnaký výsledok cez ARESService
    async def fake_fetch(self, ico):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler_factory())) as c:
            return await ARESService.__dict__["_orig_fetch"](ARESService(c), ico)

    monkeypatch.setattr(ARESService, "_orig_fetch", ARESService.fetch_company, raising=False)
    monkeypatch.setattr(ARESService, "fetch_company", fake_fetch)
    try:
        with TestClient(app) as tc:
            r = tc.get("/api/company/27082440")
            assert r.status_code == 200 and r.json()["name"] == "Alza.cz a.s."
            v4 = tc.get("/api/v4/search/27082440", params={"country": "CZ"})
            assert v4.status_code == 200
            comp = v4.json()["company"]
            assert comp["city"] == "Praha" and comp["postal_code"] == "17000"
            assert comp["legal_form"] == "121" and comp["dic"] == "CZ27082440"
    finally:
        app.dependency_overrides.clear()


async def test_client_errors_do_not_trip_breaker():
    calls = []

    def bad_request(request):
        calls.append(request)
        return httpx.Response(400, json={"kod": "CHYBA_VSTUPU"})

    for _ in range(7):
        with pytest.raises(HTTPException) as e:
            await _fetch(bad_request, "12345678")
        assert e.value.status_code == 400
    assert len(calls) == 7  # bez opakovania a breaker ostal zatvorený
    assert circuit_breaker.get_circuit_breaker("ares").state.value == "closed"
    assert (await _fetch(handler_factory(), "27082440")).name == "Alza.cz a.s."


def test_v4_search_pads_short_cz_ico(monkeypatch):
    from backend.app.main import app
    from backend.app.services.cache_service import cache_service

    seen = []

    async def fake_fetch(self, ico):
        seen.append(ico)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler_factory())) as c:
            data = copy.deepcopy(ALZA)
            data["ico"] = "00006947"
            from backend.app.models.company import Company
            n = normalize_ares(data)
            return Company(ico="00006947", name=n["legal_name"], address=n["address"], status=n["status"],
                           raw_data={**data, "normalized": n})

    monkeypatch.setattr(ARESService, "fetch_company", fake_fetch)
    cache_service.in_memory.clear()
    with TestClient(app) as tc:
        r = tc.get("/api/v4/search/6947", params={"country": "CZ"})
    cache_service.in_memory.clear()
    assert r.status_code == 200, r.text
    assert seen == ["00006947"]
