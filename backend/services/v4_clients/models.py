from dataclasses import dataclass
from typing import Optional, List
from datetime import date


@dataclass
class NormalizedCompany:
    """Jednotný model pre všetky V4 krajiny"""

    # Required fields (no defaults)
    country: str  # SK, CZ, PL, HU
    primary_id: str  # IČO, KRS, Adószám
    legal_name: str
    status: str  # active, liquidation, bankrupt, dissolved
    source_api: str
    fetched_at: str

    # Optional fields (with defaults)
    tax_id: Optional[str] = None  # DIČ, NIP, Adószám
    vat_id: Optional[str] = None  # IČ DPH, EU VAT
    legal_form: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    city_part: Optional[str] = None
    postal_code: Optional[str] = None
    registration_date: Optional[date] = None
    dissolution_date: Optional[date] = None
    executives: Optional[List[str]] = None
    shareholders: Optional[List[str]] = None
    risk_score: int = 0
    risk_flags: Optional[List[str]] = None
    raw_data: Optional[dict] = None


class V4APIError(Exception):
    """Základná chyba pre V4 API"""
    pass


class RateLimitError(V4APIError):
    """HTTP 429 - prekročený limit"""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")


class AuthenticationError(V4APIError):
    """Chyba autentifikácie"""
    pass


class NotFoundError(V4APIError):
    """Subjekt neexistuje"""
    pass