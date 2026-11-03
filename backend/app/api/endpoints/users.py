"""
Prihlásenie, API kľúče, história, obľúbené a export – endpointy, ktoré volá frontend
(frontend/src/contexts/AuthContext.jsx, config/api.js, pages/Dashboard.jsx, pages/ProfilePage.jsx,
pages/HomePageNew.jsx, utils/export.js). Prenesené z backend_legacy_20251229_195800/main.py
a routers/auth.py, routers/api_keys.py.
"""
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from ...core.security import (
    create_access_token,
    generate_api_key,
    hash_password,
    password_problem,
    tier_limits,
    verify_password,
)
from ...services.user_store import (
    EmailTakenError,
    public_api_key,
    public_favorite,
    public_history,
    public_user,
)
from ..deps import get_current_user, get_optional_user, with_users

logger = logging.getLogger("uvicorn.error")

router = APIRouter()

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- auth ----------

class RegisterIn(BaseModel):
    email: str = Field(..., max_length=254)
    password: str
    full_name: Optional[str] = Field(None, max_length=200)
    consent_given: bool = False
    document_versions: Optional[Dict[str, str]] = None


@router.post("/auth/register", tags=["auth"])
async def register(body: RegisterIn, request: Request) -> Dict[str, Any]:
    email = body.email.strip()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Neplatný e-mail")
    problem = password_problem(body.password)
    if problem:
        raise HTTPException(status_code=400, detail=problem)
    pw_hash = await run_in_threadpool(hash_password, body.password)
    ip = request.client.host if request.client else None
    ua = request.headers.get("User-Agent")
    try:
        user = await with_users(lambda s: s.create_user(email, pw_hash, body.full_name, body.consent_given, ip, ua,
                                                         body.document_versions))
    except EmailTakenError:
        raise HTTPException(status_code=400, detail="Email already registered")
    return public_user(user)


async def _login(username: str, password: str) -> Dict[str, Any]:
    user = await with_users(lambda s: s.get_user_by_email(username))
    ok = user is not None and await run_in_threadpool(verify_password, password, user["password_hash"])
    if not ok or not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    await with_users(lambda s: s.touch_login(user["id"]))
    return {
        "access_token": create_access_token(user["id"], user["tier"]),
        "token_type": "bearer",
        "user": {**public_user(user), "limits": tier_limits(user["tier"])},
    }


@router.post("/auth/token", tags=["auth"])
async def login_token(form: OAuth2PasswordRequestForm = Depends()) -> Dict[str, Any]:
    return await _login(form.username, form.password)


@router.post("/auth/login", tags=["auth"])
async def login(form: OAuth2PasswordRequestForm = Depends()) -> Dict[str, Any]:
    return await _login(form.username, form.password)


