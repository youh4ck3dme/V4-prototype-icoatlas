from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from contextlib import asynccontextmanager
from .api import router as api_router
from .core.config import settings
from .db.session import engine, Base
from .core.monitoring import init_sentry
from .middleware.monitoring import PrometheusMiddleware, SentryMiddleware
from .api.endpoints.metrics import router as metrics_router
from .api.endpoints.health import router as health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Sentry
    init_sentry(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        environment=settings.ENV
    )
    # create tables
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

# Add monitoring middleware
app.add_middleware(PrometheusMiddleware)
app.add_middleware(SentryMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. Change in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(health_router)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "ok", 
        "env": settings.ENV,
        "version": app.version
    }

