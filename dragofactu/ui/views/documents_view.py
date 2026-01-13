from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, 
    QComboBox, QDialog, QFormLayout, QHeaderView, QFrame, QDateEdit, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont

from dragofactu.models.database import SessionLocal
from dragofactu.models.entities import Document, DocumentLine, Client, Product, DocumentType, DocumentStatus
from dragofactu.ui.styles import get_card_style, get_primary_button_style, get_secondary_button_style, get_danger_button_style


class DocumentDialog(QDialog):
    """Dialog for creating/editing documents"""
    
    def __init__(self, document=None, parent=None):
        super().__init__(parent)
        self.document = document
        self.document_lines = []
        self.setup_ui()
        
        if document:
            self.load_document_data()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Create Document" if not self.document else "Edit Document")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Document info
        info_frame = QFrame()
        info_frame.setStyleSheet(get_card_style())
        info_layout = QFormLayout(info_frame)
        info_layout.setSpacing(12)
        
        # Document type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["QUOTE", "DELIVERY_NOTE", "INVOICE"])
        info_layout.addRow("Type*:", self.type_combo)
        
        # Client selection
        self.client_combo = QComboBox()
        self.load_clients()
        info_layout.addRow("Client*:", self.client_combo)
        
        # Document date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        info_layout.addRow("Date*:", self.date_edit)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["DRAFT", "SENT", "ACCEPTED", "PAID"])
        self.status_combo.setCurrentText("DRAFT")
        info_layout.addRow("Status:", self.status_combo)
        
        layout.addWidget(info_frame)
        
        # Document lines
        lines_frame = QFrame()
        lines_frame.setStyleSheet(get_card_style())
        lines_layout = QVBoxLayout(lines_frame)
        
        lines_title = QLabel("Document Lines")
        lines_title.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1D1D1F;
            font-family: system-ui, -apple-system, "SF Pro Display", "Segoe UI", sans-serif;
        """)
        lines_layout.addWidget(lines_title)
        
        # Lines table
        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(5)
        self.lines_table.setHorizontalHeaderLabels(["Product", "Description", "Quantity", "Price", "Total"])
        
        # Style table
        self.lines_table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E5E5EA;
                border-radius: 8px;
                gridline-color: #E5E5EA;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #E5E5EA;
            }
            QHeaderView::section {
                background-color: #FAFAFA;
                color: #6E6E73;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #D2D2D7;
            }
        """)
        
        # Configure headers
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        lines_layout.addWidget(self.lines_table)
        
        # Add line button
        add_line_btn = QPushButton("Add Line")
        add_line_btn.setStyleSheet(get_secondary_button_style())
        add_line_btn.clicked.connect(self.add_line)
        lines_layout.addWidget(add_line_btn)
        
        layout.addWidget(lines_frame)
        
        # Totals
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        
        self.total_label = QLabel("Total: €0.00")
        self.total_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            color: #1D1D1F;
            font-family: system-ui, -apple-system, "SF Pro Display", "Segoe UI", sans-serif;
        """)
        totals_layout.addWidget(self.total_label)
        
        layout.addLayout(totals_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        save_btn = QPushButton("Save Document")
        save_btn.setStyleSheet(get_primary_button_style())
        save_btn.clicked.connect(self.save_document)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(get_secondary_button_style())
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        # Add initial empty row
        self.add_line()
    
    def load_clients(self):
        """Load clients into combo box"""
        try:
            with SessionLocal() as db:
                clients = db.query(Client).filter(Client.is_active == True).all()
                self.client_combo.addItem("Select client...", None)
                for client in clients:
                    self.client_combo.addItem(client.name, client.id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading clients: {str(e)}")
    
    def add_line(self):
        """Add a new line to the document"""
        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)
        
        # Product dropdown
        product_combo = QComboBox()
        self.load_products(product_combo)
        self.lines_table.setCellWidget(row, 0, product_combo)
        
        # Description
        description_edit = QLineEdit()
        description_edit.setPlaceholderText("Description...")
        self.lines_table.setCellWidget(row, 1, description_edit)
        
        # Quantity
        quantity_spin = QSpinBox()
        quantity_spin.setMinimum(1)
        quantity_spin.setValue(1)
        quantity_spin.valueChanged.connect(self.update_totals)
        self.lines_table.setCellWidget(row, 2, quantity_spin)
        
        # Price
        price_spin = QDoubleSpinBox()
        price_spin.setMinimum(0)
        price_spin.setMaximum(999999)
        price_spin.setValue(0)
        price_spin.setDecimals(2)
        price_spin.valueChanged.connect(self.update_totals)
        self.lines_table.setCellWidget(row, 3, price_spin)
        
        # Total (read-only)
        total_label = QLabel("€0.00")
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        total_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                font-weight: 500;
            }
        """)
        self.lines_table.setCellWidget(row, 4, total_label)
        
        self.update_totals()
    
    def load_products(self, combo):
        """Load products into combo box"""
        try:
            with SessionLocal() as db:
                products = db.query(Product).filter(Product.is_active == True).all()
                combo.addItem("Select product...", None)
                for product in products:
                    combo.addItem(f"{product.name} (€{product.sale_price:.2f})", product.id)
        except Exception:
            combo.addItem("Error loading products", None)
    
    def update_totals(self):
        """Update line totals and document total"""
        total = 0.0
        
        for row in range(self.lines_table.rowCount()):
            quantity_spin = self.lines_table.cellWidget(row, 2)
            price_spin = self.lines_table.cellWidget(row, 3)
            total_label = self.lines_table.cellWidget(row, 4)
            
            if quantity_spin and price_spin and total_label:
                quantity = quantity_spin.value()
                price = price_spin.value()
                line_total = quantity * price
                total += line_total
                total_label.setText(f"€{line_total:.2f}")
        
        self.total_label.setText(f"Total: €{total:.2f}")
    
    def load_document_data(self):
        """Load existing document data"""
        if not self.document:
            return
        
        # Load document header
        self.type_combo.setCurrentText(self.document.document_type.value if hasattr(self.document.document_type, 'value') else str(self.document.document_type))
        self.status_combo.setCurrentText(self.document.document_status.value if hasattr(self.document.document_status, 'value') else str(self.document.document_status))
        self.date_edit.setDate(QDate.fromString(self.document.document_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        
        # Select client
        for i in range(self.client_combo.count()):
            if self.client_combo.itemData(i) == self.document.client_id:
                self.client_combo.setCurrentIndex(i)
                break
        
        # Load document lines
        try:
            with SessionLocal() as db:
                lines = db.query(DocumentLine).filter(DocumentLine.document_id == self.document.id).all()
                for line in lines:
                    row = self.lines_table.rowCount()
                    self.add_line()
                    
                    # Set line data
                    product_combo = self.lines_table.cellWidget(row, 0)
                    description_edit = self.lines_table.cellWidget(row, 1)
                    quantity_spin = self.lines_table.cellWidget(row, 2)
                    price_spin = self.lines_table.cellWidget(row, 3)
                    
                    if product_combo and line.product_id:
                        for i in range(product_combo.count()):
                            if product_combo.itemData(i) == line.product_id:
                                product_combo.setCurrentIndex(i)
                                break
                    
                    if description_edit:
                        description_edit.setText(line.description or "")
                    if quantity_spin:
                        quantity_spin.setValue(line.quantity or 1)
                    if price_spin:
                        price_spin.setValue(line.unit_price or 0)
                
                self.update_totals()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading document lines: {str(e)}")
    
    def save_document(self):
        """Save document data"""
        # Validation
        client_id = self.client_combo.currentData()
        if not client_id:
            QMessageBox.warning(self, "Validation Error", "Please select a client.")
            return
        
        # Check if lines have data
        has_lines = False
        for row in range(self.lines_table.rowCount()):
            product_combo = self.lines_table.cellWidget(row, 0)
            if product_combo and hasattr(product_combo, 'currentData') and product_combo.currentData():
                has_lines = True
                break
        
        if not has_lines:
            QMessageBox.warning(self, "Validation Error", "Please add at least one document line.")
            return
        
        try:
            with SessionLocal() as db:
                import datetime
                
                if self.document:
                    # Update existing document
                    self.document.document_type = self.type_combo.currentText()
                    self.document.document_status = self.status_combo.currentText()
                    self.document.document_date = self.date_edit.date().toPython()
                    self.document.client_id = client_id
                    self.document.total_amount = float(self.total_label.text().replace("Total: €", "").replace(",", ""))
                    
                    # Remove old lines
                    db.query(DocumentLine).filter(DocumentLine.document_id == self.document.id).delete()
                else:
                    # Create new document
                    doc_type = self.type_combo.currentText()
                    doc_status = self.status_combo.currentText()
                    
                    document = Document(
                        code=f"{doc_type[:3]}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                        document_type=doc_type,
                        document_status=doc_status,
                        document_date=self.date_edit.date().toPython(),
                        client_id=client_id,
                        total_amount=float(self.total_label.text().replace("Total: €", "").replace(",", "")),
                        is_active=True
                    )
                    db.add(document)
                    db.flush()  # Get the ID
                    self.document = document
                
                # Save document lines
                for row in range(self.lines_table.rowCount()):
                    product_combo = self.lines_table.cellWidget(row, 0)
                    description_edit = self.lines_table.cellWidget(row, 1)
                    quantity_spin = self.lines_table.cellWidget(row, 2)
                    price_spin = self.lines_table.cellWidget(row, 3)
                    
                    if product_combo and product_combo.currentData():
                        line = DocumentLine(
                            document_id=self.document.id,
                            product_id=product_combo.currentData(),
                            description=description_edit.text() if description_edit else "",
                            quantity=quantity_spin.value() if quantity_spin else 1,
                            unit_price=price_spin.value() if price_spin else 0,
                            is_active=True
                        )
                        db.add(line)
                
                db.commit()
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving document: {str(e)}")


class DocumentsView(QWidget):
    """Documents management view with full CRUD functionality"""
    
    document_updated = Signal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_documents()
    
    def setup_ui(self):
        """Setup documents UI with Apple-style design"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Documents Management")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 600;
            color: #1D1D1F;
            font-family: system-ui, -apple-system, "SF Pro Display", "Segoe UI", sans-serif;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Add document button
        self.add_btn = QPushButton("Create Document")
        self.add_btn.setStyleSheet(get_primary_button_style())
        self.add_btn.clicked.connect(self.add_document)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)
        
        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search documents...")
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
        self.search_edit.textChanged.connect(self.filter_documents)
        filter_layout.addWidget(self.search_edit)
        
        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "QUOTE", "DELIVERY_NOTE", "INVOICE"])
        self.type_filter.currentTextChanged.connect(self.filter_documents)
        self.type_filter.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #D2D2D7;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: #1D1D1F;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #007AFF;
            }
        """)
        filter_layout.addWidget(self.type_filter)
        
        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "DRAFT", "SENT", "ACCEPTED", "PAID"])
        self.status_filter.currentTextChanged.connect(self.filter_documents)
        self.status_filter.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #D2D2D7;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: #1D1D1F;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #007AFF;
            }
        """)
        filter_layout.addWidget(self.status_filter)
        
        layout.addLayout(filter_layout)
        
        # Documents table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Code", "Type", "Client", "Date", "Status", "Total", "Actions"
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
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Client
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Total
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.table)
    
    def load_documents(self):
        """Load documents from database"""
        try:
            with SessionLocal() as db:
                documents = db.query(Document).filter(Document.is_active == True).all()
                self.populate_table(documents)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading documents: {str(e)}")
    
    def populate_table(self, documents):
        """Populate table with document data"""
        self.table.setRowCount(len(documents))
        
        for row, document in enumerate(documents):
            # Code
            self.table.setItem(row, 0, QTableWidgetItem(document.code or ""))
            
            # Type
            doc_type = document.document_type.value if hasattr(document.document_type, 'value') else str(document.document_type)
            self.table.setItem(row, 1, QTableWidgetItem(doc_type))
            
            # Client
            client_name = document.client.name if document.client else "Unknown"
            self.table.setItem(row, 2, QTableWidgetItem(client_name))
            
            # Date
            date_str = document.document_date.strftime("%Y-%m-%d") if document.document_date else ""
            self.table.setItem(row, 3, QTableWidgetItem(date_str))
            
            # Status
            status = document.document_status.value if hasattr(document.document_status, 'value') else str(document.document_status)
            status_item = QTableWidgetItem(status)
            
            # Color code status
            if status == "PAID":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif status == "ACCEPTED":
                status_item.setForeground(Qt.GlobalColor.blue)
            elif status == "SENT":
                status_item.setForeground(Qt.GlobalColor.yellow)
            else:  # DRAFT
                status_item.setForeground(Qt.GlobalColor.gray)
            
            self.table.setItem(row, 4, status_item)
            
            # Total
            total_str = f"€{document.total_amount:.2f}" if document.total_amount else "€0.00"
            self.table.setItem(row, 5, QTableWidgetItem(total_str))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet(get_secondary_button_style())
            edit_btn.setMinimumWidth(60)
            edit_btn.clicked.connect(lambda checked, d=document: self.edit_document(d))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(get_danger_button_style())
            delete_btn.setMinimumWidth(60)
            delete_btn.clicked.connect(lambda checked, d=document: self.delete_document(d))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 6, actions_widget)
    
    def filter_documents(self):
        """Filter documents based on search text and filters"""
        search_text = self.search_edit.text().lower()
        type_filter = self.type_filter.currentText()
        status_filter = self.status_filter.currentText()
        
        for row in range(self.table.rowCount()):
            show_row = True
            
            # Search filter
            if search_text:
                found = False
                for col in range(self.table.columnCount() - 1):  # Exclude actions column
                    item = self.table.item(row, col)
                    if item and search_text in item.text().lower():
                        found = True
                        break
                show_row = found and show_row
            
            # Type filter
            if type_filter != "All Types" and show_row:
                type_item = self.table.item(row, 1)
                if type_item and type_item.text() != type_filter:
                    show_row = False
            
            # Status filter
            if status_filter != "All Status" and show_row:
                status_item = self.table.item(row, 4)
                if status_item and status_item.text() != status_filter:
                    show_row = False
            
            self.table.setRowHidden(row, not show_row)
    
    def add_document(self):
        """Add new document"""
        dialog = DocumentDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_documents()
            self.document_updated.emit()
    
    def edit_document(self, document):
        """Edit existing document"""
        dialog = DocumentDialog(document, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_documents()
            self.document_updated.emit()
    
    def delete_document(self, document):
        """Delete document with confirmation"""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete document '{document.code}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with SessionLocal() as db:
                    # Soft delete
                    document.is_active = False
                    db.commit()
                    self.load_documents()
                    self.document_updated.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting document: {str(e)}")
    
    def refresh(self):
        """Refresh documents view"""
        self.load_documents()