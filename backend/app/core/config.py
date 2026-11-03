from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "iCOAtlas v5"
    ENV: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/iluminati"
    AUTOFORM_API_TOKEN: Optional[str] = None
    DATAHUB_API_TOKEN: Optional[str] = None

    # JWT podpis (povinný v produkcii, aspoň 32 znakov)
    SECRET_KEY: Optional[str] = None

    # Redis configuration
    REDIS_URL: Optional[str] = None
    
    # Sentry configuration
    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    
    # Stripe configuration
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    FRONTEND_URL: str = "http://localhost:8009"
    
    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), extra="ignore")

settings = Settings()
