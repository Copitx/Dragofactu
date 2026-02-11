"""
Company settings endpoints.
GET/PUT for current user's company configuration.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.models import User, Company
from app.schemas.company import CompanyUpdate, CompanyResponse

router = APIRouter(prefix="/company", tags=["Company"])


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
