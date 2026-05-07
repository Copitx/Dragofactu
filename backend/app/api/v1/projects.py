"""
Projects (Obras) API endpoints.
Core workflow: track active projects, expenses, and linked documents.
"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from uuid import UUID

from app.api.deps import get_db, get_current_user, require_permission
from app.models import User, Document
from app.models.project import Project, ProjectExpense, ProjectDocument, ProjectStatus
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetail,
    ProjectList, ProjectSummaryKPIs,
    ProjectExpenseCreate, ProjectExpenseUpdate, ProjectExpenseResponse,
    ProjectDocumentResponse,
)

router = APIRouter(prefix="/projects", tags=["Obras"])


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

def _generate_project_code(db: Session, company_id) -> str:
    from datetime import datetime
    year = datetime.now().year
    count = db.query(Project).filter(
        Project.company_id == company_id,
    ).count() + 1
    return f"Obra-{year}-{count:03d}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _project_to_response(p: Project) -> ProjectResponse:
    total_expenses = sum(e.amount or 0 for e in p.expenses) if p.expenses is not None else 0.0
    total_invoiced = sum(
        pd.document.total or 0
        for pd in (p.project_documents or [])
        if pd.document and pd.document.type.value == "invoice"
    )
    return ProjectResponse(
        id=p.id,
        company_id=p.company_id,
        code=p.code,
        name=p.name,
        client_id=p.client_id,
        client_name=p.client.name if p.client else None,
        address=p.address,
        status=p.status.value if hasattr(p.status, 'value') else p.status,
        start_date=p.start_date,
        end_date=p.end_date,
        estimated_value=p.estimated_value or 0.0,
        notes=p.notes,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at,
        total_expenses=total_expenses,
        total_invoiced=total_invoiced,
    )


def _expense_to_response(e: ProjectExpense) -> ProjectExpenseResponse:
    return ProjectExpenseResponse(
        id=e.id,
        project_id=e.project_id,
        company_id=e.company_id,
        date=e.date,
        description=e.description,
        supplier=e.supplier,
        document_ref=e.document_ref,
        amount=e.amount or 0.0,
        category=e.category.value if hasattr(e.category, 'value') else e.category,
        worker_id=e.worker_id,
        notes=e.notes,
        created_at=e.created_at,
        worker_name=f"{e.worker.first_name} {e.worker.last_name}" if e.worker else None,
    )


def _doc_link_to_response(pd: ProjectDocument) -> ProjectDocumentResponse:
    doc = pd.document
    return ProjectDocumentResponse(
        id=pd.id,
        project_id=pd.project_id,
        document_id=pd.document_id,
        company_id=pd.company_id,
        linked_at=pd.linked_at,
        doc_code=doc.code if doc else None,
        doc_type=doc.type.value if doc and hasattr(doc.type, 'value') else None,
        doc_status=doc.status.value if doc and hasattr(doc.status, 'value') else None,
        doc_total=doc.total if doc else None,
    )


def _get_project_or_404(db: Session, project_id: UUID, company_id) -> Project:
    project = db.query(Project).options(
        joinedload(Project.client),
        joinedload(Project.expenses).joinedload(ProjectExpense.worker),
        joinedload(Project.project_documents).joinedload(ProjectDocument.document),
    ).filter(
        Project.id == project_id,
        Project.company_id == company_id,
        Project.is_active == True,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Obra no encontrada")
    return project


# ---------------------------------------------------------------------------
# Projects CRUD
# ---------------------------------------------------------------------------

@router.get("", response_model=ProjectList)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    client_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.read")),
):
    """List projects with optional filters."""
    query = db.query(Project).options(
        joinedload(Project.client),
        joinedload(Project.expenses),
        joinedload(Project.project_documents).joinedload(ProjectDocument.document),
    ).filter(
        Project.company_id == current_user.company_id,
        Project.is_active == True,
    )

    if status:
        query = query.filter(Project.status == status)
    if client_id:
        query = query.filter(Project.client_id == client_id)
    if search:
        term = f"%{search}%"
        query = query.filter(
            (Project.name.ilike(term)) |
            (Project.code.ilike(term)) |
            (Project.address.ilike(term))
        )

    total = query.count()
    projects = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()

    return ProjectList(
        items=[_project_to_response(p) for p in projects],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.write")),
):
    """Create a new project."""
    code = _generate_project_code(db, current_user.company_id)
    project = Project(
        company_id=current_user.company_id,
        code=code,
        created_by=current_user.id,
        **data.model_dump(),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    # Reload with relationships
    project = _get_project_or_404(db, project.id, current_user.company_id)
    return _project_to_response(project)


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.read")),
):
    """Get full project detail including expenses and linked documents."""
    project = _get_project_or_404(db, project_id, current_user.company_id)
    response = _project_to_response(project)

    return ProjectDetail(
        **response.model_dump(),
        expenses=[_expense_to_response(e) for e in project.expenses],
        documents=[_doc_link_to_response(pd) for pd in project.project_documents],
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.write")),
):
    """Update project fields."""
    project = _get_project_or_404(db, project_id, current_user.company_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    project = _get_project_or_404(db, project_id, current_user.company_id)
    return _project_to_response(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.write")),
):
    """Soft delete a project."""
    project = _get_project_or_404(db, project_id, current_user.company_id)
    project.is_active = False
    db.commit()


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------

@router.get("/{project_id}/expenses", response_model=List[ProjectExpenseResponse])
async def list_expenses(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.read")),
):
    project = _get_project_or_404(db, project_id, current_user.company_id)
    return [_expense_to_response(e) for e in sorted(project.expenses, key=lambda e: e.date, reverse=True)]


@router.post("/{project_id}/expenses", response_model=ProjectExpenseResponse, status_code=201)
async def add_expense(
    project_id: UUID,
    data: ProjectExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.write")),
):
    _get_project_or_404(db, project_id, current_user.company_id)
    expense = ProjectExpense(
        project_id=project_id,
        company_id=current_user.company_id,
        **data.model_dump(),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return _expense_to_response(expense)


@router.put("/{project_id}/expenses/{expense_id}", response_model=ProjectExpenseResponse)
async def update_expense(
    project_id: UUID,
    expense_id: UUID,
    data: ProjectExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.write")),
):
    expense = db.query(ProjectExpense).filter(
        ProjectExpense.id == expense_id,
        ProjectExpense.project_id == project_id,
        ProjectExpense.company_id == current_user.company_id,
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return _expense_to_response(expense)


@router.delete("/{project_id}/expenses/{expense_id}", status_code=204)
async def delete_expense(
    project_id: UUID,
    expense_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.write")),
):
    expense = db.query(ProjectExpense).filter(
        ProjectExpense.id == expense_id,
        ProjectExpense.project_id == project_id,
        ProjectExpense.company_id == current_user.company_id,
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    db.delete(expense)
    db.commit()


# ---------------------------------------------------------------------------
# Document links
# ---------------------------------------------------------------------------

@router.post("/{project_id}/documents/{document_id}", response_model=ProjectDocumentResponse, status_code=201)
async def link_document(
    project_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.write")),
):
    """Link an existing document to a project."""
    _get_project_or_404(db, project_id, current_user.company_id)

    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.company_id == current_user.company_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    existing = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.document_id == document_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="El documento ya está vinculado a esta obra")

    pd = ProjectDocument(
        project_id=project_id,
        document_id=document_id,
        company_id=current_user.company_id,
    )
    db.add(pd)
    db.commit()
    db.refresh(pd)
    pd.document = doc
    return _doc_link_to_response(pd)


@router.delete("/{project_id}/documents/{document_id}", status_code=204)
async def unlink_document(
    project_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.write")),
):
    pd = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.document_id == document_id,
        ProjectDocument.company_id == current_user.company_id,
    ).first()
    if not pd:
        raise HTTPException(status_code=404, detail="Vínculo no encontrado")
    db.delete(pd)
    db.commit()


# ---------------------------------------------------------------------------
# KPI summary
# ---------------------------------------------------------------------------

@router.get("/{project_id}/summary", response_model=ProjectSummaryKPIs)
async def get_project_summary(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.read")),
):
    """Financial summary: estimated vs spent vs invoiced → margin."""
    project = _get_project_or_404(db, project_id, current_user.company_id)

    total_expenses = sum(e.amount or 0 for e in project.expenses)
    total_invoiced = sum(
        pd.document.total or 0
        for pd in project.project_documents
        if pd.document and pd.document.type.value == "invoice"
    )
    estimated = project.estimated_value or 0.0
    margin = estimated - total_expenses
    margin_pct = (margin / estimated * 100) if estimated > 0 else None

    return ProjectSummaryKPIs(
        estimated_value=estimated,
        total_expenses=total_expenses,
        total_invoiced=total_invoiced,
        margin=margin,
        margin_pct=round(margin_pct, 1) if margin_pct is not None else None,
    )