@router.get("/auth/me", tags=["auth"])
async def me(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return public_user(user)


@router.get("/auth/tier/limits", tags=["auth"])
async def my_limits(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return tier_limits(user["tier"])


# ---------- API keys ----------

class ApiKeyIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = Field(default_factory=lambda: ["read"])
    expires_days: Optional[int] = Field(None, ge=1, le=3650)


@router.post("/api-keys", tags=["api-keys"])
async def create_api_key(body: ApiKeyIn, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if not tier_limits(user["tier"]).get("api_access"):
        raise HTTPException(status_code=403, detail="API prístup nie je v tomto programe")
    perms = [p for p in body.permissions if p in ("read", "write")] or ["read"]
    full, prefix, key_hash = generate_api_key()
    row = await with_users(lambda s: s.create_api_key(user["id"], body.name, prefix, key_hash, perms,
                                                      body.expires_days))
    return {**public_api_key(row), "key": full}  # celý kľúč sa vráti iba raz


@router.get("/api-keys", tags=["api-keys"])
async def list_api_keys(user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    return [public_api_key(r) for r in await with_users(lambda s: s.list_api_keys(user["id"]))]


@router.delete("/api-keys/{key_id}", tags=["api-keys"])
async def revoke_api_key(key_id: int, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if not await with_users(lambda s: s.revoke_api_key(user["id"], key_id)):
        raise HTTPException(status_code=404, detail="API key not found")
    return {"success": True}


# ---------- history ----------

@router.get("/search/history", tags=["user"])
async def search_history(
    limit: int = Query(100, ge=1, le=500),
    country: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    rows = await with_users(lambda s: s.list_history(user["id"], limit, country))
    return [public_history(r) for r in rows]


async def record_search(user: Optional[Dict[str, Any]], query: str, country: Optional[str],
                        atlas_id: Optional[str], result_count: Optional[int]) -> None:
    """Zapíše vyhľadávanie prihláseného používateľa; chyba zápisu nesmie zhodiť vyhľadávanie."""
    if not user:
        return
    try:
        await with_users(lambda s: s.add_history(user["id"], query, country, atlas_id, result_count))
    except Exception:
        logger.exception("Saving search history failed")


# ---------- favorites ----------

class FavoriteIn(BaseModel):
    company_identifier: str = Field(..., min_length=1, max_length=64)
    company_name: str = Field(..., min_length=1, max_length=300)
    country: str = Field(..., min_length=2, max_length=2)
    company_data: Optional[Dict[str, Any]] = None
    risk_score: Optional[float] = None
    risk_factors: Optional[List[Any]] = None
    notes: Optional[str] = Field(None, max_length=5000)


class NotesIn(BaseModel):
    notes: str = Field("", max_length=5000)


@router.post("/user/favorites", tags=["user"])
async def add_favorite(body: FavoriteIn, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    data = body.model_dump()
    data["country"] = data["country"].upper()
    row = await with_users(lambda s: s.upsert_favorite(user["id"], data))
    return {"success": True, "favorite": public_favorite(row)}


@router.get("/user/favorites", tags=["user"])
async def list_favorites(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    rows = await with_users(lambda s: s.list_favorites(user["id"], limit))
    return {"success": True, "favorites": [public_favorite(r) for r in rows], "count": len(rows)}


@router.delete("/user/favorites/{favorite_id}", tags=["user"])
async def remove_favorite(favorite_id: int, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if not await with_users(lambda s: s.remove_favorite(user["id"], favorite_id)):
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"success": True, "message": "Favorite removed"}


@router.get("/user/favorites/check/{company_identifier}/{country}", tags=["user"])
async def check_favorite(company_identifier: str, country: str,
                         user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    fav = await with_users(lambda s: s.is_favorite(user["id"], company_identifier, country))
    return {"success": True, "is_favorite": fav}


@router.put("/user/favorites/{favorite_id}/notes", tags=["user"])
async def update_notes(favorite_id: int, body: NotesIn,
                       user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    row = await with_users(lambda s: s.update_favorite_notes(user["id"], favorite_id, body.notes))
    if not row:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"success": True, "favorite": public_favorite(row)}


# ---------- export ----------

_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _xlsx_response(content: bytes, stem: str) -> Response:
    filename = f"icoatlas-{stem}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx"
    return Response(content=content, media_type=_XLSX,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.post("/export/excel", tags=["export"])
async def export_excel(graph_data: Dict[str, Any],
                       user: Optional[Dict[str, Any]] = Depends(get_optional_user)) -> Response:
    from ...services.export_service import export_to_excel

    try:
        content = await run_in_threadpool(export_to_excel, graph_data)
    except ImportError:
        raise HTTPException(status_code=503, detail="Excel export nie je dostupný")
    return _xlsx_response(content, "export")


@router.post("/export/batch-excel", tags=["export"])
async def export_batch_excel(companies: List[Dict[str, Any]],
                             user: Dict[str, Any] = Depends(get_current_user)) -> Response:
    from ...services.export_service import export_batch_to_excel

    limit = tier_limits(user["tier"]).get("export_limit", 0)
    if limit != -1 and len(companies) > limit:
        raise HTTPException(status_code=403, detail=f"Export je obmedzený na {limit} firiem")
    try:
        content = await run_in_threadpool(export_batch_to_excel, companies)
    except ImportError:
        raise HTTPException(status_code=503, detail="Excel export nie je dostupný")
    return _xlsx_response(content, "batch-export")
