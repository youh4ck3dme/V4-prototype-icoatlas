import pytest
import httpx
from backend.app.main import app
from backend.app.services.stripe_service import StripeService, TIER_PRICING


@pytest.mark.asyncio
async def test_stripe_pricing_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/api/payment/pricing")
        assert r.status_code == 200
        data = r.json()
        assert data["currency"] == "EUR"
        assert len(data["plans"]) >= 3
        tiers = [p["tier"] for p in data["plans"]]
        assert "starter" in tiers
        assert "pro" in tiers
        assert "enterprise" in tiers


@pytest.mark.asyncio
async def test_stripe_config_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/api/payment/config")
        assert r.status_code == 200
        data = r.json()
        assert "publishable_key" in data
        assert data["publishable_key"].startswith("pk_")


@pytest.mark.asyncio
async def test_stripe_checkout_creation_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/payment/checkout", params={"tier": "pro"})
        assert r.status_code == 200
        data = r.json()
        assert "session_id" in data
        assert data["session_id"].startswith("cs_")
        assert "checkout_url" in data
        assert "https://checkout.stripe.com" in data["checkout_url"]
        assert data["tier"] == "pro"
        assert data["amount"] == 19.99
        assert data["currency"] == "EUR"


@pytest.mark.asyncio
async def test_stripe_verify_session_endpoint():
    # First create a session
    session_data = StripeService.create_checkout_session(tier="pro")
    session_id = session_data["session_id"]

    # Verify session via endpoint
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(f"/api/payment/verify-session/{session_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == session_id
        assert data["tier"] == "pro"
        assert data["currency"] == "EUR"


@pytest.mark.asyncio
async def test_stripe_webhook_endpoint():
    mock_payload = b'{"id": "evt_test_123", "type": "checkout.session.completed", "data": {"object": {"customer": "cus_123", "subscription": "sub_123", "metadata": {"tier": "enterprise", "user_id": "usr_999"}}}}'
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/payment/webhook", content=mock_payload, headers={"Content-Type": "application/json"})
        assert r.status_code == 200
        data = r.json()
        assert data["received"] is True
        assert data["event"] == "checkout.session.completed"
