"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config import get_settings

# Import Base from models to ensure single source of truth
from app.models.base import Base

settings = get_settings()

# Create engine - SQLite needs special handling
connect_args = {}
pool_class = None

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # For in-memory SQLite, use StaticPool to share connection
    if ":memory:" in settings.DATABASE_URL:
        pool_class = StaticPool

engine_kwargs = {
    "connect_args": connect_args
}
if pool_class:
    engine_kwargs["poolclass"] = pool_class

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
