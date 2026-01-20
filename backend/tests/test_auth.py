"""
Authentication endpoint tests.
Note: These are placeholder tests. Update when auth endpoints are implemented.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_endpoints_not_yet_implemented(client: AsyncClient):
    """Test that auth endpoints return expected status when not implemented."""
    # These endpoints don't exist yet, so we expect 404
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "test123"
    })
    # Should return 404 since auth is not implemented yet
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_protected_route_without_auth(client: AsyncClient):
    """Test accessing protected routes without authentication."""
    response = await client.get("/api/auth/me")
    # Should return 404 or 401
    assert response.status_code in [401, 404]
