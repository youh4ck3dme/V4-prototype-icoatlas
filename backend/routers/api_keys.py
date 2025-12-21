from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.api_keys import (
    create_api_key,
    get_user_api_keys,
    revoke_api_key
)
from services.auth import decode_access_token, get_user_by_email, User
from services.database import get_db_session

router = APIRouter(prefix="/api/api-keys", tags=["API Keys"])


# --- Models ---
class ApiKeyCreate(BaseModel):
    name: str
    permissions: Optional[List[str]] = ["read"]
    ip_whitelist: Optional[List[str]] = None


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    created_at: str
    expires_at: Optional[str]
    is_active: bool
    # Key is ONLY returned on creation

    class Config:
        from_attributes = True


class ApiKeyCreatedResponse(ApiKeyResponse):
    key: str  # Full key returned only once


# --- Dependencies ---
def get_db():
    with get_db_session() as db:
        yield db


def get_current_user(token: str, db: Session = Depends(get_db)) -> User:
    """
    Extract user from token.
    Ideally this should be a shared dependency in a `deps.py` file,
    but for this implementation phase strict separation isn't enforced yet.
    """
    try:
        payload = decode_access_token(token)
        if payload is None:
             raise HTTPException(status_code=401, detail="Invalid token")
        email = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Token validation failed")
        
    user = get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# --- Endpoints ---

@router.post("", response_model=ApiKeyCreatedResponse)
def create_new_api_key(
    key_in: ApiKeyCreate,
    token: str,  # In real app: Depends(oauth2_scheme)
    db: Session = Depends(get_db)
):
    """
    Create a new API key (Enterprise users only).
    """
    user = get_current_user(token, db)
    
    # Check Tier
    if user.tier.value != "enterprise":
        raise HTTPException(
            status_code=403, 
            detail="API Keys are only available for ENTERPRISE tier."
        )

    # Create Key
    result = create_api_key(
        db, 
        user_id=user.id, 
        name=key_in.name,
        permissions=key_in.permissions,
        ip_whitelist=key_in.ip_whitelist
    )
    
    return result


@router.get("", response_model=List[ApiKeyResponse])
def list_api_keys(
    token: str,
    db: Session = Depends(get_db)
):
    """
    List all active API keys for the current user.
    """
    user = get_current_user(token, db)
    keys = get_user_api_keys(db, user.id)
    
    # Filter active only? Or all? Usually show all but mark revoked.
    # Service returns all ordered by created_at desc.
    return [
        {
            "id": k.id,
            "name": k.name,
            "prefix": k.prefix,
            "created_at": k.created_at.isoformat(),
            "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            "is_active": k.is_active
        }
        for k in keys
    ]


@router.delete("/{key_id}")
def revoke_key(
    key_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Revoke (delete/deactivate) an API key.
    """
    user = get_current_user(token, db)
    success = revoke_api_key(db, key_id, user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="API Key not found or does not belong to user")
        
    return {"status": "success", "message": "API Key revoked"}
