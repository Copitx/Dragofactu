"""
Dashboard statistics endpoint.
Returns aggregated stats for the desktop client dashboard.
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, require_permission
from app.models import User, Client, Product, Document
from app.models.document import DocumentStatus, DocumentType

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clients.read"))
):
    """
    Obtener estadisticas para el dashboard.
    Devuelve conteos agregados de clientes, productos, documentos, etc.
    """
    company_id = current_user.company_id

    # Client count
    client_count = db.query(Client).filter(
        Client.company_id == company_id,
        Client.is_active == True
    ).count()

    # Product count
    product_count = db.query(Product).filter(
        Product.company_id == company_id,
        Product.is_active == True
    ).count()

    # Low stock products
    low_stock_count = db.query(Product).filter(
        Product.company_id == company_id,
        Product.is_active == True,
        Product.current_stock <= Product.minimum_stock
    ).count()

    # Pending documents
    pending_statuses = [
        DocumentStatus.DRAFT, DocumentStatus.NOT_SENT, DocumentStatus.SENT,
        DocumentStatus.ACCEPTED, DocumentStatus.PARTIALLY_PAID
    ]
    pending_docs_count = db.query(Document).filter(
        Document.company_id == company_id,
        Document.status.in_(pending_statuses)
    ).count()

    # Total documents
    total_docs = db.query(Document).filter(
        Document.company_id == company_id
    ).count()

    # This month's invoices
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    month_invoices = db.query(Document).filter(
        Document.company_id == company_id,
        Document.type == DocumentType.INVOICE,
        Document.issue_date >= month_start
    ).count()

    month_total = db.query(func.sum(Document.total)).filter(
        Document.company_id == company_id,
        Document.type == DocumentType.INVOICE,
        Document.issue_date >= month_start
    ).scalar() or 0

    # Pending total
    pending_total = db.query(func.sum(Document.total)).filter(
        Document.company_id == company_id,
        Document.status.in_(pending_statuses)
    ).scalar() or 0

    return {
        "clients": client_count,
        "products": product_count,
        "low_stock": low_stock_count,
        "pending_documents": pending_docs_count,
        "total_documents": total_docs,
        "month_invoices": month_invoices,
        "month_total": float(month_total),
        "pending_total": float(pending_total)
    }
