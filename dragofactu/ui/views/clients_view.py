from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, 
    QComboBox, QDialog, QFormLayout, QHeaderView, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from dragofactu.models.database import SessionLocal
from dragofactu.models.entities import Client
from dragofactu.ui.styles import get_card_style, get_primary_button_style, get_secondary_button_style, get_danger_button_style


class ClientDialog(QDialog):
    """Dialog for adding/editing clients"""
    
    def __init__(self, client=None, parent=None):
        super().__init__(parent)
        self.client = client
        self.setup_ui()
        
        if client:
            self.load_client_data()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Add Client" if not self.client else "Edit Client")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Card container
        card = QFrame()
        card.setStyleSheet(get_card_style())
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(24, 24, 24, 24)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(16)
        
        # Client fields
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Client name...")
        form_layout.addRow("Name*:", self.name_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@company.com")
        form_layout.addRow("Email:", self.email_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+34 900 000 000")
        form_layout.addRow("Phone:", self.phone_edit)
        
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Street address...")
        form_layout.addRow("Address:", self.address_edit)
        
        self.city_edit = QLineEdit()
        self.city_edit.setPlaceholderText("City...")
        form_layout.addRow("City:", self.city_edit)
        
        self.postal_code_edit = QLineEdit()
        self.postal_code_edit.setPlaceholderText("Postal code...")
        form_layout.addRow("Postal Code:", self.postal_code_edit)
        
        self.tax_id_edit = QLineEdit()
        self.tax_id_edit.setPlaceholderText("Tax ID / VAT number...")
        form_layout.addRow("Tax ID:", self.tax_id_edit)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive"])
        form_layout.addRow("Status:", self.status_combo)
        
        card_layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(get_primary_button_style())
        save_btn.clicked.connect(self.save_client)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(get_secondary_button_style())
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        
        card_layout.addLayout(button_layout)
        layout.addWidget(card)
    
    def load_client_data(self):
        """Load client data into form"""
        if self.client:
            self.name_edit.setText(self.client.name or "")
            self.email_edit.setText(self.client.email or "")
            self.phone_edit.setText(self.client.phone or "")
            self.address_edit.setText(self.client.address or "")
            self.city_edit.setText(self.client.city or "")
            self.postal_code_edit.setText(self.client.postal_code or "")
            self.tax_id_edit.setText(self.client.tax_id or "")
            self.status_combo.setCurrentText("Active" if self.client.is_active else "Inactive")
    
    def save_client(self):
        """Save client data"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Client name is required.")
            return
        
        try:
            with SessionLocal() as db:
                if self.client:
                    # Update existing client
                    self.client.name = name
                    self.client.email = self.email_edit.text().strip() or None
                    self.client.phone = self.phone_edit.text().strip() or None
                    self.client.address = self.address_edit.text().strip() or None
                    self.client.city = self.city_edit.text().strip() or None
                    self.client.postal_code = self.postal_code_edit.text().strip() or None
                    self.client.tax_id = self.tax_id_edit.text().strip() or None
                    self.client.is_active = self.status_combo.currentText() == "Active"
                    db.commit()
                else:
                    # Create new client
                    import datetime
                    client = Client(
                        code=f"C-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                        name=name,
                        email=self.email_edit.text().strip() or None,
                        phone=self.phone_edit.text().strip() or None,
                        address=self.address_edit.text().strip() or None,
                        city=self.city_edit.text().strip() or None,
                        postal_code=self.postal_code_edit.text().strip() or None,
                        tax_id=self.tax_id_edit.text().strip() or None,
                        is_active=self.status_combo.currentText() == "Active"
                    )
                    db.add(client)
                    db.commit()
                
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving client: {str(e)}")


class ClientsView(QWidget):
    """Clients management view with full CRUD functionality"""
    
    client_updated = Signal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_clients()
    
    def setup_ui(self):
        """Setup clients UI with Apple-style design"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Clients Management")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 600;
            color: #1D1D1F;
            font-family: system-ui, -apple-system, "SF Pro Display", "Segoe UI", sans-serif;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Add client button
        self.add_btn = QPushButton("Add Client")
        self.add_btn.setStyleSheet(get_primary_button_style())
        self.add_btn.clicked.connect(self.add_client)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search clients...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #D2D2D7;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: #1D1D1F;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #007AFF;
            }
        """)
        self.search_edit.textChanged.connect(self.filter_clients)
        search_layout.addWidget(self.search_edit)
        
        layout.addLayout(search_layout)
        
        # Clients table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Code", "Name", "Email", "Phone", "City", "Status", "Created", "Actions"
        ])
        
        # Style table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E5E5EA;
                border-radius: 12px;
                gridline-color: #E5E5EA;
                selection-background-color: #007AFF;
                selection-color: #FFFFFF;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #E5E5EA;
            }
            QTableWidget::item:hover {
                background-color: #F5F5F7;
            }
            QHeaderView::section {
                background-color: #FAFAFA;
                color: #6E6E73;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 12px;
                border: none;
                border-bottom: 1px solid #D2D2D7;
            }
        """)
        
        # Configure headers
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Code
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Email
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Phone
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # City
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Created
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.table)
    
    def load_clients(self):
        """Load clients from database"""
        try:
            with SessionLocal() as db:
                clients = db.query(Client).all()
                self.populate_table(clients)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading clients: {str(e)}")
    
    def populate_table(self, clients):
        """Populate table with client data"""
        self.table.setRowCount(len(clients))
        
        for row, client in enumerate(clients):
            # Code
            self.table.setItem(row, 0, QTableWidgetItem(client.code or ""))
            
            # Name
            self.table.setItem(row, 1, QTableWidgetItem(client.name or ""))
            
            # Email
            self.table.setItem(row, 2, QTableWidgetItem(client.email or ""))
            
            # Phone
            self.table.setItem(row, 3, QTableWidgetItem(client.phone or ""))
            
            # City
            self.table.setItem(row, 4, QTableWidgetItem(client.city or ""))
            
            # Status
            status_text = "Active" if client.is_active else "Inactive"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(
                Qt.GlobalColor.darkGreen if client.is_active else Qt.GlobalColor.darkRed
            )
            self.table.setItem(row, 5, status_item)
            
            # Created date
            created_date = client.created_at.strftime("%Y-%m-%d") if client.created_at else ""
            self.table.setItem(row, 6, QTableWidgetItem(created_date))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet(get_secondary_button_style())
            edit_btn.setMinimumWidth(60)
            edit_btn.clicked.connect(lambda checked, c=client: self.edit_client(c))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(get_danger_button_style())
            delete_btn.setMinimumWidth(60)
            delete_btn.clicked.connect(lambda checked, c=client: self.delete_client(c))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 7, actions_widget)
    
    def filter_clients(self):
        """Filter clients based on search text"""
        search_text = self.search_edit.text().lower()
        
        for row in range(self.table.rowCount()):
            show_row = False
            
            for col in range(self.table.columnCount() - 1):  # Exclude actions column
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            
            self.table.setRowHidden(row, not show_row)
    
    def add_client(self):
        """Add new client"""
        dialog = ClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_clients()
            self.client_updated.emit()
    
    def edit_client(self, client):
        """Edit existing client"""
        dialog = ClientDialog(client, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_clients()
            self.client_updated.emit()
    
    def delete_client(self, client):
        """Delete client with confirmation"""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete client '{client.name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with SessionLocal() as db:
                    db.delete(client)
                    db.commit()
                    self.load_clients()
                    self.client_updated.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting client: {str(e)}")
    
    def refresh(self):
        """Refresh clients view"""
        self.load_clients()