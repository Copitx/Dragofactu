"""
Endpoints para el libro de gastos / dietario financiero (CompanyExpense).
"""
from datetime import date
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.models.company_expense import CompanyExpense
from app.models.project import Project
from app.models.user import User
from app.schemas.company_expense import (
    CompanyExpenseCreate,
    CompanyExpenseUpdate,
    CompanyExpenseResponse,
    CompanyExpenseListResponse,
    ExpenseMonthlySummary,
    MarkExpensePaidRequest,
    SupplierSuggestion,
)

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _to_response(expense: CompanyExpense) -> CompanyExpenseResponse:
    project_name = expense.project.name if expense.project else None
    data = {
        "id": str(expense.id),
        "company_id": str(expense.company_id),
        "expense_date": expense.expense_date,
        "supplier": expense.supplier,
        "concept": expense.concept,
        "invoice_ref": expense.invoice_ref,
        "net_amount": expense.net_amount,
        "vat_rate": expense.vat_rate,
        "vat_amount": expense.vat_amount,
        "total_amount": expense.total_amount,
        "category": expense.category,
        "status": expense.status,
        "payment_method": expense.payment_method,
        "payment_date": expense.payment_date,
        "paid_by": expense.paid_by,
        "project_id": str(expense.project_id) if expense.project_id else None,
        "project_name": project_name,
        "notes": expense.notes,
        "user_id": str(expense.user_id),
        "created_at": expense.created_at,
        "updated_at": expense.updated_at,
    }
    return CompanyExpenseResponse(**data)


@router.get("", response_model=CompanyExpenseListResponse)
def list_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    supplier: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("diary.read")),
):
    q = (
        db.query(CompanyExpense)
        .filter(CompanyExpense.company_id == current_user.company_id)
    )

    if status:
        q = q.filter(CompanyExpense.status == status)
    if category:
        q = q.filter(CompanyExpense.category == category)
    if project_id:
        q = q.filter(CompanyExpense.project_id == project_id)
    if date_from:
        q = q.filter(CompanyExpense.expense_date >= date_from)
    if date_to:
        q = q.filter(CompanyExpense.expense_date <= date_to)
    if supplier:
        q = q.filter(CompanyExpense.supplier.ilike(f"%{supplier}%"))
    if search:
        term = f"%{search}%"
        q = q.filter(
            CompanyExpense.supplier.ilike(term)
            | CompanyExpense.concept.ilike(term)
            | CompanyExpense.invoice_ref.ilike(term)
        )
    if year:
        q = q.filter(func.extract("year", CompanyExpense.expense_date) == year)
    if month:
        q = q.filter(func.extract("month", CompanyExpense.expense_date) == month)

    total = q.count()
    items = (
        q.order_by(CompanyExpense.expense_date.desc(), CompanyExpense.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return CompanyExpenseListResponse(
        items=[_to_response(e) for e in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=CompanyExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    body: CompanyExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("diary.write")),
):
    expense = CompanyExpense(
        id=uuid4().hex,
        company_id=current_user.company_id,
        user_id=current_user.id,
        **body.model_dump(exclude_none=False),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return _to_response(expense)


@router.get("/suppliers/suggestions", response_model=list[SupplierSuggestion])
def supplier_suggestions(
    q: str = Query("", min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("diary.read")),
):
    """Autocomplete for supplier names based on previous entries."""
    from sqlalchemy import func as sqlfunc, distinct
    rows = (
        db.query(
            CompanyExpense.supplier,
            sqlfunc.max(CompanyExpense.expense_date).label("last_used"),
        )
        .filter(
            CompanyExpense.company_id == current_user.company_id,
            CompanyExpense.supplier.ilike(f"%{q}%"),
        )
        .group_by(CompanyExpense.supplier)
        .order_by(sqlfunc.max(CompanyExpense.expense_date).desc())
        .limit(10)
        .all()
    )
    return [SupplierSuggestion(name=r.supplier, last_used=r.last_used) for r in rows]


@router.get("/summary/monthly", response_model=ExpenseMonthlySummary)
def monthly_summary(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("diary.read")),
):
    from sqlalchemy import func as sqlfunc

    expenses = (
        db.query(CompanyExpense)
        .filter(
            CompanyExpense.company_id == current_user.company_id,
            sqlfunc.extract("year", CompanyExpense.expense_date) == year,
            sqlfunc.extract("month", CompanyExpense.expense_date) == month,
        )
        .all()
    )

    total = sum(e.total_amount for e in expenses)
    pending = sum(e.total_amount for e in expenses if e.status == "pending")
    paid = sum(e.total_amount for e in expenses if e.status == "paid")
    partial = sum(e.total_amount for e in expenses if e.status == "partial")

    by_cat: dict[str, float] = {}
    for e in expenses:
        cat = e.category or "other"
        by_cat[cat] = by_cat.get(cat, 0.0) + e.total_amount

    return ExpenseMonthlySummary(
        year=year,
        month=month,
        total_amount=round(total, 2),
        pending_amount=round(pending, 2),
        paid_amount=round(paid, 2),
        partial_amount=round(partial, 2),
        by_category={k: round(v, 2) for k, v in by_cat.items()},
        expense_count=len(expenses),
        pending_count=sum(1 for e in expenses if e.status == "pending"),
        paid_count=sum(1 for e in expenses if e.status == "paid"),
    )


@router.get("/{expense_id}", response_model=CompanyExpenseResponse)
def get_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("diary.read")),
):
    expense = (
        db.query(CompanyExpense)
        .filter(
            CompanyExpense.id == expense_id,
            CompanyExpense.company_id == current_user.company_id,
        )
        .first()
    )
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return _to_response(expense)


@router.put("/{expense_id}", response_model=CompanyExpenseResponse)
def update_expense(
    expense_id: str,
    body: CompanyExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("diary.write")),
):
    expense = (
        db.query(CompanyExpense)
        .filter(
            CompanyExpense.id == expense_id,
            CompanyExpense.company_id == current_user.company_id,
        )
        .first()
    )
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    return _to_response(expense)


@router.post("/{expense_id}/mark-paid", response_model=CompanyExpenseResponse)
def mark_expense_paid(
    expense_id: str,
    body: MarkExpensePaidRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("diary.write")),
):
    expense = (
        db.query(CompanyExpense)
        .filter(
            CompanyExpense.id == expense_id,
            CompanyExpense.company_id == current_user.company_id,
        )
        .first()
    )
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    expense.status = "paid"
    if body.payment_method:
        expense.payment_method = body.payment_method
    if body.payment_date:
        expense.payment_date = body.payment_date
    if body.paid_by:
        expense.paid_by = body.paid_by

    db.commit()
    db.refresh(expense)
    return _to_response(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("diary.write")),
):
    expense = (
        db.query(CompanyExpense)
        .filter(
            CompanyExpense.id == expense_id,
            CompanyExpense.company_id == current_user.company_id,
        )
        .first()
    )
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(expense)
    db.commit()
