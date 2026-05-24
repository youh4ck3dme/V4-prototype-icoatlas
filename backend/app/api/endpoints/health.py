"""
Health check endpoints.
"""
from fastapi import APIRouter
from typing import Dict, Any
import httpx
import asyncio

try:
    import redis
except ImportError:
    redis = None

router = APIRouter()


async def check_database() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        from ...db.session import engine
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return {"status": "ok", "message": "Database is reachable"}
    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}


async def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity."""
    if redis is None:
        return {"status": "skipped", "message": "Redis library not installed"}
    
    try:
        from ...core.config import settings
        
        # Try to connect to Redis if configured
        if settings.REDIS_URL:
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            return {"status": "ok", "message": "Redis is reachable"}
        else:
            return {"status": "skipped", "message": "Redis not configured"}
    except Exception as e:
        return {"status": "error", "message": f"Redis error: {str(e)}"}


async def check_sentry() -> Dict[str, Any]:
    """Check Sentry configuration."""
    try:
        from ...core.config import settings
        
        if settings.SENTRY_DSN:
            return {"status": "ok", "message": "Sentry is configured"}
        else:
            return {"status": "skipped", "message": "Sentry not configured"}
    except Exception as e:
        return {"status": "error", "message": f"Sentry error: {str(e)}"}


async def check_external_apis() -> Dict[str, Any]:
    """Check external API availability."""
    external_services = {
        "ares": "https://ares.gov.cz",
        "krs": "https://api-krs.ms.gov.pl",
    }
    
    results = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service, url in external_services.items():
            try:
                response = await client.get(url)
                if response.status_code < 500:
                    results[service] = {"status": "ok", "message": f"{service.upper()} is reachable"}
                else:
                    results[service] = {"status": "degraded", "message": f"{service.upper()} returned {response.status_code}"}
            except Exception as e:
                results[service] = {"status": "error", "message": f"{service.upper()} unreachable: {str(e)}"}
    
    return results


@router.get("/health", tags=["health"])
async def health_check():
    """
    Basic health check.
    
    Returns basic status information.
    """
    from ...core.config import settings
    
    return {
        "status": "ok",
        "env": settings.ENV,
        "version": "5.0.0"
    }


@router.get("/health/detailed", tags=["health"])
async def detailed_health_check():
    """
    Detailed health check.
    
    Returns detailed status of all dependencies:
    - Database connectivity
    - Redis connectivity
    - Sentry configuration
    - External APIs availability
    """
    from ...core.config import settings
    
    # Run all checks in parallel
    db_check, redis_check, sentry_check, apis_check = await asyncio.gather(
        check_database(),
        check_redis(),
        check_sentry(),
        check_external_apis(),
        return_exceptions=True
    )
    
    # Determine overall status
    checks = {
        "database": db_check if not isinstance(db_check, Exception) else {"status": "error", "message": str(db_check)},
        "redis": redis_check if not isinstance(redis_check, Exception) else {"status": "error", "message": str(redis_check)},
        "sentry": sentry_check if not isinstance(sentry_check, Exception) else {"status": "error", "message": str(sentry_check)},
        "external_apis": apis_check if not isinstance(apis_check, Exception) else {"status": "error", "message": str(apis_check)},
    }
    
    # Overall status is "ok" if all critical services are ok
    critical_services = ["database"]
    overall_status = "ok"
    
    for service in critical_services:
        if checks.get(service, {}).get("status") == "error":
            overall_status = "degraded"
            break
    
    return {
        "status": overall_status,
        "env": settings.ENV,
        "version": "5.0.0",
        "checks": checks
    }
