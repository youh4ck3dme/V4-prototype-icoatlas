"""
Heslá, JWT a API kľúče pre v5.

- Heslá: hashlib.scrypt (štandardná knižnica), formát "scrypt$n$r$p$salt$hash".
- JWT: PyJWT, HS256, kľúč SECRET_KEY z prostredia. V produkcii (ENV=production) je povinný,
  inak sa vygeneruje náhodný kľúč na beh procesu (tokeny po reštarte neplatia).
- API kľúče: "ica_" + náhodný reťazec; v DB je len SHA-256 hash a prefix na zobrazenie.
"""
import base64
import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import jwt

logger = logging.getLogger("uvicorn.error")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(days=7)
MIN_PASSWORD_LEN = 8
MAX_PASSWORD_LEN = 256
MIN_SECRET_LEN = 32

_SCRYPT_N, _SCRYPT_R, _SCRYPT_P, _SCRYPT_DKLEN = 2 ** 14, 8, 1, 64
API_KEY_PREFIX = "ica_"

_ephemeral_secret: Optional[str] = None


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R,
                            p=_SCRYPT_P, dklen=_SCRYPT_DKLEN)
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, digest = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = _unb64(digest)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=_unb64(salt), n=int(n), r=int(r),
                                p=int(p), dklen=len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def password_problem(password: str) -> Optional[str]:
    if len(password) < MIN_PASSWORD_LEN:
        return f"Heslo musí mať aspoň {MIN_PASSWORD_LEN} znakov"
    if len(password) > MAX_PASSWORD_LEN:
        return f"Heslo môže mať najviac {MAX_PASSWORD_LEN} znakov"
    return None


def get_secret_key() -> str:
    global _ephemeral_secret
    from .config import settings

    key = settings.SECRET_KEY or os.getenv("SECRET_KEY")
    if key and ("CHANGE_ME" in key.upper() or "YOUR-SECRET" in key.upper()):
        key = None  # zástupná hodnota z .env*.example nie je tajomstvo
    if key and len(key) >= MIN_SECRET_LEN:
        return key
    if settings.ENV.lower() in ("production", "prod"):
        raise RuntimeError(f"SECRET_KEY musí byť nastavený (aspoň {MIN_SECRET_LEN} znakov) v produkcii")
    if _ephemeral_secret is None:
        logger.warning("SECRET_KEY nie je nastavený: používam dočasný kľúč, tokeny po reštarte neplatia")
        _ephemeral_secret = secrets.token_urlsafe(48)
    return _ephemeral_secret


def create_access_token(user_id: int, tier: str, ttl: timedelta = ACCESS_TOKEN_TTL) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "tier": tier, "type": "access", "iat": now, "exp": now + ttl}
    return jwt.encode(payload, get_secret_key(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[JWT_ALGORITHM],
                             options={"require": ["exp", "sub"]})
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    return payload


def generate_api_key() -> Tuple[str, str, str]:
    """Vráti (celý kľúč, prefix na zobrazenie, sha256 hash)."""
    full = API_KEY_PREFIX + secrets.token_urlsafe(32)
    return full, full[:12], hash_api_key(full)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


TIER_LIMITS: Dict[str, Dict[str, Any]] = {
    # prevzaté z backend_legacy_…/services/auth.py:get_user_tier_limits (-1 = bez limitu)
    "free": {"searches_per_day": 10, "searches_per_month": 100, "export_limit": 5,
             "api_access": False, "advanced_features": False},
    "pro": {"searches_per_day": 100, "searches_per_month": 2000, "export_limit": 100,
            "api_access": False, "advanced_features": True},
    "enterprise": {"searches_per_day": -1, "searches_per_month": -1, "export_limit": -1,
                   "api_access": True, "advanced_features": True},
}


def tier_limits(tier: str) -> Dict[str, Any]:
    return dict(TIER_LIMITS.get(tier, TIER_LIMITS["free"]))
