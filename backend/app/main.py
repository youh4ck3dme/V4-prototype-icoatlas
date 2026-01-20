from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import json

from .api import router as api_router
from .core.config import settings
from .db.session import engine, Base
from .middleware.security import SecurityHeadersMiddleware, HTTPSRedirectMiddleware, RateLimitMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown logic if needed

app = FastAPI(
    title="ILUMINATI SYSTEM v5 API",
    version="5.0.0",
    description="Enterprise Business Intelligence Platform for V4 Region",
    lifespan=lifespan
)

# Load CORS origins from environment
cors_origins_str = os.getenv("CORS_ORIGINS", '["http://localhost:8009", "http://localhost:8010", "http://localhost:5173", "http://localhost:3000"]')
try:
    cors_origins = json.loads(cors_origins_str)
except json.JSONDecodeError:
    cors_origins = ["http://localhost:3000"]

# Security Middlewares (order matters!)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(HTTPSRedirectMiddleware)

# Rate limiting - default 60 requests per minute, configurable via env
rate_limit = int(os.getenv("RATE_LIMIT_DEFAULT", "60"))
app.add_middleware(RateLimitMiddleware, requests_per_minute=rate_limit)

# CORS - strict configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

app.include_router(api_router, prefix="/api")

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "version": app.version}
