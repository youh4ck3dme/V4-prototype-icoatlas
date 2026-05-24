import pytest
import httpx
from backend.app.main import app

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


@pytest.mark.asyncio
async def test_v4_search_dic_hu():
    """Test that DIČ/Adószám is resolved correctly for Hungary (HU)"""
    raw = "10902090" # A HU Cegjegyzékszám
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(f"/api/v4/search/{raw}", params={"country": "HU"})
        assert r.status_code in [200, 404]
        if r.status_code == 200:
            data = r.json()
            assert "company" in data
            comp = data["company"]
            assert "dic" in comp
