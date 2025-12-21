from datetime import timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from services.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    User,
    authenticate_user,
    create_access_token,
    create_user,
    get_user_by_email,
)
from services.database import get_db_session

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# --- Models ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    consent_given: bool = True
    document_versions: Optional[Dict[str, str]] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    tier: str
    is_active: bool
    created_at: str
    stripe_customer_id: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


# --- Dependencies ---
def get_db():
    with get_db_session() as db:
        yield db


# --- Endpoints ---

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    existing_user = get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists",
        )
    
    # Create user
    # Note: consent_ip/user_agent would be extracted from Request in a real scenario
    user = create_user(
        db=db,
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
        consent_given=user_in.consent_given,
        document_versions=user_in.document_versions
    )
    
    # Helper to serialize datetimes
    return _serialize_user(user)


@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Standard form fields: username (email) and password.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "tier": user.tier.value},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.get("/me", response_model=UserResponse)
def read_users_me(token: str, db: Session = Depends(get_db)):
    """
    Get current user details (Using token manually for simplicity in MVP, 
    normally we'd use a dependency `get_current_user`).
    To keep this simple and compatible with simple fetch calls, we accept token query/header logic elsewhere,
    but here we might need a dependency to extract user from token.
    
    REVISION: Let's assume the frontend passes valid JWT in Header.
    For now, let's implement a quick dependency here to DRY.
    """
    from fastapi.security import OAuth2PasswordBearer
    from services.auth import decode_access_token
    
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
    
    # This logic should ideally be shared, but for this task scope, inline is fine.
    try:
        payload = decode_access_token(token)
        if payload is None:
             raise HTTPException(status_code=401, detail="Invalid token")
        email = payload.get("sub")
        if email is None:
             raise HTTPException(status_code=401, detail="Invalid token payload")
    except Exception:
        raise HTTPException(status_code=401, detail="Token validation failed")
        
    user = get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
        
    return _serialize_user(user)


# Helper
def _serialize_user(user: User):
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "tier": user.tier.value,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "stripe_customer_id": user.stripe_customer_id
    }
