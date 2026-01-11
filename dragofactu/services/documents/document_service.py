from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from dragofactu.models.entities import Document, DocumentLine, DocumentType, DocumentStatus, Client
from dragofactu.models.audit import DocumentHistory
from dragofactu.services.auth.auth_service import require_permission
import json


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
    
    def _generate_document_code(self, doc_type: DocumentType) -> str:
        """Generate unique document code based on type"""
        year = datetime.now().year
        prefix = {
            DocumentType.QUOTE: 'QT',
            DocumentType.DELIVERY_NOTE: 'DN', 
            DocumentType.INVOICE: 'INV'
        }[doc_type]
        
        # Count documents of this type this year
        count = self.db.query(Document).filter(
            Document.type == doc_type,
            Document.issue_date.between(
                datetime(year, 1, 1),
                datetime(year, 12, 31)
            )
        ).count()
        
        return f"{prefix}{year}{count + 1:04d}"
    
    def _create_history_record(self, document: Document, action: str, user_id: str,
                              field_name: str = None, old_value: str = None,
                              new_value: str = None, before_snapshot: str = None,
                              after_snapshot: str = None, description: str = None):
        """Create a document history record"""
        history = DocumentHistory(
            document_id=document.id,
            user_id=user_id,
            action=action,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            description=description
        )
        
        self.db.add(history)
    
    @require_permission('documents.create')
    def create_document(self, doc_type: DocumentType, client_id: str, user_id: str,
                       issue_date: datetime = None, due_date: datetime = None,
                       notes: str = None, internal_notes: str = None,
                       terms: str = None, tax_config: Dict[str, Any] = None) -> Document:
        
        # Get client
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError("Client not found")
        
        # Generate document code
        code = self._generate_document_code(doc_type)
        
        # Set default issue date if not provided
        if not issue_date:
            issue_date = datetime.utcnow()
        
        # Convert tax_config to JSON string if provided
        tax_config_json = json.dumps(tax_config) if tax_config else None
        
        document = Document(
            code=code,
            type=doc_type,
            client_id=client_id,
            issue_date=issue_date,
            due_date=due_date,
            notes=notes,
            internal_notes=internal_notes,
            terms=terms,
            tax_config=tax_config_json,
            created_by=user_id
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # Create history record
        self._create_history_record(
            document, "created", user_id,
            description=f"Document {code} created as {doc_type.value}"
        )
        self.db.commit()
        
        return document
    
    @require_permission('documents.read')
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    @require_permission('documents.read')
    def get_document_by_code(self, code: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.code == code).first()
    
    @require_permission('documents.read')
    def search_documents(self, query: str = None, doc_type: DocumentType = None,
                        client_id: str = None, status: DocumentStatus = None,
                        date_from: datetime = None, date_to: datetime = None,
                        created_by: str = None) -> List[Document]:
        
        db_query = self.db.query(Document)
        
        if query:
            db_query = db_query.filter(
                or_(
                    Document.code.ilike(f"%{query}%"),
                    Document.notes.ilike(f"%{query}%"),
                    Client.name.ilike(f"%{query}%")
                )
            )
        
        if doc_type:
            db_query = db_query.filter(Document.type == doc_type)
        
        if client_id:
            db_query = db_query.filter(Document.client_id == client_id)
        
        if status:
            db_query = db_query.filter(Document.status == status)
        
        if date_from:
            db_query = db_query.filter(Document.issue_date >= date_from)
        
        if date_to:
            db_query = db_query.filter(Document.issue_date <= date_to)
        
        if created_by:
            db_query = db_query.filter(Document.created_by == created_by)
        
        return db_query.order_by(Document.issue_date.desc()).all()
    
    @require_permission('documents.update')
    def update_document(self, document_id: str, user_id: str, **kwargs) -> Optional[Document]:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return None
        
        # Store old values for history
        old_values = {}
        new_values = {}
        
        # Update allowed fields
        allowed_fields = ['status', 'issue_date', 'due_date', 'notes', 
                         'internal_notes', 'terms', 'tax_config']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                old_value = getattr(document, field)
                if old_value != value:
                    old_values[field] = old_value
                    new_values[field] = value
                    
                    # Special handling for tax_config
                    if field == 'tax_config' and value is not None:
                        if isinstance(value, dict):
                            value = json.dumps(value)
                    elif field == 'tax_config' and value is None:
                        value = None
                    
                    setattr(document, field, value)
        
        if old_values:
            # Create history record for each changed field
            for field in old_values:
                self._create_history_record(
                    document, "updated", user_id, field,
                    str(old_values[field]) if old_values[field] else None,
                    str(new_values[field]) if new_values[field] else None,
                    description=f"Field {field} updated"
                )
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    @require_permission('documents.delete')
    def delete_document(self, document_id: str, user_id: str) -> bool:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False
        
        # Create history record before deletion
        self._create_history_record(
            document, "deleted", user_id,
            description=f"Document {document.code} deleted"
        )
        
        self.db.delete(document)
        self.db.commit()
        
        return True
    
    @require_permission('documents.update')
    def add_document_line(self, document_id: str, user_id: str, description: str,
                         quantity: Decimal = Decimal('1'), unit_price: Decimal = Decimal('0'),
                         discount_percent: Decimal = Decimal('0'), product_id: str = None,
                         line_type: str = "product", tax_config: Dict[str, Any] = None,
                         order_index: int = None) -> DocumentLine:
        
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")
        
        # Calculate subtotal
        subtotal = quantity * unit_price * (1 - discount_percent / Decimal('100'))
        
        # Determine order index if not provided
        if order_index is None:
            max_order = self.db.query(DocumentLine).filter(
                DocumentLine.document_id == document_id
            ).count()
            order_index = max_order
        
        # Convert tax_config to JSON if provided
        tax_config_json = json.dumps(tax_config) if tax_config else None
        
        line = DocumentLine(
            document_id=document_id,
            line_type=line_type,
            product_id=product_id,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            discount_percent=discount_percent,
            subtotal=subtotal,
            tax_config=tax_config_json,
            order_index=order_index
        )
        
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        
        # Update document totals
        self._recalculate_document_totals(document_id, user_id)
        
        # Create history record
        self._create_history_record(
            document, "line_added", user_id,
            description=f"Line added: {description[:50]}..."
        )
        self.db.commit()
        
        return line
    
    @require_permission('documents.update')
    def update_document_line(self, line_id: str, user_id: str, **kwargs) -> Optional[DocumentLine]:
        line = self.db.query(DocumentLine).filter(DocumentLine.id == line_id).first()
        if not line:
            return None
        
        document = self.db.query(Document).filter(Document.id == line.document_id).first()
        
        # Store old values for history
        old_values = {}
        
        # Update allowed fields
        allowed_fields = ['description', 'quantity', 'unit_price', 'discount_percent',
                         'line_type', 'tax_config', 'order_index']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                old_value = getattr(line, field)
                if old_value != value:
                    old_values[field] = old_value
                    
                    # Special handling for tax_config
                    if field == 'tax_config' and value is not None:
                        if isinstance(value, dict):
                            value = json.dumps(value)
                    elif field == 'tax_config' and value is None:
                        value = None
                    
                    setattr(line, field, value)
        
        # Recalculate subtotal if quantity, unit_price, or discount changed
        if any(field in ['quantity', 'unit_price', 'discount_percent'] for field in old_values):
            line.subtotal = line.quantity * line.unit_price * (1 - line.discount_percent / Decimal('100'))
        
        if old_values:
            # Create history record
            changes = ", ".join([f"{field}: {old_values[field]} -> {kwargs.get(field, '')}" 
                               for field in old_values])
            self._create_history_record(
                document, "line_updated", user_id,
                description=f"Line updated: {changes}"
            )
        
        self.db.commit()
        self.db.refresh(line)
        
        # Update document totals
        self._recalculate_document_totals(line.document_id, user_id)
        
        return line
    
    @require_permission('documents.update')
    def delete_document_line(self, line_id: str, user_id: str) -> bool:
        line = self.db.query(DocumentLine).filter(DocumentLine.id == line_id).first()
        if not line:
            return False
        
        document = self.db.query(Document).filter(Document.id == line.document_id).first()
        document_id = line.document_id
        description = line.description
        
        # Create history record before deletion
        self._create_history_record(
            document, "line_deleted", user_id,
            description=f"Line deleted: {description[:50]}..."
        )
        
        self.db.delete(line)
        self.db.commit()
        
        # Update document totals
        self._recalculate_document_totals(document_id, user_id)
        
        return True
    
    def _recalculate_document_totals(self, document_id: str, user_id: str):
        """Recalculate document totals based on lines"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return
        
        lines = self.db.query(DocumentLine).filter(
            DocumentLine.document_id == document_id
        ).all()
        
        # Calculate subtotal
        subtotal = sum(line.subtotal or Decimal('0') for line in lines)
        
        # For now, simple tax calculation (can be enhanced later based on tax_config)
        tax_amount = subtotal * Decimal('0.21')  # Default 21% VAT
        total = subtotal + tax_amount
        
        # Update document totals
        old_subtotal = document.subtotal
        old_total = document.total
        
        document.subtotal = subtotal
        document.tax_amount = tax_amount
        document.total = total
        
        # Create history record if totals changed significantly
        if abs(float(old_total or 0) - float(total)) > 0.01:
            self._create_history_record(
                document, "totals_recalculated", user_id,
                description=f"Totals updated: {old_subtotal or 0} + {tax_amount} = {total}"
            )
        
        self.db.commit()
    
    @require_permission('documents.convert')
    def convert_document(self, source_document_id: str, target_type: DocumentType,
                        user_id: str, keep_original: bool = True) -> Document:
        """Convert a document to another type (e.g., Quote -> Invoice)"""
        
        source_document = self.db.query(Document).filter(
            Document.id == source_document_id
        ).first()
        
        if not source_document:
            raise ValueError("Source document not found")
        
        # Validate conversion
        if source_document.type == target_type:
            raise ValueError("Cannot convert document to same type")
        
        valid_conversions = {
            DocumentType.QUOTE: [DocumentType.DELIVERY_NOTE, DocumentType.INVOICE],
            DocumentType.DELIVERY_NOTE: [DocumentType.INVOICE],
            DocumentType.INVOICE: []  # Cannot convert from invoice
        }
        
        if target_type not in valid_conversions.get(source_document.type, []):
            raise ValueError(f"Cannot convert {source_document.type.value} to {target_type.value}")
        
        # Create new document with same data
        new_document = Document(
            code=self._generate_document_code(target_type),
            type=target_type,
            client_id=source_document.client_id,
            parent_document_id=source_document.id,
            issue_date=datetime.utcnow(),
            due_date=source_document.due_date,
            notes=source_document.notes,
            internal_notes=source_document.internal_notes,
            terms=source_document.terms,
            tax_config=source_document.tax_config,
            created_by=user_id
        )
        
        self.db.add(new_document)
        self.db.commit()
        self.db.refresh(new_document)
        
        # Copy all lines
        for line in source_document.lines:
            new_line = DocumentLine(
                document_id=new_document.id,
                line_type=line.line_type,
                product_id=line.product_id,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_percent=line.discount_percent,
                subtotal=line.subtotal,
                tax_config=line.tax_config,
                order_index=line.order_index
            )
            self.db.add(new_line)
        
        self.db.commit()
        
        # Calculate totals for new document
        self._recalculate_document_totals(new_document.id, user_id)
        
        # Create history records
        self._create_history_record(
            new_document, "created", user_id,
            description=f"Document converted from {source_document.type.value} ({source_document.code})"
        )
        
        self._create_history_record(
            source_document, "converted", user_id,
            description=f"Document converted to {target_type.value} ({new_document.code})"
        )
        
        self.db.commit()
        
        return new_document