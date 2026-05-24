from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from contextlib import asynccontextmanager
from .api import router as api_router
from .core.config import settings
from .db.session import engine, Base

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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. Change in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

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

