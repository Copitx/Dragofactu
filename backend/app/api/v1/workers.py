"""
Workers CRUD endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user, require_permission
from app.models import Worker, Course, User
from app.schemas import (
    WorkerCreate, WorkerUpdate, WorkerResponse, WorkerList,
    CourseCreate, CourseResponse, MessageResponse
)

router = APIRouter(prefix="/workers", tags=["Trabajadores"])


@router.get("", response_model=WorkerList)
async def list_workers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("workers.read"))
):
    """Listar trabajadores."""
    query = db.query(Worker).filter(Worker.company_id == current_user.company_id)

    if active_only:
        query = query.filter(Worker.is_active == True)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Worker.first_name.ilike(search_term)) |
            (Worker.last_name.ilike(search_term)) |
            (Worker.code.ilike(search_term))
        )

    if department:
        query = query.filter(Worker.department == department)

    total = query.count()
    workers = query.order_by(Worker.last_name).offset(skip).limit(limit).all()

    return WorkerList(
        items=[WorkerResponse.model_validate(w) for w in workers],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=WorkerResponse, status_code=status.HTTP_201_CREATED)
async def create_worker(
    data: WorkerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("workers.create"))
):
    """Crear trabajador."""
    existing = db.query(Worker).filter(
        Worker.company_id == current_user.company_id,
        Worker.code == data.code
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail=f"Ya existe un trabajador con codigo {data.code}")

    worker = Worker(
        company_id=current_user.company_id,
        **data.model_dump()
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)

    return WorkerResponse.model_validate(worker)


@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker(
    worker_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("workers.read"))
):
    """Obtener trabajador con sus cursos."""
    worker = db.query(Worker).filter(
        Worker.id == worker_id,
        Worker.company_id == current_user.company_id
    ).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")

    return WorkerResponse.model_validate(worker)


@router.put("/{worker_id}", response_model=WorkerResponse)
async def update_worker(
    worker_id: UUID,
    data: WorkerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("workers.update"))
):
    """Actualizar trabajador."""
    worker = db.query(Worker).filter(
        Worker.id == worker_id,
        Worker.company_id == current_user.company_id
    ).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(worker, field, value)

    db.commit()
    db.refresh(worker)

    return WorkerResponse.model_validate(worker)


@router.delete("/{worker_id}", response_model=MessageResponse)
async def delete_worker(
    worker_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("workers.delete"))
):
    """Eliminar trabajador (soft delete)."""
    worker = db.query(Worker).filter(
        Worker.id == worker_id,
        Worker.company_id == current_user.company_id
    ).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")

    worker.is_active = False
    db.commit()

    return MessageResponse(message=f"Trabajador {worker.code} eliminado")


# Courses endpoints
@router.post("/{worker_id}/courses", response_model=CourseResponse, status_code=201)
async def add_course(
    worker_id: UUID,
    data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("workers.update"))
):
    """Añadir curso a trabajador."""
    worker = db.query(Worker).filter(
        Worker.id == worker_id,
        Worker.company_id == current_user.company_id
    ).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")

    course = Course(worker_id=worker_id, **data.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)

    return CourseResponse.model_validate(course)


@router.delete("/{worker_id}/courses/{course_id}", response_model=MessageResponse)
async def delete_course(
    worker_id: UUID,
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("workers.update"))
):
    """Eliminar curso de trabajador."""
    course = db.query(Course).join(Worker).filter(
        Course.id == course_id,
        Course.worker_id == worker_id,
        Worker.company_id == current_user.company_id
    ).first()

    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    db.delete(course)
    db.commit()

    return MessageResponse(message="Curso eliminado")
