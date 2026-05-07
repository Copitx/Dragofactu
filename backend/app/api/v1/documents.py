"""
Documents CRUD endpoints with business logic.
Handles quotes, delivery notes, and invoices.
"""
import logging
from typing import Optional, List
from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from uuid import UUID

from app.api.deps import get_db, get_current_user, require_permission
from app.models import (
    Document, DocumentLine, DocumentType, DocumentStatus,
    STATUS_TRANSITIONS, Client, Product, User
)
from app.schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentSummary,
    DocumentList, DocumentLineCreate, StatusChange, MessageResponse
)

router = APIRouter(prefix="/documents", tags=["Documentos"])
logger = logging.getLogger(__name__)


# Code prefixes by document type
CODE_PREFIXES = {
    DocumentType.QUOTE: "PRE",
    DocumentType.DELIVERY_NOTE: "ALB",
    DocumentType.INVOICE: "FAC"
}


def _mask_email(value: str) -> str:
    """Return a minimally identifiable representation of an email."""
    if "@" not in value:
        return "[redacted]"
    local, domain = value.split("@", 1)
    if not local:
        return f"***@{domain}"
    if len(local) == 1:
        return f"{local}***@{domain}"
    return f"{local[0]}***{local[-1]}@{domain}"


def generate_document_code(db: Session, company_id: UUID, doc_type: DocumentType) -> str:
    """Generate next document code for the company."""
    prefix = CODE_PREFIXES[doc_type]
    year = datetime.now().year

    # Find max code for this type and year
    pattern = f"{prefix}-{year}-%"
    max_code = db.query(func.max(Document.code)).filter(
        Document.company_id == company_id,
        Document.type == doc_type,
        Document.code.like(pattern)
    ).scalar()

    if max_code:
        # Extract number and increment
        try:
            num = int(max_code.split("-")[-1])
            next_num = num + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1

    return f"{prefix}-{year}-{next_num:05d}"


def calculate_line_subtotal(line: DocumentLine) -> float:
    """Calculate line subtotal with discount."""
    base = float(line.quantity) * float(line.unit_price)
    discount = base * (float(line.discount_percent) / 100)
    return round(base - discount, 2)


def calculate_document_totals(document: Document, tax_rate: float = 21.0):
    """Recalculate document totals from lines."""
    subtotal = sum(calculate_line_subtotal(line) for line in document.lines)
    tax_amount = round(subtotal * (tax_rate / 100), 2)
    total = round(subtotal + tax_amount, 2)

    document.subtotal = subtotal
    document.tax_amount = tax_amount
    document.total = total


