"""
Dragofactu API - Main FastAPI application.

Multi-tenant ERP backend for the Dragofactu desktop client.
"""
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.database import engine
from app.models.base import Base

settings = get_settings()

# Startup logging
print(f"[STARTUP] Python version: {sys.version}", flush=True)
print(f"[STARTUP] PORT env: {os.environ.get('PORT', 'not set')}", flush=True)
print(f"[STARTUP] DATABASE_URL: {settings.DATABASE_URL[:30]}...", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create all tables
    print("[STARTUP] Creating database tables...", flush=True)
    try:
        Base.metadata.create_all(bind=engine)
        print("[STARTUP] Database tables created successfully.", flush=True)
    except Exception as e:
        print(f"[STARTUP ERROR] Failed to create tables: {e}", flush=True)
        raise
    print("[STARTUP] Application ready to receive requests.", flush=True)
    yield
    # Shutdown: Clean up if needed
    print("[SHUTDOWN] Application shutting down.", flush=True)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API backend for Dragofactu ERP - Multi-tenant invoicing system",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS middleware - Required for desktop client
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "app": settings.APP_NAME
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info."""
    return {
        "message": "Dragofactu API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


# Include API routers
print("[STARTUP] Loading API routers...", flush=True)
try:
    from app.api.router import api_router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    print("[STARTUP] API routers loaded successfully.", flush=True)
except Exception as e:
    print(f"[STARTUP ERROR] Failed to load routers: {e}", flush=True)
    raise
