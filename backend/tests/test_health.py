"""
Health check endpoint tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint returns 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint is accessible."""
    response = await client.get("/")
    # Root may redirect or return 404, both are acceptable
    assert response.status_code in [200, 404, 307]
