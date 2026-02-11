"""
Dragofactu API - Main FastAPI application.

Multi-tenant ERP backend for the Dragofactu desktop client.
"""
import os
import sys
import time
import uuid
import logging
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.config import get_settings
from app.database import engine, SessionLocal
from app.models.base import Base

settings = get_settings()

# App start time for uptime calculation
_app_start_time = time.time()

# Request metrics (in-memory counters)
_request_metrics = {
    "total_requests": 0,
    "total_errors": 0,
    "status_codes": {},
    "endpoint_latency": {},
}
_metrics_lock = __import__("threading").Lock()


# ============================================================================
# STRUCTURED JSON LOGGING
# ============================================================================

class JSONFormatter(logging.Formatter):
    """JSON log formatter for production log aggregation."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "company_id"):
            log_entry["company_id"] = record.company_id
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, default=str)


# Configure logging - JSON in production, readable in dev
log_handler = logging.StreamHandler()
if settings.DEBUG:
    log_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
else:
    log_handler.setFormatter(JSONFormatter())

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    handlers=[log_handler],
)
logger = logging.getLogger("dragofactu")

# Startup logging
logger.info(f"Python version: {sys.version}")
logger.info(f"PORT env: {os.environ.get('PORT', 'not set')}")
logger.info(f"DATABASE_URL: {settings.DATABASE_URL[:30]}...")
logger.info(f"DEBUG mode: {settings.DEBUG}")
logger.info(f"CORS origins: {settings.get_cors_origins()}")


# ============================================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        if request.url.path.startswith("/api/") or request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        else:
            # SPA frontend needs inline styles (Tailwind) and scripts (Vite)
            response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; font-src 'self' data:"

        # Strict Transport Security (only in production)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Remove server header (don't reveal tech stack)
        response.headers["Server"] = "Dragofactu"

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with method, path, status, duration, and request_id."""

    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID for tracing
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
        request.state.request_id = request_id

        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        # Add request ID to response
        response.headers["X-Request-ID"] = request_id

        # Update metrics
        status_code = response.status_code
        path = request.url.path
        with _metrics_lock:
            _request_metrics["total_requests"] += 1
            if status_code >= 400:
                _request_metrics["total_errors"] += 1
            status_key = str(status_code)
            _request_metrics["status_codes"][status_key] = _request_metrics["status_codes"].get(status_key, 0) + 1
            # Track latency per endpoint (keep last value)
            _request_metrics["endpoint_latency"][f"{request.method} {path}"] = round(duration * 1000, 2)

        logger.info(
            f"{request.method} {path} -> {status_code} ({duration:.3f}s) [{request_id}]"
        )
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests exceeding MAX_REQUEST_SIZE."""

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"}
            )
        return await call_next(request)


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """Global rate limiting: 120 requests/minute per IP."""

    # Paths exempt from rate limiting
    EXEMPT_PATHS = {"/health", "/health/ready", "/metrics", "/", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        # Disable in DEBUG/test mode
        if settings.DEBUG:
            return await call_next(request)

        path = request.url.path
        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        from app.core.security_utils import api_rate_limiter
        client_ip = request.client.host if request.client else "unknown"

        if not api_rate_limiter.is_allowed(client_ip):
            retry_after = api_rate_limiter.get_retry_after(client_ip)
            return JSONResponse(
                status_code=429,
                content={"detail": f"Too many requests. Retry after {retry_after} seconds."},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)


def _init_sentry():
    """Initialize Sentry error tracking if DSN is configured."""
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured, error tracking disabled.")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment="production" if not settings.DEBUG else "development",
            release=f"dragofactu@{settings.APP_VERSION}",
            traces_sample_rate=0.1,  # 10% of transactions for performance
            profiles_sample_rate=0.1,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
            send_default_pii=False,  # Don't send user emails/IPs
        )
        logger.info("Sentry error tracking initialized.")
    except ImportError:
        logger.warning("sentry-sdk not installed, error tracking disabled.")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")


def _run_migrations():
    """
    Run safe ALTER TABLE migrations for columns added after initial deployment.
    Each migration checks if the column exists before adding it, so this is
    idempotent and safe to run on every startup.
    """
    migrations = [
        ("companies", "logo_base64", "TEXT"),
        ("companies", "pdf_footer_text", "TEXT"),
    ]
    with engine.connect() as conn:
        for table, column, col_type in migrations:
            try:
                # Check if column exists (works for both PostgreSQL and SQLite)
                result = conn.execute(text(
                    f"SELECT column_name FROM information_schema.columns "
                    f"WHERE table_name = :table AND column_name = :column"
                ), {"table": table, "column": column})
                if result.first() is None:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}'))
                    conn.commit()
                    logger.info(f"Migration: added column {table}.{column}")
            except Exception:
                # SQLite doesn't support information_schema; try adding directly
                try:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}'))
                    conn.commit()
                    logger.info(f"Migration: added column {table}.{column}")
                except Exception:
                    # Column likely already exists
                    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Initialize Sentry
    _init_sentry()

    # Startup: Create all tables
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

    # Run column migrations for existing tables
    try:
        _run_migrations()
    except Exception as e:
        logger.warning(f"Migration warning (non-fatal): {e}")

    logger.info("Application ready to receive requests.")
    yield
    # Shutdown
    logger.info("Application shutting down.")

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

# Middleware stack (order matters: outermost first)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(GlobalRateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware - Required for desktop client
# In production, set ALLOWED_ORIGINS env var to comma-separated list
cors_origins = settings.get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["X-Total-Count"],  # For pagination
    max_age=600,  # Cache preflight for 10 minutes
)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Liveness probe - checks if the app is running.
    Used by Railway healthcheck and load balancers.
    """
    uptime = time.time() - _app_start_time
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "app": settings.APP_NAME,
        "uptime_seconds": round(uptime, 1),
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness probe - checks if the app can serve requests.
    Verifies database connectivity.
    """
    checks = {}
    overall_healthy = True

    # Check database connectivity
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            checks["database"] = {"status": "ok"}
        finally:
            db.close()
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)}
        overall_healthy = False

    uptime = time.time() - _app_start_time
    status_code = 200 if overall_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if overall_healthy else "degraded",
            "version": settings.APP_VERSION,
            "uptime_seconds": round(uptime, 1),
            "checks": checks,
        }
    )


@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """
    Application metrics endpoint.
    Returns request counts, error rates, and latency data.
    """
    uptime = time.time() - _app_start_time
    with _metrics_lock:
        total = _request_metrics["total_requests"]
        errors = _request_metrics["total_errors"]
        return {
            "uptime_seconds": round(uptime, 1),
            "requests": {
                "total": total,
                "errors": errors,
                "error_rate": round(errors / max(total, 1) * 100, 2),
            },
            "status_codes": dict(_request_metrics["status_codes"]),
            "endpoint_latency_ms": dict(_request_metrics["endpoint_latency"]),
        }


# Include API routers
logger.info("Loading API routers...")
try:
    from app.api.router import api_router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    logger.info("API routers loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load routers: {e}")
    raise


# ============================================================================
# SERVE FRONTEND STATIC FILES (production)
# ============================================================================

_static_dir = Path(__file__).resolve().parent.parent / "static"

if _static_dir.is_dir():
    logger.info(f"Serving frontend static files from {_static_dir}")
    app.mount("/assets", StaticFiles(directory=str(_static_dir / "assets")), name="static-assets")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        """Serve the SPA index page."""
        return FileResponse(str(_static_dir / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve the SPA frontend. API routes are handled above by priority."""
        file_path = _static_dir / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_static_dir / "index.html"))
else:
    logger.info("No static directory found, frontend not served.")

    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API info (no frontend deployed)."""
        return {
            "message": "Dragofactu API",
            "version": settings.APP_VERSION,
            "docs": "/docs"
        }
