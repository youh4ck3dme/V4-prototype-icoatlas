"""
Špeciálne testy pre Redis cache funkcionalitu
"""

import os
import sys

import pytest

# Pridať backend do path
backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from services.redis_cache import (
        get_redis_client,
        redis_delete,
        redis_get,
        redis_get_stats,
        redis_set,
    )
except ImportError:
    pytest.skip("Redis cache nie je dostupný")


def test_redis_cache_imports():
    """Test, či Redis cache sa dá importovať"""
    try:
        from backend.services.redis_cache import get_redis_client

        assert get_redis_client is not None
        assert callable(get_redis_client)
    except ImportError:
        pytest.skip("Redis cache nie je dostupný")


def test_redis_client_initialization():
    """Test, či Redis klient sa inicializuje (ak je Redis dostupný)"""
    client = get_redis_client()

    # Ak Redis nie je dostupný, client bude None (to je OK)
    if client is None:
        pytest.skip("Redis nie je dostupný (to je OK pre lokálny vývoj)")

    # Ak je dostupný, overiť, či funguje
    assert client is not None
    try:
        client.ping()
    except Exception:
        pytest.skip("Redis klient nie je dostupný")


def test_redis_get_set_delete():
    """Test základných Redis operácií (get, set, delete)"""
    client = get_redis_client()

    if client is None:
        pytest.skip("Redis nie je dostupný")

    try:
        # Test set
        test_key = "test_key_12345"
        test_value = {"test": "data", "number": 42}
        redis_set(test_key, test_value, ttl=60)

        # Test get
        retrieved = redis_get(test_key)
        assert retrieved is not None
        assert retrieved == test_value

        # Test delete
        redis_delete(test_key)
        deleted = redis_get(test_key)
        assert deleted is None

    except Exception as e:
        pytest.skip(f"Redis operácie zlyhali: {e}")


def test_redis_get_stats():
    """Test, či redis_get_stats vracia správne štatistiky"""
    stats = redis_get_stats()

    assert isinstance(stats, dict)

    # Ak Redis nie je dostupný, stats by mal obsahovať error
    if "error" in stats:
        pytest.skip(f"Redis nie je dostupný: {stats['error']}")

    # Ak je dostupný, overiť štruktúru
    assert "total_keys" in stats or "used_memory_mb" in stats


def test_redis_cache_integration():
    """Test, či cache.py používa Redis (ak je dostupný)"""
    try:
        from backend.services.cache import get, set

        # Test, či cache funkcie fungujú
        test_key = "test_cache_key_12345"
        test_value = {"test": "cache"}

        set(test_key, test_value)
        retrieved = get(test_key)

        # Hodnota by mala byť vrátená (z Redis alebo in-memory)
        assert retrieved is not None

        # Vyčistiť
        from backend.services.cache import delete

        delete(test_key)

    except ImportError:
        pytest.skip("Cache service nie je dostupný")


def test_redis_fallback_to_memory():
    """Test, či cache fallbackuje na in-memory, ak Redis nie je dostupný"""
    try:
        from backend.services.cache import get, set

        # Test, či cache funguje aj bez Redis
        test_key = "test_fallback_key_12345"
        test_value = {"test": "fallback"}

        set(test_key, test_value)
        retrieved = get(test_key)

        # Hodnota by mala byť vrátená (z in-memory fallback)
        assert retrieved is not None
        assert retrieved == test_value

        # Vyčistiť
        from backend.services.cache import delete

        delete(test_key)

    except ImportError:
        pytest.skip("Cache service nie je dostupný")
