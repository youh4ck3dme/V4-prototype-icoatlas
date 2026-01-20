"""
Authentication endpoint tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, sample_user_data):
    """Test user registration."""
    response = await client.post("/api/auth/register", json=sample_user_data)
    assert response.status_code in [200, 201]
    data = response.json()
    assert "email" in data or "user_id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, sample_user_data):
    """Test duplicate email registration fails."""
    # Register first user
    await client.post("/api/auth/register", json=sample_user_data)
    
    # Try to register with same email
    response = await client.post("/api/auth/register", json=sample_user_data)
    assert response.status_code in [400, 409, 422]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, sample_user_data):
    """Test successful login."""
    # Register user first
    await client.post("/api/auth/register", json=sample_user_data)
    
    # Login
    login_data = {
        "email": sample_user_data["email"],
        "password": sample_user_data["password"],
    }
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials."""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword",
    }
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code in [401, 404]


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, sample_user_data):
    """Test getting current user info."""
    # Register and login
    await client.post("/api/auth/register", json=sample_user_data)
    login_response = await client.post("/api/auth/login", json={
        "email": sample_user_data["email"],
        "password": sample_user_data["password"],
    })
    token = login_response.json().get("access_token")
    
    # Get current user
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == sample_user_data["email"]
