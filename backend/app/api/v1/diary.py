"""
Diary entries CRUD endpoints.
"""
from typing import Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user, require_permission
from app.models import DiaryEntry, User
from app.schemas import (
    DiaryEntryCreate, DiaryEntryUpdate, DiaryEntryResponse, DiaryEntryList, MessageResponse
)

router = APIRouter(prefix="/diary", tags=["Diario"])


@router.get("", response_model=DiaryEntryList)
async def list_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    pinned_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("diary.read"))
):
    """Listar entradas del diario."""
    query = db.query(DiaryEntry).filter(DiaryEntry.company_id == current_user.company_id)

    if date_from:
        query = query.filter(DiaryEntry.entry_date >= datetime.combine(date_from, datetime.min.time()))

    if date_to:
        query = query.filter(DiaryEntry.entry_date <= datetime.combine(date_to, datetime.max.time()))

    if pinned_only:
        query = query.filter(DiaryEntry.is_pinned == True)

    total = query.count()
    entries = query.order_by(DiaryEntry.entry_date.desc()).offset(skip).limit(limit).all()

    return DiaryEntryList(
        items=[DiaryEntryResponse.model_validate(e) for e in entries],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=DiaryEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    data: DiaryEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("diary.create"))
):
    """Crear entrada en el diario."""
    entry = DiaryEntry(
        company_id=current_user.company_id,
        user_id=current_user.id,
        **data.model_dump()
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return DiaryEntryResponse.model_validate(entry)


@router.get("/{entry_id}", response_model=DiaryEntryResponse)
async def get_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("diary.read"))
):
    """Obtener entrada del diario."""
    entry = db.query(DiaryEntry).filter(
        DiaryEntry.id == entry_id,
        DiaryEntry.company_id == current_user.company_id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")

    return DiaryEntryResponse.model_validate(entry)


@router.put("/{entry_id}", response_model=DiaryEntryResponse)
async def update_entry(
    entry_id: UUID,
    data: DiaryEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("diary.update"))
):
    """Actualizar entrada del diario."""
    entry = db.query(DiaryEntry).filter(
        DiaryEntry.id == entry_id,
        DiaryEntry.company_id == current_user.company_id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)

    db.commit()
    db.refresh(entry)

    return DiaryEntryResponse.model_validate(entry)


@router.delete("/{entry_id}", response_model=MessageResponse)
async def delete_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("diary.delete"))
):
    """Eliminar entrada del diario."""
    entry = db.query(DiaryEntry).filter(
        DiaryEntry.id == entry_id,
        DiaryEntry.company_id == current_user.company_id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")

    db.delete(entry)
    db.commit()

    return MessageResponse(message="Entrada eliminada")
