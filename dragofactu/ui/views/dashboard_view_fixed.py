"""
Fixed Dashboard View with proper Qt attributes and translations
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from dragofactu.models.database import SessionLocal
from dragofactu.models.entities import User
from dragofactu.services.business.entity_services import ClientService, SupplierService, ProductService
from dragofactu.services.documents.document_service import DocumentService, DocumentStatus
from dragofactu.config.translation import t

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.summary_labels = {}
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Setup dashboard UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(t("menu.dashboard"))
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
        cards = [
            (t("dashboard.total_clients"), "0", "#0078d4", 0, 0),
            (t("dashboard.total_suppliers"), "0", "#107c10", 0, 1),
            (t("dashboard.active_products"), "0", "#d83b01", 0, 2),
            (t("dashboard.pending_documents"), "0", "#5c2d91", 1, 0),
            (t("dashboard.low_stock_items"), "0", "#d13438", 1, 1),
            (t("dashboard.unpaid_invoices"), "0", "#ca5010", 1, 2),
        ]
        
        for title, value, color, row, col in cards:
            card = self.create_summary_card(title, value, color)
            layout.addWidget(card, row, col)
            
            # Store reference to value label for updates
            self.summary_labels[title] = card.findChild(QLabel, "value_label")
    
    def create_summary_card(self, title, value, color):
        """Create a single summary card"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
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
        title_font = QFont("Arial", 10, QFont.Weight.Bold)
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
        section_frame.setFrameStyle(QFrame.Shape.Box)
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
        title_label = QLabel(t("dashboard.recent_activity"))
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
                pending_docs = len(document_service.search_documents(
                    current_user, 
                    doc_type=None, 
                    client_id=None, 
                    status=DocumentStatus.DRAFT, 
                    date_from=None, 
                    date_to=None, 
                    created_by=None
                ))
                
                # Update summary labels
                self.summary_labels[t("dashboard.total_clients")].setText(str(client_count))
                self.summary_labels[t("dashboard.total_suppliers")].setText(str(supplier_count))
                self.summary_labels[t("dashboard.active_products")].setText(str(product_count))
                self.summary_labels[t("dashboard.pending_documents")].setText(str(pending_docs))
                self.summary_labels[t("dashboard.low_stock_items")].setText(str(low_stock_count))
                self.summary_labels[t("dashboard.unpaid_invoices")].setText("0")  # TODO: Implement unpaid invoices
                
                # Clear and update recent activity
                self.clear_activity_layout()
                self.update_recent_activity(db)
                
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
    
    def clear_activity_layout(self):
        """Clear activity layout"""
        while self.activity_layout.count():
            child = self.activity_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def update_recent_activity(self, db):
        """Update recent activity section"""
        try:
            # Add placeholder activity items
            activities = [
                "Sistema iniciado",
                "Base de datos conectada", 
                "Dashboard actualizado"
            ]
            
            for activity in activities:
                activity_label = QLabel(f"• {activity}")
                activity_label.setStyleSheet("color: #666; padding: 4px;")
                self.activity_layout.addWidget(activity_label)
                
        except Exception as e:
            print(f"Error updating activity: {e}")
    
    def show_error(self, message):
        """Show error message"""
        self.clear_activity_layout()
        error_label = QLabel(f"❌ {t('dashboard.error_loading_data')}: {message}")
        error_label.setStyleSheet("color: red; padding: 8px;")
        self.activity_layout.addWidget(error_label)