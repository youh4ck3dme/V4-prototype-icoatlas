"""
PostgreSQL databázový servis pre ILUMINATI SYSTEM
Ukladá históriu vyhľadávaní, cache a analytics
"""

import os
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Database URL (môže byť z env alebo default)
# Na macOS s Homebrew sa používa aktuálny používateľ, nie postgres
_default_user = os.getenv("USER", os.getenv("USERNAME", "postgres"))
DATABASE_URL = os.getenv(
    "DATABASE_URL", f"postgresql://{_default_user}@localhost:5432/iluminati_db"
)

Base = declarative_base()


# Database Models
class SearchHistory(Base):
    """História vyhľadávaní"""

    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(255), nullable=False, index=True)
    country = Column(String(2), index=True)  # SK, CZ, PL, HU
    result_count = Column(Integer, default=0)
    risk_score = Column(Float)
    search_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_ip = Column(String(45))  # IPv6 support
    response_data = Column(JSON)  # Full response for analytics

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "query": self.query,
            "country": self.country,
            "result_count": self.result_count,
            "risk_score": self.risk_score,
            "search_timestamp": self.search_timestamp.isoformat()
            if self.search_timestamp
            else None,
            "user_ip": self.user_ip,
        }


class CompanyCache(Base):
    """Cache pre firmy (dlhodobé uloženie) - Hybridný model"""

    __tablename__ = "company_cache"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(
        String(100), unique=True, nullable=False, index=True
    )  # IČO, KRS, etc.
    country = Column(String(2), nullable=False, index=True)
    company_name = Column(String(500))
    data = Column(JSON, nullable=False)  # Full company data (legacy)
    company_data = Column(JSON)  # Normalized company data (12-poľový formát)
    risk_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(DateTime, default=datetime.utcnow, index=True)  # Posledná synchronizácia
    expires_at = Column(DateTime, index=True)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "identifier": self.identifier,
            "country": self.country,
            "company_name": self.company_name,
            "risk_score": self.risk_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class Analytics(Base):
    """Analytics a štatistiky"""

    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # search, export, error
    event_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_ip = Column(String(45))
    user_agent = Column(Text)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class FavoriteCompany(Base):
    """Obľúbené firmy používateľov"""

    __tablename__ = "favorite_companies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Foreign key to users.id
    company_identifier = Column(String(100), nullable=False, index=True)  # IČO, KRS, etc.
    company_name = Column(String(500), nullable=False)
    country = Column(String(2), nullable=False)
    company_data = Column(JSON)  # Full company data snapshot
    risk_score = Column(Float)
    risk_factors = Column(JSON)  # List of risk factors
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    notes = Column(Text)  # User notes about this company

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "company_identifier": self.company_identifier,
            "company_name": self.company_name,
            "country": self.country,
            "risk_score": self.risk_score,
            "risk_factors": self.risk_factors or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "notes": self.notes,
        }


# Database engine and session
engine = None
SessionLocal = None
_initialized = False


def init_database():
    """Inicializuje databázu - vytvorí tabuľky ak neexistujú"""
    global engine, SessionLocal, _initialized

    if _initialized:
        return

    try:
        # Connection Pooling (Tip 2)
        engine = create_engine(
            DATABASE_URL,
            echo=False,
            poolclass=QueuePool,
            pool_size=20,  # Zvýšené pre produkciu
            max_overflow=40,  # Burst capacity
            pool_timeout=30,
            pool_recycle=3600,  # Recycle connections every hour
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Import ERP models to ensure tables are created
        try:
            from services.auth import User  # Ensure User is loaded
            from services.api_keys import ApiKey  # Ensure ApiKey is loaded for User relationship
            from services.webhooks import Webhook  # Ensure Webhook is loaded for User relationship
            from services.erp.models import ErpConnection, ErpSyncLog  # noqa: F401
        except ImportError:
            pass  # ERP models not available yet

        # Vytvoriť tabuľky
        Base.metadata.create_all(bind=engine)
        _initialized = True
        print("✅ PostgreSQL databáza inicializovaná")
        return True
    except Exception as e:
        print(f"⚠️ PostgreSQL databáza nie je dostupná: {e}")
        print("   Používa sa len in-memory cache")
        _initialized = False
        return False


@contextmanager
def get_db_session():
    """Context manager pre databázovú session"""
    if not _initialized or SessionLocal is None:
        init_database()

    if SessionLocal is None:
        yield None
        return

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"❌ Database error: {e}")
        raise
    finally:
        session.close()


