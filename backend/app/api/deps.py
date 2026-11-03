"""
Spoločné závislosti pre prihláseného používateľa.

Token sa prijíma len v hlavičke: `Authorization: Bearer <JWT>` alebo `Authorization: Bearer ica_…`
(API kľúč), prípadne `X-API-Key: ica_…`. Nikdy nie v URL (?token=), aby nekončil v logoch a histórii.
"""
from typing import Any, Callable, Dict, Optional, TypeVar

from fastapi import Header, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from ..core.security import API_KEY_PREFIX, decode_access_token, hash_api_key
from ..services.company_store import database_configured
from ..services.user_store import UserStore

T = TypeVar("T")


async def with_users(fn: Callable[[UserStore], T]) -> T:
    """Spustí fn(store) v threadpoole; 503 ak databáza nie je nakonfigurovaná."""
    if not database_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not available")

    def run() -> T:
        with UserStore() as store:
            return fn(store)

    return await run_in_threadpool(run)


def _extract_token(authorization: Optional[str], x_api_key: Optional[str]) -> Optional[str]:
    if x_api_key:
        return x_api_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return None


async def _resolve_user(token: str) -> Optional[Dict[str, Any]]:
    if token.startswith(API_KEY_PREFIX):
        key_hash = hash_api_key(token)
        return await with_users(lambda s: s.user_for_api_key(key_hash))
    payload = decode_access_token(token)
    if not payload:
        return None
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        return None
    return await with_users(lambda s: s.get_user(user_id))


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Dict[str, Any]:
    token = _extract_token(authorization, x_api_key)
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise unauthorized
    user = await _resolve_user(token)
    if not user or not user.get("is_active"):
        raise unauthorized
    return user


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Optional[Dict[str, Any]]:
    token = _extract_token(authorization, x_api_key)
    if not token or not database_configured():
        return None
    try:
        user = await _resolve_user(token)
    except HTTPException:
        return None
    return user if user and user.get("is_active") else None
