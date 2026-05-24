from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "ILUMINATI SYSTEM v5"
    ENV: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/iluminati"
    AUTOFORM_API_TOKEN: Optional[str] = None
    
    # Redis configuration
    REDIS_URL: Optional[str] = None
    
    # Sentry configuration
    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
