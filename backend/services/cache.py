"""
Hybrid Cache Service pre API odpovede.
Kombinuje Redis (ak je dostupný) a in-memory fallback.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# Import Redis cache (ak je dostupný)
try:
    from services.redis_cache import (
        get_redis_client,
    )
    from services.redis_cache import (
        redis_delete as _redis_delete,
    )
    from services.redis_cache import (
        redis_get as _redis_get,
    )
    from services.redis_cache import (
        redis_set as _redis_set,
    )

    REDIS_ENABLED = get_redis_client() is not None
except (ImportError, Exception):
    REDIS_ENABLED = False
    _redis_get = None
    _redis_set = None
    _redis_delete = None

# In-memory cache (fallback)
_cache: Dict[str, tuple[Any, datetime]] = {}
_default_ttl = timedelta(hours=24)  # 24 hodín pre firmy


def get_cache_key(query: str, source: str = "default") -> str:
    """
    Generuje cache key z query a source.
    """
    key_string = f"{source}:{query}"
    return hashlib.md5(key_string.encode()).hexdigest()


def get(key: str) -> Optional[Any]:
    """
    Získa hodnotu z cache (Redis alebo in-memory fallback).

    Returns:
        Cached hodnota alebo None ak nie je v cache alebo expirovala
    """
    # Skúsiť Redis najprv
    if REDIS_ENABLED and _redis_get:
        value = _redis_get(key)
        if value is not None:
            return value

    # Fallback na in-memory cache
    if key not in _cache:
        return None

    value, expiry_time = _cache[key]

    if datetime.now() > expiry_time:
        # Expired - odstrániť
        del _cache[key]
        return None

    return value


def set(key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
    """
    Uloží hodnotu do cache (Redis aj in-memory fallback).

    Args:
        key: Cache key
        value: Hodnota na uloženie
        ttl: Time to live (ak None, použije sa default)
    """
    if ttl is None:
        ttl = _default_ttl

    # Skúsiť Redis najprv
    if REDIS_ENABLED and _redis_set:
        ttl_seconds = int(ttl.total_seconds())
        _redis_set(key, value, ttl_seconds)

    # Vždy uložiť aj do in-memory (backup)
    expiry_time = datetime.now() + ttl
    _cache[key] = (value, expiry_time)


def delete(key: str) -> None:
    """Odstráni hodnotu z cache (Redis aj in-memory)."""
    # Vymazať z Redis
    if REDIS_ENABLED and _redis_delete:
        _redis_delete(key)

    # Vymazať z in-memory
    if key in _cache:
        del _cache[key]


def clear() -> None:
    """Vyčistí celý cache."""
    global _cache
    _cache = {}


def get_stats() -> Dict:
    """Vráti štatistiky cache (Redis aj in-memory)."""
    stats = {
        "cache_type": "hybrid",
        "redis_enabled": REDIS_ENABLED,
    }

    # Redis štatistiky
    if REDIS_ENABLED:
        try:
            from services.redis_cache import redis_get_stats

            redis_stats = redis_get_stats()
            stats["redis"] = redis_stats
        except Exception as e:
            stats["redis"] = {"error": str(e)}

    # In-memory štatistiky
    now = datetime.now()
    expired_count = sum(1 for _, (_, expiry) in _cache.items() if now > expiry)

    # Vyčistiť expirované
    if expired_count > 0:
        keys_to_delete = [k for k, (_, expiry) in _cache.items() if now > expiry]
        for k in keys_to_delete:
            del _cache[k]

    stats["in_memory"] = {
        "total_items": len(_cache),
        "expired_items": expired_count,
        "cache_size_mb": _estimate_cache_size(),
    }

    return stats


def _estimate_cache_size() -> float:
    """Odhad veľkosti cache v MB."""
    try:
        total_size = sum(
            len(json.dumps(value, default=str).encode()) for value, _ in _cache.values()
        )
        return round(total_size / (1024 * 1024), 2)
    except (TypeError, ValueError, KeyError):
        return 0.0