@router.get("", response_model=DocumentList)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    doc_type: Optional[str] = Query(None, description="quote, delivery_note, invoice"),
    doc_status: Optional[str] = Query(None, description="draft, sent, paid, etc."),
    client_id: Optional[UUID] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.read"))
):
    """Listar documentos con filtros."""
    query = db.query(Document).options(
        joinedload(Document.client)
    ).filter(Document.company_id == current_user.company_id)

    if doc_type:
        try:
            query = query.filter(Document.type == DocumentType(doc_type))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Tipo invalido: {doc_type}")

    if doc_status:
        # Special case: "pending" returns all pending statuses
        if doc_status == "pending":
            pending_statuses = [
                DocumentStatus.DRAFT, DocumentStatus.NOT_SENT, DocumentStatus.SENT,
                DocumentStatus.ACCEPTED, DocumentStatus.PARTIALLY_PAID
            ]
            query = query.filter(Document.status.in_(pending_statuses))
        else:
            try:
                query = query.filter(Document.status == DocumentStatus(doc_status))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Estado invalido: {doc_status}")

    if client_id:
        query = query.filter(Document.client_id == client_id)

    if date_from:
        query = query.filter(Document.issue_date >= date_from)

    if date_to:
        query = query.filter(Document.issue_date <= date_to)

    total = query.count()
    documents = query.order_by(Document.issue_date.desc()).offset(skip).limit(limit).all()

    # Build response with client_name
    items = []
    for doc in documents:
        item = DocumentSummary(
            id=doc.id,
            code=doc.code,
            type=doc.type.value,
            status=doc.status.value,
            issue_date=doc.issue_date,
            due_date=doc.due_date,
            client_id=doc.client_id,
            client_name=doc.client.name if doc.client else None,
            total=float(doc.total or 0),
            created_at=doc.created_at
        )
        items.append(item)

    return DocumentList(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.create"))
):
    """Crear documento con líneas."""
    # Validate client
    client = db.query(Client).filter(
        Client.id == data.client_id,
        Client.company_id == current_user.company_id,
        Client.is_active == True
    ).first()

    if not client:
        raise HTTPException(status_code=400, detail="Cliente no encontrado o inactivo")

    # Parse document type
    try:
        doc_type = DocumentType(data.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Tipo invalido: {data.type}")

    # Generate code
    code = generate_document_code(db, current_user.company_id, doc_type)

    # Create document
    document = Document(
        company_id=current_user.company_id,
        code=code,
        type=doc_type,
        status=DocumentStatus.DRAFT,
        client_id=data.client_id,
        issue_date=data.issue_date,
        due_date=data.due_date,
        notes=data.notes,
        internal_notes=data.internal_notes,
        terms=data.terms,
        created_by=current_user.id
    )
    db.add(document)
    db.flush()

    # Add lines
    for idx, line_data in enumerate(data.lines):
        # Validate product if provided
        if line_data.product_id:
            product = db.query(Product).filter(
                Product.id == line_data.product_id,
                Product.company_id == current_user.company_id
            ).first()
            if not product:
                raise HTTPException(status_code=400, detail=f"Producto no encontrado: {line_data.product_id}")

        line = DocumentLine(
            document_id=document.id,
            line_type=line_data.line_type,
            product_id=line_data.product_id,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            discount_percent=line_data.discount_percent,
            order_index=idx
        )
        line.subtotal = calculate_line_subtotal(line)
        db.add(line)

    db.flush()
    calculate_document_totals(document)

    # Deduct stock for invoices on creation
    if doc_type == DocumentType.INVOICE:
        for line_data in data.lines:
            if line_data.product_id:
                product = db.query(Product).filter(
                    Product.id == line_data.product_id,
                    Product.company_id == current_user.company_id
                ).first()
                if product:
                    product.current_stock = (product.current_stock or 0) - line_data.quantity

    db.commit()
    db.refresh(document)

    return DocumentResponse.model_validate(document)


@router.get("/email/status")
async def get_email_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.read")),
):
    """Check if email sending is configured."""
    from app.core.email import is_smtp_configured
    from app.models import Company

    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    return {"configured": is_smtp_configured(company=company)}


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.read"))
):
    """Obtener documento con líneas."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.company_id == current_user.company_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    return DocumentResponse.model_validate(document)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.update"))
):
    """Actualizar documento. Solo en estado DRAFT."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.company_id == current_user.company_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if document.status != DocumentStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden editar documentos en borrador"
        )

    # Update basic fields
    if data.client_id:
        client = db.query(Client).filter(
            Client.id == data.client_id,
            Client.company_id == current_user.company_id
        ).first()
        if not client:
            raise HTTPException(status_code=400, detail="Cliente no encontrado")
        document.client_id = data.client_id

    if data.due_date is not None:
        document.due_date = data.due_date
    if data.notes is not None:
        document.notes = data.notes
    if data.internal_notes is not None:
        document.internal_notes = data.internal_notes
    if data.terms is not None:
        document.terms = data.terms

    # Update lines if provided
    if data.lines is not None:
        # Delete existing lines
        db.query(DocumentLine).filter(DocumentLine.document_id == document.id).delete()

        # Add new lines
        for idx, line_data in enumerate(data.lines):
            if line_data.product_id:
                product = db.query(Product).filter(
                    Product.id == line_data.product_id,
                    Product.company_id == current_user.company_id
                ).first()
                if not product:
                    raise HTTPException(status_code=400, detail=f"Producto no encontrado")

            line = DocumentLine(
                document_id=document.id,
                line_type=line_data.line_type,
                product_id=line_data.product_id,
                description=line_data.description,
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                discount_percent=line_data.discount_percent,
                order_index=idx
            )
            line.subtotal = calculate_line_subtotal(line)
            db.add(line)

        db.flush()
        calculate_document_totals(document)

    db.commit()
    db.refresh(document)

    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", response_model=MessageResponse)
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.delete"))
):
    """Eliminar documento. Solo en estado DRAFT."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.company_id == current_user.company_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if document.status != DocumentStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden eliminar documentos en borrador"
        )

    db.delete(document)
    db.commit()

    return MessageResponse(message=f"Documento {document.code} eliminado")


@router.post("/{document_id}/change-status", response_model=DocumentResponse)
async def change_document_status(
    document_id: UUID,
    data: StatusChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.update"))
):
    """Cambiar estado del documento con validación de transiciones."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.company_id == current_user.company_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    try:
        new_status = DocumentStatus(data.new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Estado invalido: {data.new_status}")

    # Validate transition
    allowed = STATUS_TRANSITIONS.get(document.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Transicion no permitida de {document.status.value} a {new_status.value}"
        )

    # Stock is now deducted at invoice creation time, not on status change

    document.status = new_status
    db.commit()
    db.refresh(document)

    return DocumentResponse.model_validate(document)


@router.post("/{document_id}/convert", response_model=DocumentResponse)
async def convert_document(
    document_id: UUID,
    target_type: str = Query(..., description="delivery_note o invoice"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.create"))
):
    """Convertir presupuesto a albarán o factura."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.company_id == current_user.company_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Validate source type
    if document.type != DocumentType.QUOTE:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden convertir presupuestos"
        )

    # Validate source status
    if document.status not in [DocumentStatus.ACCEPTED, DocumentStatus.SENT]:
        raise HTTPException(
            status_code=400,
            detail="El presupuesto debe estar enviado o aceptado para convertir"
        )

    # Parse target type
    try:
        new_type = DocumentType(target_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Tipo invalido: {target_type}")

    if new_type == DocumentType.QUOTE:
        raise HTTPException(status_code=400, detail="No se puede convertir a presupuesto")

    # Generate new code
    new_code = generate_document_code(db, current_user.company_id, new_type)

    # Create new document
    new_document = Document(
        company_id=current_user.company_id,
        code=new_code,
        type=new_type,
        status=DocumentStatus.DRAFT,
        client_id=document.client_id,
        issue_date=datetime.now(timezone.utc),
        due_date=document.due_date,
        parent_document_id=document.id,
        notes=document.notes,
        terms=document.terms,
        created_by=current_user.id
    )
    db.add(new_document)
    db.flush()

    # Copy lines
    for line in document.lines:
        new_line = DocumentLine(
            document_id=new_document.id,
            line_type=line.line_type,
            product_id=line.product_id,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            discount_percent=line.discount_percent,
            subtotal=line.subtotal,
            order_index=line.order_index
        )
        db.add(new_line)

    db.flush()
    calculate_document_totals(new_document)
    db.commit()
    db.refresh(new_document)

    return DocumentResponse.model_validate(new_document)


@router.get("/stats/summary")
async def get_documents_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.read"))
):
    """Obtener resumen de documentos para dashboard."""
    base_query = db.query(Document).filter(Document.company_id == current_user.company_id)

    # Pending documents (not paid/cancelled)
    pending_statuses = [
        DocumentStatus.DRAFT, DocumentStatus.NOT_SENT, DocumentStatus.SENT,
        DocumentStatus.ACCEPTED, DocumentStatus.PARTIALLY_PAID
    ]

    pending_count = base_query.filter(Document.status.in_(pending_statuses)).count()
    pending_total = db.query(func.sum(Document.total)).filter(
        Document.company_id == current_user.company_id,
        Document.status.in_(pending_statuses)
    ).scalar() or 0

    # This month invoices
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    month_invoices = base_query.filter(
        Document.type == DocumentType.INVOICE,
        Document.issue_date >= month_start
    ).count()
    month_total = db.query(func.sum(Document.total)).filter(
        Document.company_id == current_user.company_id,
        Document.type == DocumentType.INVOICE,
        Document.issue_date >= month_start
    ).scalar() or 0

    return {
        "pending_documents": pending_count,
        "pending_total": float(pending_total),
        "month_invoices": month_invoices,
        "month_total": float(month_total)
    }


@router.get("/{document_id}/pdf")
async def generate_document_pdf(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.read"))
):
    """Generate PDF for document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.company_id == current_user.company_id
    ).options(
        joinedload(Document.client),
        joinedload(Document.lines).joinedload(DocumentLine.product)
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    from app.core.pdf import InvoicePDFGenerator
    from app.models import Company
    from fastapi.responses import Response
    import io

    # Fetch company data for PDF header/footer
    company = db.query(Company).filter(Company.id == current_user.company_id).first()

    # Generate PDF in memory
    generator = InvoicePDFGenerator()
    pdf_buffer = io.BytesIO()

    # Generate PDF content
    generator.generate_pdf(document, pdf_buffer, company=company)
    pdf_buffer.seek(0)

    # Return PDF as response
    pdf_content = pdf_buffer.getvalue()
    filename = f"{document.code}.pdf"

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


@router.post("/{document_id}/send-email")
async def send_document_email(
    document_id: UUID,
    recipient_email: str = Query(..., description="Email address to send to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.read")),
):
    """Send a document as PDF via email."""
    from app.core.email import (
        is_smtp_configured,
        get_company_smtp_config,
        send_document_email as send_email,
        build_document_email_content,
    )
    from app.core.pdf import InvoicePDFGenerator
    from app.models import Company, AuditLog
    import io

    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    company_smtp = get_company_smtp_config(company)

    if not is_smtp_configured(company=company):
        raise HTTPException(
            status_code=400,
            detail="Email not configured. Configure SMTP in company settings."
        )

    # Fetch document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.company_id == current_user.company_id
    ).options(
        joinedload(Document.client),
        joinedload(Document.lines).joinedload(DocumentLine.product)
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Company already loaded above for PDF and email config
    company_name = company.name if company else "Dragofactu"

    # Generate PDF
    generator = InvoicePDFGenerator()
    pdf_buffer = io.BytesIO()
    generator.generate_pdf(document, pdf_buffer, company=company)
    pdf_buffer.seek(0)
    pdf_bytes = pdf_buffer.getvalue()

    # Build email
    doc_type = document.type.value if document.type else "document"
    subject, html_body = build_document_email_content(
        company_name=company_name,
        doc_type=doc_type,
        doc_code=document.code,
        subject_template=getattr(company, "email_subject_template", None),
        body_template=getattr(company, "email_body_template", None),
    )

    # Send
    try:
        send_email(
            recipient_email=recipient_email,
            subject=subject,
            body_html=html_body,
            pdf_bytes=pdf_bytes,
            pdf_filename=f"{document.code}.pdf",
            smtp_config=company_smtp,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

    # Audit log should not fail the main operation once email is delivered.
    try:
        masked_recipient = _mask_email(recipient_email)
        audit = AuditLog(
            company_id=current_user.company_id,
            user_id=current_user.id,
            action="email_sent",
            entity_type="document",
            entity_id=document_id.hex,
            details=f"Email sent to {masked_recipient}",
        )
        db.add(audit)
        db.commit()
    except Exception as audit_error:
        db.rollback()
        logger.warning("Email delivered but audit log failed for document %s: %s", document_id, audit_error)

    return {"message": f"Email sent to {_mask_email(recipient_email)}", "success": True}


# ---------------------------------------------------------------------------
# Group invoice: combine multiple delivery notes into a single invoice
# ---------------------------------------------------------------------------

class GroupInvoiceRequest(BaseModel):
    delivery_note_ids: List[UUID]
    client_id: UUID


@router.post("/group-invoice", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_group_invoice(
    data: GroupInvoiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.create"))
):
    """
    Create an INVOICE by grouping all lines from the given delivery notes.
    The delivery notes must belong to the same client and company.
    """
    if not data.delivery_note_ids:
        raise HTTPException(status_code=400, detail="Se requiere al menos un albarán")

    # Validate client
    client = db.query(Client).filter(
        Client.id == data.client_id,
        Client.company_id == current_user.company_id,
        Client.is_active == True
    ).first()
    if not client:
        raise HTTPException(status_code=400, detail="Cliente no encontrado")

    # Load delivery notes and validate
    delivery_notes = db.query(Document).filter(
        Document.id.in_(data.delivery_note_ids),
        Document.company_id == current_user.company_id,
        Document.type == DocumentType.DELIVERY_NOTE,
    ).all()

    if len(delivery_notes) != len(data.delivery_note_ids):
        raise HTTPException(status_code=400, detail="Algunos albaranes no se encontraron o no son válidos")

    for dn in delivery_notes:
        if str(dn.client_id) != str(data.client_id):
            raise HTTPException(
                status_code=400,
                detail=f"El albarán {dn.code} no pertenece al cliente seleccionado"
            )

    # Collect all lines from the delivery notes (with eager load)
    all_lines = []
    for dn in delivery_notes:
        dn_with_lines = db.query(Document).options(
            joinedload(Document.lines)
        ).filter(Document.id == dn.id).first()
        if dn_with_lines:
            all_lines.extend(dn_with_lines.lines)

    if not all_lines:
        raise HTTPException(status_code=400, detail="Los albaranes seleccionados no tienen líneas")

    # Generate invoice code
    code = generate_document_code(db, current_user.company_id, DocumentType.INVOICE)

    invoice = Document(
        company_id=current_user.company_id,
        code=code,
        type=DocumentType.INVOICE,
        status=DocumentStatus.DRAFT,
        client_id=data.client_id,
        issue_date=datetime.now(timezone.utc),
        created_by=current_user.id,
        notes=f"Factura agrupada de {len(delivery_notes)} albarán/es: " +
              ", ".join(dn.code for dn in delivery_notes if dn.code),
    )
    db.add(invoice)
    db.flush()

    for idx, src_line in enumerate(all_lines):
        new_line = DocumentLine(
            document_id=invoice.id,
            line_type=src_line.line_type,
            product_id=src_line.product_id,
            description=src_line.description,
            quantity=src_line.quantity,
            unit_price=src_line.unit_price,
            discount_percent=src_line.discount_percent,
            order_index=idx,
        )
        new_line.subtotal = calculate_line_subtotal(new_line)
        db.add(new_line)

    db.flush()
    calculate_document_totals(invoice)
    db.commit()
    db.refresh(invoice)

    logger.info(
        f"Group invoice {invoice.code} created from {len(delivery_notes)} delivery notes "
        f"for company {current_user.company_id}"
    )
    return DocumentResponse.model_validate(invoice)


# ---------------------------------------------------------------------------
# Quick mark as paid
# ---------------------------------------------------------------------------

class QuickPaidRequest(BaseModel):
    payment_date: Optional[date] = None


@router.post("/{document_id}/mark-paid", response_model=DocumentResponse)
async def mark_document_paid(
    document_id: UUID,
    data: QuickPaidRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.create"))
):
    """
    Quickly mark a document as PAID with an optional payment_date.
    Allowed from SENT or ACCEPTED status.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.company_id == current_user.company_id,
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if document.status not in (DocumentStatus.SENT, DocumentStatus.ACCEPTED):
        raise HTTPException(
            status_code=400,
            detail=f"Solo se puede marcar como pagado desde estado SENT o ACCEPTED (actual: {document.status})"
        )

    document.status = DocumentStatus.PAID
    if data.payment_date:
        document.payment_date = datetime.combine(data.payment_date, datetime.min.time())

    db.commit()
    db.refresh(document)
    logger.info(f"Document {document.code} marked as PAID for company {current_user.company_id}")
    return DocumentResponse.model_validate(document)
