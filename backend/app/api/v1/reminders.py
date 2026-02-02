"""
Reminders CRUD endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user, require_permission
from app.models import Reminder, User
from app.schemas import (
    ReminderCreate, ReminderUpdate, ReminderResponse, ReminderList, MessageResponse
)

router = APIRouter(prefix="/reminders", tags=["Recordatorios"])


@router.get("", response_model=ReminderList)
async def list_reminders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    pending_only: bool = Query(True, description="Solo pendientes"),
    priority: Optional[str] = Query(None, description="low, normal, high"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reminders.read"))
):
    """Listar recordatorios."""
    query = db.query(Reminder).filter(Reminder.company_id == current_user.company_id)

    if pending_only:
        query = query.filter(Reminder.is_completed == False)

    if priority:
        query = query.filter(Reminder.priority == priority)

    total = query.count()
    reminders = query.order_by(Reminder.due_date.asc().nullslast()).offset(skip).limit(limit).all()

    return ReminderList(
        items=[ReminderResponse.model_validate(r) for r in reminders],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    data: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reminders.create"))
):
    """Crear recordatorio."""
    reminder = Reminder(
        company_id=current_user.company_id,
        created_by=current_user.id,
        **data.model_dump()
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    return ReminderResponse.model_validate(reminder)


@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(
    reminder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reminders.read"))
):
    """Obtener recordatorio."""
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.company_id == current_user.company_id
    ).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")

    return ReminderResponse.model_validate(reminder)


@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: UUID,
    data: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reminders.update"))
):
    """Actualizar recordatorio."""
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.company_id == current_user.company_id
    ).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reminder, field, value)

    db.commit()
    db.refresh(reminder)

    return ReminderResponse.model_validate(reminder)


@router.post("/{reminder_id}/complete", response_model=ReminderResponse)
async def complete_reminder(
    reminder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reminders.update"))
):
    """Marcar recordatorio como completado."""
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.company_id == current_user.company_id
    ).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")

    reminder.is_completed = True
    db.commit()
    db.refresh(reminder)

    return ReminderResponse.model_validate(reminder)


@router.delete("/{reminder_id}", response_model=MessageResponse)
async def delete_reminder(
    reminder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reminders.delete"))
):
    """Eliminar recordatorio."""
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.company_id == current_user.company_id
    ).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")

    db.delete(reminder)
    db.commit()

    return MessageResponse(message="Recordatorio eliminado")
