"""
Company settings endpoints.
GET/PUT for current user's company configuration.
"""
import smtplib
import socket
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.models import User, Company
from app.schemas.company import (
    CompanyUpdate,
    CompanyResponse,
    CompanyEmailSettingsUpdate,
    CompanyEmailSettingsResponse,
)
from app.core.security import encrypt_secret_value, decrypt_secret_value
from app.core.email import get_managed_email_config

router = APIRouter(prefix="/company", tags=["Company"])


def _build_company_email_response(company: Company) -> CompanyEmailSettingsResponse:
    return CompanyEmailSettingsResponse(
        configured=company.smtp_configured,
        smtp_host=company.smtp_host,
        smtp_port=company.smtp_port or 587,
        smtp_user=company.smtp_user,
        smtp_use_tls=bool(company.smtp_use_tls),
        smtp_from_email=company.smtp_from_email,
        smtp_from_name=company.smtp_from_name,
    )


@router.get("/settings", response_model=CompanyResponse)
async def get_company_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clients.read"))
):
    """Get current user's company settings."""
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/settings", response_model=CompanyResponse)
async def update_company_settings(
    data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin"))
):
    """Update current user's company settings. Admin only."""
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(company, key, value)

    db.commit()
    db.refresh(company)
    return company


@router.get("/email/settings", response_model=CompanyEmailSettingsResponse)
async def get_company_email_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin"))
):
    """Get current company SMTP settings (without password)."""
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return _build_company_email_response(company)


@router.put("/email/settings", response_model=CompanyEmailSettingsResponse)
async def update_company_email_settings(
    data: CompanyEmailSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin"))
):
    """Update current company SMTP settings (password stored encrypted)."""
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_data = data.model_dump(exclude_unset=True)

    if "smtp_host" in update_data:
        company.smtp_host = (update_data.get("smtp_host") or "").strip() or None
    if "smtp_port" in update_data:
        company.smtp_port = update_data.get("smtp_port") or 587
    if "smtp_user" in update_data:
        company.smtp_user = (update_data.get("smtp_user") or "").strip() or None
    if "smtp_use_tls" in update_data:
        company.smtp_use_tls = bool(update_data.get("smtp_use_tls"))
    if "smtp_from_email" in update_data:
        company.smtp_from_email = (update_data.get("smtp_from_email") or "").strip() or None
    if "smtp_from_name" in update_data:
        company.smtp_from_name = (update_data.get("smtp_from_name") or "").strip() or None

    # Password behavior:
    # - omitted: keep existing
    # - empty string: clear saved password
    # - non-empty: encrypt and store
    if "smtp_password" in update_data:
        raw_password = (update_data.get("smtp_password") or "").strip()
        if raw_password:
            company.smtp_password_encrypted = encrypt_secret_value(raw_password)
        else:
            company.smtp_password_encrypted = None

    db.commit()
    db.refresh(company)
    return _build_company_email_response(company)


@router.post("/email/test")
async def test_company_email_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin"))
):
    """Test current company SMTP connection with login."""
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    managed = get_managed_email_config()

    if not company.smtp_configured:
        if managed:
            return {
                "success": True,
                "message": "Canal de correo gestionado activo (API HTTPS). No hace falta configurar SMTP por usuario.",
            }
        raise HTTPException(status_code=400, detail="Correo no configurado para la empresa")

    smtp_password = decrypt_secret_value(company.smtp_password_encrypted or "")
    if not smtp_password:
        raise HTTPException(status_code=400, detail="Configuración de correo inválida")

    try:
        with smtplib.SMTP(company.smtp_host, company.smtp_port or 587, timeout=15) as server:
            if company.smtp_use_tls:
                server.starttls()
            server.login(company.smtp_user, smtp_password)
    except (socket.timeout, TimeoutError):
        if managed:
            return {
                "success": True,
                "message": "SMTP bloqueado por hosting. Se usara canal gestionado (API HTTPS).",
            }
        raise HTTPException(
            status_code=400,
            detail="Timeout conectando al servidor SMTP. Es posible que el hosting bloquee puertos SMTP salientes.",
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo conectar con SMTP: {str(exc)}")

    return {"success": True, "message": "Conexión SMTP verificada"}
