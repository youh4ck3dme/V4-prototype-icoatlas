import pytest
import re
import httpx
from backend.app.main import app
from backend.app.models.company import Company
from backend.app.services.nav_playwright_service import NAVPlaywrightService

@pytest.mark.asyncio
async def test_v4_search_dic_sk():
    """Test that DIČ is resolved correctly for Slovakia (SK) mock company"""
    raw = "88888888"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(f"/api/v4/search/{raw}", params={"country": "SK"})
        assert r.status_code == 200
        data = r.json()
        
    assert "company" in data
    comp = data["company"]
    # Verify tin is mapped to dic
    assert comp.get("dic") == 2020202020 or comp.get("dic") == "2020202020"
    # Regional Contract assertion: SK DIČ is strictly a 10-digit number
    assert re.match(r"^\d{10}$", str(comp["dic"]))


@pytest.mark.asyncio
async def test_v4_search_dic_cz():
    """Test that DIČ is resolved correctly for Czech Republic (CZ) company"""
    raw = "27082440" # Alza.cz a.s.
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(f"/api/v4/search/{raw}", params={"country": "CZ"})
        assert r.status_code == 200
        data = r.json()
        
    assert "company" in data
    comp = data["company"]
    # Verify dic is CZ27082440
    assert comp.get("dic") == "CZ27082440"
    # Regional Contract assertion: CZ DIČ matches optional CZ prefix + 8-10 digits
    assert re.match(r"^(CZ)?\d{8,10}$", comp["dic"])


@pytest.mark.asyncio
async def test_v4_search_dic_pl():
    """Test that DIČ/NIP is resolved correctly for Poland (PL)"""
    raw = "5260250995" # A real Polish NIP for test
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(f"/api/v4/search/{raw}", params={"country": "PL"})
        assert r.status_code in [200, 404] # Scraper may timeout/fail in testing environment, which is acceptable
        if r.status_code == 200:
            data = r.json()
            assert "company" in data
            comp = data["company"]
            assert comp.get("dic") == "5260250995"
            # Regional Contract assertion: PL NIP/DIČ is strictly 10 digits
            assert re.match(r"^\d{10}$", comp["dic"])


@pytest.mark.asyncio
async def test_v4_search_dic_hu():
    """Test that DIČ/Adószám is resolved correctly for Hungary (HU)"""
    raw = "01-09-562739" # Real Hungarian Cégjegyzékszám
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(f"/api/v4/search/{raw}", params={"country": "HU"})
        assert r.status_code in [200, 404]
        if r.status_code == 200:
            data = r.json()
            assert "company" in data
            comp = data["company"]
            assert comp.get("dic")
            assert comp["dic"] != "N/A"
            # Regional Contract assertion: HU Adószám format is XXXXXXXX-Y-ZZ
            assert re.fullmatch(r"\d{8}-\d-\d{2}", comp["dic"])


@pytest.mark.asyncio
async def test_v4_search_dic_hu_maps_adoszam_from_scraper(monkeypatch):
    """Mocked unit test for Hungary (HU) mapping logic without real API calls"""
    captured_lookup_value = None

    async def fake_fetch_company(self, lookup_value: str):
        nonlocal captured_lookup_value
        captured_lookup_value = lookup_value
        return Company(
            ico=lookup_value,
            name="Teszt Kft.",
            address="Budapest",
            status="AKTÍV",
            raw_data={
                "source": "companyregister.hu",
                "provider_ok": True,
                "adoszam": "14906428-2-06",
            },
        )

    monkeypatch.setattr(
        NAVPlaywrightService,
        "fetch_company",
        fake_fetch_company,
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        # 1. Search with Cégjegyzékszám
        r = await ac.get(
            "/api/v4/search/01-09-562739",
            params={"country": "HU"},
        )
        assert r.status_code == 200
        comp = r.json()["company"]
        assert comp["country"] == "HU"
        assert comp["dic"] == "14906428-2-06"
        assert re.fullmatch(r"\d{8}-\d-\d{2}", comp["dic"])
        assert captured_lookup_value == "01-09-562739"

        # 2. Search with 11-digit unformatted Adószám
        r2 = await ac.get(
            "/api/v4/search/14906428206",
            params={"country": "HU"},
        )
        assert r2.status_code == 200
        comp2 = r2.json()["company"]
        assert comp2["country"] == "HU"
        assert comp2["dic"] == "14906428-2-06"
        assert re.fullmatch(r"\d{8}-\d-\d{2}", comp2["dic"])
        assert captured_lookup_value == "14906428-2-06"


@pytest.mark.asyncio
async def test_v4_search_cache_hit(monkeypatch):
    """Test that subsequent searches hit the cache and bypass provider lookups"""
    from backend.app.services.cache_service import cache_service
    from backend.app.services.ruz_service import RuzService

    # Clear cache before starting
    cache_service.in_memory.clear()

    call_count = 0
    original_fetch = RuzService.fetch_company

    async def mocked_fetch_company(self, digits: str):
        nonlocal call_count
        call_count += 1
        return await original_fetch(self, digits)

    monkeypatch.setattr(RuzService, "fetch_company", mocked_fetch_company)

    raw = "88888888"  # Slovakia mock
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        # First call: cache miss, calls provider
        r1 = await ac.get(f"/api/v4/search/{raw}", params={"country": "SK"})
        assert r1.status_code == 200
        assert call_count == 1

        # Second call: cache hit, bypasses provider
        r2 = await ac.get(f"/api/v4/search/{raw}", params={"country": "SK"})
        assert r2.status_code == 200
        assert call_count == 1  # Verify no extra call was made
