from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from dragofactu.config.translation import t

from dragofactu.models.database import SessionLocal
from dragofactu.services.business.entity_services import ClientService, SupplierService, ProductService
from dragofactu.services.documents.document_service import DocumentService


class DashboardView(QWidget):
    """Dashboard view with summary information"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        # Defer refresh to prevent blocking during initialization
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.refresh)
    
    def setup_ui(self):
        """Setup dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Dashboard")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Summary cards container
        cards_widget = QWidget()
        cards_layout = QGridLayout(cards_widget)
        
        # Create summary cards
        self.create_summary_cards(cards_layout)
        
        layout.addWidget(cards_widget)
        
        # Recent activity
        self.create_recent_activity_section(layout)
        
        # Add stretch at bottom
        layout.addStretch()
    
    def create_summary_cards(self, layout):
        """Create summary cards for key metrics"""
        # Define cards with their positions and data
        cards = [
            ("Total Clients", "0", "#0078d4", 0, 0),
            ("Total Suppliers", "0", "#107c10", 0, 1),
            ("Active Products", "0", "#d83b01", 0, 2),
            ("Pending Documents", "0", "#5c2d91", 1, 0),
            ("Low Stock Items", "0", "#e81123", 1, 1),
            ("Unpaid Invoices", "0", "#ff8c00", 1, 2),
        ]
        
        self.summary_labels = {}
        
        for title, value, color, row, col in cards:
            card = self.create_summary_card(title, value, color)
            layout.addWidget(card, row, col)
            
            # Store reference to value label for updates
            self.summary_labels[title] = card.findChild(QLabel, "value_label")
    
    def create_summary_card(self, title, value, color):
        """Create a single summary card"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 16px;
                min-height: 120px;
            }}
            QLabel {{
                background-color: transparent;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        
        # Title label
        title_label = QLabel(title)
        title_font = QFont("Arial", 10)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #666;")
        card_layout.addWidget(title_label)
        
        # Value label
        value_label = QLabel(value)
        value_label.setObjectName("value_label")
        value_font = QFont("Arial", 18, QFont.Weight.Bold)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color};")
        card_layout.addWidget(value_label)
        
        return card
    
    def create_recent_activity_section(self, layout):
        """Create recent activity section"""
        section_frame = QFrame()
        section_frame.setFrameStyle(QFrame.Box)
        section_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e1e1e1;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        section_layout = QVBoxLayout(section_frame)
        
        # Section title
        title_label = QLabel("Recent Activity")
        title_font = QFont("Arial", 12, QFont.Weight.Bold)
        title_label.setFont(title_font)
        section_layout.addWidget(title_label)
        
        # Activity content
        activity_widget = QWidget()
        self.activity_layout = QVBoxLayout(activity_widget)
        
        # Scroll area for activity
        scroll_area = QScrollArea()
        scroll_area.setWidget(activity_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        section_layout.addWidget(scroll_area)
        
        layout.addWidget(section_frame)
    
    def refresh(self):
        """Refresh dashboard data"""
        try:
            with SessionLocal() as db:
                # Get current user for permissions
                from dragofactu.models.entities import User
                current_user = db.query(User).filter(User.username == "admin").first()
                
                # Get summary data
                client_service = ClientService(db)
                supplier_service = SupplierService(db)
                product_service = ProductService(db)
                document_service = DocumentService(db)
                
                # Update summary counts (pass current_user for permission checks)
                client_count = len(client_service.search_clients(current_user, active_only=True))
                supplier_count = len(supplier_service.search_suppliers(current_user, active_only=True))
                product_count = len(product_service.search_products(current_user, active_only=True))
                low_stock_count = len(product_service.get_low_stock_products(current_user))
                
                # Get document statistics
                from dragofactu.models.entities import DocumentStatus
                pending_docs = len(document_service.search_documents(current_user, doc_type=None, client_id=None, status=DocumentStatus.DRAFT, date_from=None, date_to=None, created_by=None))
                
                # Update summary labels
                self.summary_labels["Total Clients"].setText(str(client_count))
                self.summary_labels["Total Suppliers"].setText(str(supplier_count))
                self.summary_labels["Active Products"].setText(str(product_count))
                self.summary_labels["Pending Documents"].setText(str(pending_docs))
                self.summary_labels["Low Stock Items"].setText(str(low_stock_count))
                # Count unpaid invoices (SENT or ACCEPTED status)
                from dragofactu.models.entities import Document, DocumentType
                unpaid_count = db.query(Document).filter(
                    Document.type == DocumentType.INVOICE,
                    Document.is_active == True,
                    Document.status.in_([
                        DocumentStatus.SENT,
                        DocumentStatus.ACCEPTED,
                        DocumentStatus.NOT_SENT,
                    ])
                ).count()
                self.summary_labels["Unpaid Invoices"].setText(str(unpaid_count))

                # Clear and update recent activity
                self.clear_activity_layout()
                self.update_recent_activity(db)
        
        except Exception as e:
            # Show error in activity section
            self.clear_activity_layout()
            error_label = QLabel(f"Error loading dashboard data: {str(e)}")
            error_label.setStyleSheet("color: red; padding: 8px;")
            self.activity_layout.addWidget(error_label)
    
    def clear_activity_layout(self):
        """Clear all widgets from activity layout"""
        while self.activity_layout.count():
            item = self.activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def update_recent_activity(self, db):
        """Update recent activity section with recent documents."""
        from dragofactu.models.entities import Document

        recent_docs = (
            db.query(Document)
            .filter(Document.is_active == True)
            .order_by(Document.created_at.desc())
            .limit(5)
            .all()
        )

        if not recent_docs:
            placeholder_label = QLabel("No recent activity")
            placeholder_label.setStyleSheet("color: #666; padding: 8px;")
            self.activity_layout.addWidget(placeholder_label)
        else:
            for doc in recent_docs:
                status_text = doc.status.value if doc.status else "unknown"
                date_str = doc.created_at.strftime("%d/%m/%Y") if doc.created_at else ""
                activity_item = QLabel(f"• {doc.code} - {status_text} ({date_str})")
                activity_item.setStyleSheet("padding: 4px; border-bottom: 1px solid #f0f0f0;")
                self.activity_layout.addWidget(activity_item)

        self.activity_layout.addStretch()