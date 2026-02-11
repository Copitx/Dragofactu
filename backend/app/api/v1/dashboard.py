"""
Dashboard statistics endpoint.
Returns aggregated stats for the desktop client dashboard.
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, require_permission
from app.models import User, Client, Product, Document, Supplier, Reminder
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

    # Supplier count
    supplier_count = db.query(Supplier).filter(
        Supplier.company_id == company_id,
        Supplier.is_active == True
    ).count()

    # Unpaid invoices (SENT or ACCEPTED)
    unpaid_statuses = [DocumentStatus.SENT, DocumentStatus.ACCEPTED]
    unpaid_invoices = db.query(Document).filter(
        Document.company_id == company_id,
        Document.type == DocumentType.INVOICE,
        Document.status.in_(unpaid_statuses)
    ).count()

    # Pending reminders count
    pending_reminders = db.query(Reminder).filter(
        Reminder.company_id == company_id,
        Reminder.is_completed == False
    ).count()

    # Recent pending documents (last 5)
    recent_pending = db.query(Document).filter(
        Document.company_id == company_id,
        Document.status.in_(pending_statuses)
    ).order_by(Document.issue_date.desc()).limit(5).all()

    recent_docs_list = []
    for doc in recent_pending:
        client_name = ""
        if doc.client_id:
            client = db.query(Client).filter(Client.id == doc.client_id).first()
            if client:
                client_name = client.name or ""
        recent_docs_list.append({
            "id": str(doc.id),
            "code": doc.code or "",
            "client_name": client_name,
            "total": float(doc.total or 0),
            "status": doc.status.value if doc.status else "",
            "type": doc.type.value if doc.type else "",
        })

    return {
        # Legacy keys (desktop client compatibility)
        "clients": client_count,
        "products": product_count,
        "low_stock": low_stock_count,
        "pending_documents": pending_docs_count,
        "total_documents": total_docs,
        "month_invoices": month_invoices,
        "month_total": float(month_total),
        "pending_total": float(pending_total),
        # Frontend-friendly keys
        "clients_count": client_count,
        "products_count": product_count,
        "low_stock_count": low_stock_count,
        "suppliers_count": supplier_count,
        "unpaid_invoices": unpaid_invoices,
        "pending_reminders": pending_reminders,
        "recent_pending_docs": recent_docs_list,
    }
