"""
Search endpoint tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_search_valid_ico(client: AsyncClient):
    """Test search with valid ICO."""
    response = await client.get("/api/search", params={"q": "12345678"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_search_empty_query(client: AsyncClient):
    """Test search with empty query."""
    response = await client.get("/api/search", params={"q": ""})
    # Should return empty list or validation error
    assert response.status_code in [200, 400, 422]


@pytest.mark.asyncio
async def test_search_with_limit(client: AsyncClient):
    """Test search with limit parameter."""
    response = await client.get("/api/search", params={"q": "test", "limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


@pytest.mark.asyncio
async def test_search_company_sk(client: AsyncClient):
    """Test Slovak company search endpoint."""
    response = await client.get("/api/sk/company/12345678")
    # May return 200 with data or 404 if not found
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_search_company_cz(client: AsyncClient):
    """Test Czech company search endpoint."""
    response = await client.get("/api/company/12345678")
    assert response.status_code in [200, 404]
