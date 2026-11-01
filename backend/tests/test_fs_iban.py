import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.core import circuit_breaker
from backend.app.services import fs_iban_service as fs
from backend.app.services.fs_iban_service import (
    ATTRIBUTION,
    FsIbanNotConfiguredError,
    FsIbanService,
    FsIbanUnavailableError,
    iban_checksum_ok,
    normalize_iban,
)

EXAMPLE_IBAN = "SK3112000000198742637541"  # vzorový IBAN z normy, nie reálny účet
OTHER_IBAN = "SK0809000000000123123123"


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    monkeypatch.setattr(fs, "RETRY_DELAY", 0)
    monkeypatch.delenv("FS_IBAN_STUB_MODE", raising=False)
    monkeypatch.delenv("FS_OPENDATA_API_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_DSN", raising=False)
    circuit_breaker._breakers.clear()
    yield
    circuit_breaker._breakers.clear()


def test_iban_checksum():
    assert iban_checksum_ok(EXAMPLE_IBAN)
    assert iban_checksum_ok("sk31 1200 0000 1987 4263 7541")
    assert not iban_checksum_ok("SK3112000000198742637542")  # zlá kontrolná číslica
    assert not iban_checksum_ok("SK31120000001987426375")    # krátky
    assert not iban_checksum_ok("")
    assert normalize_iban(" sk31 1200 ") == "SK311200"


def make_fs_handler(rows=None, fail_first=0, seen=None, searchable=("ico", "ic_dph"), pages=1):
    rows = rows if rows is not None else {
        "12345678": [
            {"ic_dph": "SK2020000000", "ico": "12345678", "iban": EXAMPLE_IBAN},
            {"ic_dph": "SK2020000000", "ico": "12345678", "iban": OTHER_IBAN},
            {"ic_dph": "SK2020000000", "ico": "12345678", "iban": EXAMPLE_IBAN},  # duplicita
            {"ic_dph": "SK2099999999", "ico": "123456789", "iban": "SK0000"},      # podreťazcová zhoda
        ]
    }
    state = {"fails": fail_first}

    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        if state["fails"] > 0:
            state["fails"] -= 1
            return httpx.Response(503, json={"message": "updating"})
        if request.headers.get("key") != "test-key":
            return httpx.Response(401, json={"message": "Header 'key' with ApiKey is not provided"})
        path = request.url.path
        if path.endswith("/lists/ds_dph_iban"):
            return httpx.Response(200, json={"name": "IBAN", "slug": "ds_dph_iban",
                                              "update_date": "2026-11-01", "searchable": list(searchable)})
        if path.endswith("/data/ds_dph_iban/search"):
            q = request.url.params
            found = rows.get(q["search"])
            if not found:
                return httpx.Response(404, json={"message": "Search not found"})
            return httpx.Response(200, json={"page": int(q["page"]), "pages": pages, "itemsCount": len(found),
                                              "itemsPerPage": 50, "data": found})
        return httpx.Response(404)

    return handler


async def _lookup(handler, ico="12345678", key="test-key"):
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        return await FsIbanService(c, api_key=key).lookup(ico)


async def test_lookup_dedupes_and_filters_exact_ico():
    seen = []
    r = await _lookup(make_fs_handler(seen=seen))
    assert r["registered"] is True
    assert r["ibans"] == [EXAMPLE_IBAN, OTHER_IBAN]
    assert r["vat_ids"] == ["SK2020000000"]
    assert r["list_updated"] == "2026-11-01"
    assert r["attribution"] == ATTRIBUTION
    search = [s for s in seen if s.url.path.endswith("/search")][0]
    assert search.url.params["column"] == "ico" and search.url.params["search"] == "12345678"


async def test_lookup_not_in_list():
    r = await _lookup(make_fs_handler(), ico="87654321")
    assert r["registered"] is False and r["ibans"] == []


async def test_uppercase_columns_are_supported():
    rows = {"12345678": [{"IC_DPH": "SK2020000000", "ICO": "12345678", "IBAN": EXAMPLE_IBAN}]}
    r = await _lookup(make_fs_handler(rows=rows, searchable=("IC_DPH", "ICO")))
    assert r["ibans"] == [EXAMPLE_IBAN]


async def test_missing_search_column_is_an_error():
    with pytest.raises(FsIbanUnavailableError):
        await _lookup(make_fs_handler(searchable=("ic_dph",)))


async def test_missing_or_rejected_key():
    with pytest.raises(FsIbanNotConfiguredError):
        await _lookup(make_fs_handler(), key="")
    with pytest.raises(FsIbanNotConfiguredError):
        await _lookup(make_fs_handler(), key="wrong")


async def test_retry_on_503_list_update():
    r = await _lookup(make_fs_handler(fail_first=2))
    assert r["registered"] is True


async def test_persistent_503_raises():
    with pytest.raises(FsIbanUnavailableError):
        await _lookup(make_fs_handler(fail_first=10_000))


async def test_stub_mode(monkeypatch):
    monkeypatch.setenv("FS_IBAN_STUB_MODE", "1")
    r = await _lookup(make_fs_handler(fail_first=10_000), ico="52374220", key="")
    assert r["registered"] is True and r["source"] == "FS_STUB"


# ---------- endpoint ----------

@pytest.fixture()
def api(monkeypatch):
    from backend.app.api.endpoints import search_sk
    from backend.app.main import app

    holder = {"handler": make_fs_handler()}

    async def client_override():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: holder["handler"](r))) as c:
            yield c

    app.dependency_overrides[search_sk.get_httpx_client] = client_override
    with TestClient(app) as tc:
        yield tc, holder
    app.dependency_overrides.clear()


def test_endpoint_match_and_mismatch(api, monkeypatch):
    monkeypatch.setenv("FS_OPENDATA_API_KEY", "test-key")
    tc, _ = api
    ok = tc.get("/api/sk/company/12345678/iban", params={"iban": "SK31 1200 0000 1987 4263 7541"}).json()
    assert ok["iban_match"] is True and ok["registered"] is True and ok["atlas_id"] is None
    no = tc.get("/api/sk/company/87654321/iban", params={"iban": EXAMPLE_IBAN}).json()
    assert no["iban_match"] is False and no["registered"] is False
    plain = tc.get("/api/sk/company/12345678/iban").json()
    assert plain["iban_match"] is None and plain["checked_iban"] is None


def test_endpoint_errors(api, monkeypatch):
    tc, holder = api
    assert tc.get("/api/sk/company/1234/iban").status_code == 400
    assert tc.get("/api/sk/company/12345678/iban", params={"iban": "SK3112000000198742637542"}).status_code == 400
    assert tc.get("/api/sk/company/12345678/iban").status_code == 503  # bez kľúča
    monkeypatch.setenv("FS_OPENDATA_API_KEY", "test-key")
    holder["handler"] = make_fs_handler(fail_first=10_000)
    assert tc.get("/api/sk/company/12345678/iban").status_code == 503
