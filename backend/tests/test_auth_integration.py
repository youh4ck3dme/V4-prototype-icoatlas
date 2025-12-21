import pytest
from fastapi.testclient import TestClient
from main import app
from services.database import get_db_session
from services.auth import User

client = TestClient(app)

def test_auth_flow(db_session):
    """Test registration, login and me endpoint"""
    
    email = "test_auth@example.com"
    password = "password123"
    
    # 1. Cleanup
    db_session.query(User).filter(User.email == email).delete()
    db_session.commit()
    
    # 2. Register
    response = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Test User"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["tier"] == "free"
    
    # 3. Login
    response = client.post("/api/auth/token", data={
        "username": email,
        "password": password
    })
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    
    # 4. Me
    response = client.get("/api/auth/me", params={"token": token})
    assert response.status_code == 200
    me_data = response.json()
    assert me_data["email"] == email

    # 5. API Keys (Should fail for FREE tier)
    response = client.post("/api/api-keys", json={"name": "MyKey"}, params={"token": token})
    assert response.status_code == 403
    
    # Cleanup
    db_session.query(User).filter(User.email == email).delete()
    db_session.commit()
