from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ILUMINATI SYSTEM v5"
    ENV: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/iluminati"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
