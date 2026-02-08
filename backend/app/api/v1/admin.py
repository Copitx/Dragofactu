"""
Admin endpoints: system info, database stats, backup info.
Restricted to ADMIN role.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from app.api.deps import get_db, get_current_user
from app.models import User, UserRole, Company, Client, Product, Document

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require ADMIN role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador"
        )
    return current_user


@router.get("/system-info")
async def get_system_info(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system and database information."""
    from app.config import get_settings
    settings = get_settings()

    # Database info
    db_info = {}
    try:
        if settings.DATABASE_URL.startswith("postgresql"):
            # PostgreSQL specific info
            result = db.execute(text("SELECT version()")).scalar()
            db_info["engine"] = "PostgreSQL"
            db_info["version"] = result

            # Database size
            result = db.execute(text(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            )).scalar()
            db_info["size"] = result

            # Connection count
            result = db.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
            )).scalar()
            db_info["active_connections"] = result
        else:
            db_info["engine"] = "SQLite"
            db_info["version"] = db.execute(text("SELECT sqlite_version()")).scalar()
    except Exception as e:
        db_info["error"] = str(e)

    # Table counts for this company
    counts = {
        "companies": db.query(func.count(Company.id)).scalar(),
        "users": db.query(func.count(User.id)).scalar(),
        "clients": db.query(func.count(Client.id)).filter(
            Client.company_id == current_user.company_id
        ).scalar(),
        "products": db.query(func.count(Product.id)).filter(
            Product.company_id == current_user.company_id
        ).scalar(),
        "documents": db.query(func.count(Document.id)).filter(
            Document.company_id == current_user.company_id
        ).scalar(),
    }

    return {
        "app_version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG,
        "database": db_info,
        "record_counts": counts,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/backup-info")
async def get_backup_info(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get backup information.
    Railway PostgreSQL provides automatic daily backups.
    This endpoint shows DB stats useful for backup verification.
    """
    from app.config import get_settings
    settings = get_settings()

    info = {
        "provider": "Railway PostgreSQL" if "postgresql" in settings.DATABASE_URL else "SQLite (local)",
        "automatic_backups": "postgresql" in settings.DATABASE_URL,
        "backup_note": "Railway provides automatic daily snapshots for PostgreSQL databases.",
    }

    if settings.DATABASE_URL.startswith("postgresql"):
        try:
            # Last vacuum / analyze time
            result = db.execute(text(
                "SELECT schemaname, relname, last_autovacuum, last_autoanalyze "
                "FROM pg_stat_user_tables ORDER BY last_autovacuum DESC NULLS LAST LIMIT 5"
            )).fetchall()
            info["recent_maintenance"] = [
                {
                    "table": f"{row[0]}.{row[1]}",
                    "last_vacuum": row[2].isoformat() if row[2] else None,
                    "last_analyze": row[3].isoformat() if row[3] else None,
                }
                for row in result
            ]
        except Exception:
            pass

    return info
