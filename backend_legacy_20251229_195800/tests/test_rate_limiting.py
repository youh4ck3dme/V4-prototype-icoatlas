import pytest
from unittest.mock import MagicMock, patch
from backend.services.rate_limiter import is_allowed, _buckets, TIER_CONFIGS

@pytest.fixture(autouse=True)
def clear_buckets():
    _buckets.clear()
    yield
    _buckets.clear()

def test_rate_limit_free_tier():
    client_id = "127.0.0.1"
    # Free tier capacity is 10
    
    # First request should be allowed
    allowed, info = is_allowed(client_id, tier="free")
    assert allowed == True
    assert info['remaining'] == 9
    
    # Consume all tokens
    _buckets[client_id]['tokens'] = 0
    
    allowed, info = is_allowed(client_id, tier="free")
    assert allowed == False

def test_rate_limit_pro_tier():
    client_id = "127.0.0.1"
    # Pro tier capacity is 50
    
    allowed, info = is_allowed(client_id, tier="pro")
    assert allowed == True
    assert _buckets[client_id]['capacity'] == 50

def test_rate_limit_enterprise_tier():
    client_id = "127.0.0.1"
    # Enterprise tier capacity is 200
    
    allowed, info = is_allowed(client_id, tier="enterprise")
    assert allowed == True
    assert _buckets[client_id]['capacity'] == 200