def save_search_history(
    query: str,
    country: Optional[str],
    result_count: int,
    risk_score: Optional[float],
    user_ip: Optional[str] = None,
    response_data: Optional[Dict] = None,
) -> bool:
    """Uloží vyhľadávanie do histórie"""
    if not _initialized:
        return False

    try:
        with get_db_session() as session:
            if session is None:
                return False

            history = SearchHistory(
                query=query,
                country=country,
                result_count=result_count,
                risk_score=risk_score,
                user_ip=user_ip,
                response_data=response_data,
            )
            session.add(history)
            return True
    except Exception as e:
        print(f"⚠️ Chyba pri ukladaní histórie: {e}")
        return False


def get_search_history(limit: int = 100, country: Optional[str] = None) -> List[Dict]:
    """Získa históriu vyhľadávaní"""
    if not _initialized:
        return []

    try:
        with get_db_session() as session:
            if session is None:
                return []

            query = session.query(SearchHistory)
            if country:
                query = query.filter(SearchHistory.country == country)
            query = query.order_by(SearchHistory.search_timestamp.desc()).limit(limit)

            return [item.to_dict() for item in query.all()]
    except Exception as e:
        print(f"⚠️ Chyba pri načítaní histórie: {e}")
        return []


def save_company_cache(
    identifier: str,
    country: str,
    company_name: str,
    data: Dict,
    risk_score: Optional[float] = None,
    expires_hours: int = 24,
) -> bool:
    """Uloží firmu do cache"""
    if not _initialized:
        return False

    try:
        from datetime import timedelta

        with get_db_session() as session:
            if session is None:
                return False

            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

            # Skúsiť nájsť existujúcu
            existing = (
                session.query(CompanyCache)
                .filter(
                    CompanyCache.identifier == identifier,
                    CompanyCache.country == country,
                )
                .first()
            )

            if existing:
                existing.company_name = company_name
                existing.data = data
                existing.risk_score = risk_score
                existing.updated_at = datetime.utcnow()
                existing.expires_at = expires_at
            else:
                cache = CompanyCache(
                    identifier=identifier,
                    country=country,
                    company_name=company_name,
                    data=data,
                    risk_score=risk_score,
                    expires_at=expires_at,
                )
                session.add(cache)

            return True
    except Exception as e:
        print(f"⚠️ Chyba pri ukladaní cache: {e}")
        return False


def get_company_cache(identifier: str, country: str) -> Optional[Dict]:
    """Získa firmu z cache"""
    if not _initialized:
        return None

    try:
        with get_db_session() as session:
            if session is None:
                return None

            cache = (
                session.query(CompanyCache)
                .filter(
                    CompanyCache.identifier == identifier,
                    CompanyCache.country == country,
                    CompanyCache.expires_at > datetime.utcnow(),
                )
                .first()
            )

            if cache:
                return cache.data
            return None
    except Exception as e:
        print(f"⚠️ Chyba pri načítaní cache: {e}")
        return None


def save_analytics(
    event_type: str,
    event_data: Optional[Dict] = None,
    user_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> bool:
    """Uloží analytics event"""
    if not _initialized:
        return False

    try:
        with get_db_session() as session:
            if session is None:
                return False

            analytics = Analytics(
                event_type=event_type,
                event_data=event_data,
                user_ip=user_ip,
                user_agent=user_agent,
            )
            session.add(analytics)
            return True
    except Exception as e:
        print(f"⚠️ Chyba pri ukladaní analytics: {e}")
        return False


def get_database_stats() -> Dict:
    """Vráti štatistiky databázy"""
    if not _initialized:
        return {"status": "not_initialized", "available": False}

    try:
        with get_db_session() as session:
            if session is None:
                return {"status": "no_session", "available": False}

            search_count = session.query(SearchHistory).count()
            cache_count = session.query(CompanyCache).count()
            analytics_count = session.query(Analytics).count()

            return {
                "status": "ok",
                "available": True,
                "search_history_count": search_count,
                "company_cache_count": cache_count,
                "analytics_count": analytics_count,
            }
    except Exception as e:
        return {"status": "error", "available": False, "error": str(e)}


def cleanup_expired_cache() -> int:
    """Vymaže expirovaný cache"""
    if not _initialized:
        return 0

    try:
        with get_db_session() as session:
            if session is None:
                return 0

            deleted = (
                session.query(CompanyCache)
                .filter(CompanyCache.expires_at < datetime.utcnow())
                .delete()
            )

            return deleted
    except Exception as e:
        print(f"⚠️ Chyba pri cleanup: {e}")
        return 0
