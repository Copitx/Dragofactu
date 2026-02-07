"""
Financial reports endpoints.
Monthly, quarterly, and annual summaries.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func, extract

from app.api.deps import get_db, get_current_user
from app.models import Document, DocumentType, DocumentStatus, User
from app.schemas.report import PeriodReport, DocumentTypeSummary, AnnualReport

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Informes"])


def _get_period_report(db: Session, company_id, start: datetime, end: datetime) -> PeriodReport:
    """Generate a financial report for a specific period."""
    base_query = db.query(Document).filter(
        Document.company_id == company_id,
        Document.issue_date >= start,
        Document.issue_date < end,
    )

    # Totals by type
    by_type = []
    for doc_type in DocumentType:
        type_query = base_query.filter(Document.type == doc_type)
        count = type_query.count()
        total = type_query.with_entities(sa_func.coalesce(sa_func.sum(Document.total), 0)).scalar()
        by_type.append(DocumentTypeSummary(
            type=doc_type.value,
            count=count,
            total=float(total)
        ))

    # Invoiced = total of all invoices
    invoiced = base_query.filter(
        Document.type == DocumentType.INVOICE
    ).with_entities(
        sa_func.coalesce(sa_func.sum(Document.total), 0)
    ).scalar()

    # Paid = invoices with PAID status
    paid = base_query.filter(
        Document.type == DocumentType.INVOICE,
        Document.status == DocumentStatus.PAID
    ).with_entities(
        sa_func.coalesce(sa_func.sum(Document.total), 0)
    ).scalar()

    # Quotes total
    quotes = base_query.filter(
        Document.type == DocumentType.QUOTE
    ).with_entities(
        sa_func.coalesce(sa_func.sum(Document.total), 0)
    ).scalar()

    doc_count = base_query.count()

    return PeriodReport(
        period_start=start,
        period_end=end,
        total_invoiced=float(invoiced),
        total_quotes=float(quotes),
        total_paid=float(paid),
        total_pending=float(invoiced) - float(paid),
        document_count=doc_count,
        by_type=by_type
    )


@router.get("/monthly", response_model=PeriodReport)
async def monthly_report(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get financial report for a specific month."""
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    return _get_period_report(db, current_user.company_id, start, end)


@router.get("/quarterly", response_model=PeriodReport)
async def quarterly_report(
    year: int = Query(..., ge=2020, le=2100),
    quarter: int = Query(..., ge=1, le=4),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get financial report for a specific quarter (Q1=Jan-Mar, Q2=Apr-Jun, etc.)."""
    start_month = (quarter - 1) * 3 + 1
    end_month = start_month + 3

    start = datetime(year, start_month, 1, tzinfo=timezone.utc)
    if end_month > 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, end_month, 1, tzinfo=timezone.utc)

    return _get_period_report(db, current_user.company_id, start, end)


@router.get("/annual", response_model=AnnualReport)
async def annual_report(
    year: int = Query(..., ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get annual report with monthly breakdown."""
    months = []
    total_invoiced = 0.0
    total_paid = 0.0

    for month in range(1, 13):
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

        report = _get_period_report(db, current_user.company_id, start, end)
        months.append(report)
        total_invoiced += report.total_invoiced
        total_paid += report.total_paid

    return AnnualReport(
        year=year,
        total_invoiced=total_invoiced,
        total_paid=total_paid,
        total_pending=total_invoiced - total_paid,
        months=months
    )
