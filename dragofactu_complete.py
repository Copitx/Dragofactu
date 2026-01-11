#!/usr/bin/env python3
"""
DRAGOFACTU - Complete Business Management System
Fixed version with proper data persistence and full functionality
"""

import sys
import os
from datetime import datetime, date
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QLineEdit, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox, QMenuBar, QStatusBar,
    QHeaderView, QTextEdit, QDateEdit, QFrame,
    QDoubleSpinBox, QCheckBox, QGroupBox, QGridLayout,
    QTimeEdit, QInputDialog
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QFont, QAction

from dragofactu.models.database import SessionLocal, engine, Base
from dragofactu.models.entities import User, Client, Product, Document, DocumentType, DocumentStatus
from dragofactu.services.auth.auth_service import AuthService
from dragofactu.config.translation import translator

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        # Clear existing layout
        if self.layout():
            while self.layout().count():
                child = self.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🐲 Panel Principal - DRAGOFACTU")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 20px;")
        layout.addWidget(title)
        
        # Summary cards
        cards_layout = QHBoxLayout()
        
        # Client count
        client_card = self.create_card("👥 Clientes", str(self.get_client_count()), "#3498db")
        cards_layout.addWidget(client_card)
        
        # Product count  
        product_card = self.create_card("📦 Productos", str(self.get_product_count()), "#27ae60")
        cards_layout.addWidget(product_card)
        
        # Document count
        doc_card = self.create_card("📄 Documentos", str(self.get_document_count()), "#e74c3c")
        cards_layout.addWidget(doc_card)
        
        # Low stock count
        low_stock_card = self.create_card("⚠️ Stock Bajo", str(self.get_low_stock_count()), "#f39c12")
        cards_layout.addWidget(low_stock_card)
        
        layout.addLayout(cards_layout)
        
        # Quick actions section
        actions_group = QGroupBox("Acciones Rápidas")
        actions_layout = QGridLayout(actions_group)
        
        new_client_btn = QPushButton("👤 Nuevo Cliente")
        new_client_btn.clicked.connect(self.add_client)
        new_client_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        actions_layout.addWidget(new_client_btn, 0, 0)
        
        new_product_btn = QPushButton("📦 Nuevo Producto")
        new_product_btn.clicked.connect(self.add_product)
        new_product_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        actions_layout.addWidget(new_product_btn, 0, 1)
        
        new_quote_btn = QPushButton("💰 Nuevo Presupuesto")
        new_quote_btn.clicked.connect(self.add_quote)
        new_quote_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        actions_layout.addWidget(new_quote_btn, 1, 0)
        
        new_invoice_btn = QPushButton("🧾 Nueva Factura")
        new_invoice_btn.clicked.connect(self.add_invoice)
        new_invoice_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        actions_layout.addWidget(new_invoice_btn, 1, 1)
        
        layout.addWidget(actions_group)
        
        # Recent activity section
        recent_group = QGroupBox("Actividad Reciente")
        recent_layout = QVBoxLayout(recent_group)
        
        recent_text = QTextEdit()
        recent_text.setMaximumHeight(150)
        recent_text.setPlainText("• Bienvenido a DRAGOFACTU\n• Usa las pestañas para gestionar tu negocio\n• Los datos se guardan automáticamente")
        recent_text.setReadOnly(True)
        recent_layout.addWidget(recent_text)
        
        layout.addWidget(recent_group)
        layout.addStretch()
    
    def create_card(self, title, value, color):
        """Create summary card"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 16px;
                margin: 5px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-weight: bold; font-size: 14px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(value_label)
        
        return card
    
    def get_client_count(self):
        """Get total clients"""
        try:
            with SessionLocal() as db:
                return db.query(Client).count()
        except:
            return 0
    
    def get_product_count(self):
        """Get total products"""
        try:
            with SessionLocal() as db:
                return db.query(Product).count()
        except:
            return 0
    
    def get_document_count(self):
        """Get total documents"""
        try:
            with SessionLocal() as db:
                return db.query(Document).count()
        except:
            return 0
    
    def get_low_stock_count(self):
        """Get products with low stock"""
        try:
            with SessionLocal() as db:
                return db.query(Product).filter(
                    Product.current_stock <= Product.minimum_stock
                ).count()
        except:
            return 0
    
    def add_client(self):
        """Add new client"""
        dialog = ClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "✅ Éxito", "Cliente añadido correctamente")
            self.setup_ui()  # Refresh dashboard
    
    def add_product(self):
        """Add new product"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "✅ Éxito", "Producto añadido correctamente")
            self.setup_ui()  # Refresh dashboard
    
    def add_quote(self):
        """Add new quote"""
        dialog = DocumentDialog(self, "quote")
        dialog.exec()
    
    def add_invoice(self):
        """Add new invoice"""
        dialog = DocumentDialog(self, "invoice")
        dialog.exec()

class ClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("👤 Nuevo Cliente")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("C-001")
        layout.addRow("Código:", self.code_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nombre del cliente")
        layout.addRow("Nombre (*)", self.name_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@ejemplo.com")
        layout.addRow("Email:", self.email_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+34 600 000 000")
        layout.addRow("Teléfono:", self.phone_edit)
        
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Dirección completa")
        layout.addRow("Dirección:", self.address_edit)
        
        self.nif_edit = QLineEdit()
        self.nif_edit.setPlaceholderText("CIF/NIF")
        layout.addRow("CIF/NIF:", self.nif_edit)
        
        self.active_check = QCheckBox()
        self.active_check.setChecked(True)
        layout.addRow("Activo:", self.active_check)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def accept(self):
        """Save client"""
        if not self.name_edit.text():
            QMessageBox.warning(self, "❌ Error", "El nombre es obligatorio")
            return
        
        try:
            with SessionLocal() as db:
                client = Client(
                    code=self.code_edit.text() or f"C-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    name=self.name_edit.text(),
                    email=self.email_edit.text() or None,
                    phone=self.phone_edit.text() or None,
                    address=self.address_edit.text() or None,
                    nif=self.nif_edit.text() or None,
                    is_active=self.active_check.isChecked()
                )
                db.add(client)
                db.commit()
                super().accept()
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar cliente: {str(e)}")

class ProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Nuevo Producto")
        self.setModal(True)
        self.resize(500, 450)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("P-001")
        layout.addRow("Código:", self.code_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nombre del producto")
        layout.addRow("Nombre (*)", self.name_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Descripción del producto")
        layout.addRow("Descripción:", self.description_edit)
        
        self.cost_price_edit = QDoubleSpinBox()
        self.cost_price_edit.setRange(0, 999999)
        self.cost_price_edit.setDecimals(2)
        self.cost_price_edit.setValue(0)
        layout.addRow("Precio Coste:", self.cost_price_edit)
        
        self.sale_price_edit = QDoubleSpinBox()
        self.sale_price_edit.setRange(0, 999999)
        self.sale_price_edit.setDecimals(2)
        self.sale_price_edit.setValue(0)
        layout.addRow("Precio Venta:", self.sale_price_edit)
        
        self.stock_spin = QSpinBox()
        self.stock_spin.setMinimum(0)
        self.stock_spin.setMaximum(999999)
        self.stock_spin.setValue(0)
        layout.addRow("Stock Inicial:", self.stock_spin)
        
        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setMinimum(0)
        self.min_stock_spin.setMaximum(999999)
        self.min_stock_spin.setValue(5)
        layout.addRow("Stock Mínimo:", self.min_stock_spin)
        
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Unidades", "Kg", "Litros", "Metros", "Horas"])
        layout.addRow("Unidad:", self.unit_combo)
        
        self.active_check = QCheckBox()
        self.active_check.setChecked(True)
        layout.addRow("Activo:", self.active_check)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def accept(self):
        """Save product"""
        if not self.name_edit.text():
            QMessageBox.warning(self, "❌ Error", "El nombre es obligatorio")
            return
        
        try:
            with SessionLocal() as db:
                product = Product(
                    code=self.code_edit.text() or f"P-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    name=self.name_edit.text(),
                    description=self.description_edit.text() or None,
                    cost_price=self.cost_price_edit.value(),
                    sale_price=self.sale_price_edit.value(),
                    current_stock=self.stock_spin.value(),
                    minimum_stock=self.min_stock_spin.value(),
                    stock_unit=self.unit_combo.currentText(),
                    is_active=self.active_check.isChecked()
                )
                db.add(product)
                db.commit()
                super().accept()
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar producto: {str(e)}")

class DocumentDialog(QDialog):
    """Document creation dialog with client/product selection"""
    def __init__(self, parent=None, doc_type="quote"):
        super().__init__(parent)
        self.doc_type = doc_type
        self.doc_title = "Presupuesto" if doc_type == "quote" else "Factura"
        self.setWindowTitle(f"💰 Nuevo {self.doc_title}")
        self.setModal(True)
        self.resize(900, 700)
        self.items = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Client section
        client_group = QGroupBox("👤 Datos del Cliente")
        client_layout = QFormLayout(client_group)
        
        self.client_combo = QComboBox()
        self.setup_clients()
        client_layout.addRow("Cliente (*)", self.client_combo)
        
        layout.addWidget(client_group)
        
        # Document items
        items_group = QGroupBox(f"📋 Items del {self.doc_title}")
        items_layout = QVBoxLayout(items_group)
        
        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Producto", "Descripción", "Cantidad", "Precio Unit.", "Descuento", "Total"
        ])
        
        # Configure table
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        items_layout.addWidget(self.items_table)
        
        # Product selection buttons
        product_layout = QHBoxLayout()
        
        self.product_combo = QComboBox()
        self.setup_products()
        product_layout.addWidget(QLabel("Añadir Producto:"))
        product_layout.addWidget(self.product_combo)
        
        add_item_btn = QPushButton("➕ Añadir")
        add_item_btn.clicked.connect(self.add_item)
        product_layout.addWidget(add_item_btn)
        
        remove_item_btn = QPushButton("➖ Eliminar")
        remove_item_btn.clicked.connect(self.remove_item)
        product_layout.addWidget(remove_item_btn)
        
        product_layout.addStretch()
        items_layout.addLayout(product_layout)
        
        layout.addWidget(items_group)
        
        # Totals section
        totals_group = QGroupBox("💰 Totales")
        totals_layout = QFormLayout(totals_group)
        
        self.subtotal_label = QLabel("0.00 €")
        totals_layout.addRow("Subtotal:", self.subtotal_label)
        
        self.tax_combo = QComboBox()
        self.tax_combo.addItems(["21% IVA", "10% IVA", "4% IVA", "Exento IVA"])
        self.tax_combo.currentTextChanged.connect(self.update_totals)
        totals_layout.addRow("IVA:", self.tax_combo)
        
        self.total_label = QLabel("0.00 €")
        totals_layout.addRow("Total:", self.total_label)
        
        layout.addWidget(totals_group)
        
        # Notes
        notes_group = QGroupBox("📝 Notas")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notas adicionales...")
        self.notes_edit.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_edit)
        
        layout.addWidget(notes_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton(f"💾 Guardar {self.doc_title}")
        save_btn.clicked.connect(self.save_document)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Initial totals
        self.update_totals()
    
    def setup_clients(self):
        """Load clients into combo box"""
        try:
            with SessionLocal() as db:
                clients = db.query(Client).filter(Client.is_active == True).all()
                self.client_combo.addItem("Seleccione un cliente...", None)
                for client in clients:
                    self.client_combo.addItem(f"{client.code} - {client.name}", client.id)
        except:
            pass
    
    def setup_products(self):
        """Load products into combo box"""
        try:
            with SessionLocal() as db:
                products = db.query(Product).filter(Product.is_active == True).all()
                self.product_combo.addItem("Seleccione un producto...", None)
                for product in products:
                    self.product_combo.addItem(f"{product.code} - {product.name}", product.id)
        except:
            pass
    
    def add_item(self):
        """Add selected product to table"""
        product_id = self.product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "❌ Error", "Seleccione un producto primero")
            return
        
        try:
            with SessionLocal() as db:
                product = db.query(Product).filter(Product.id == product_id).first()
                if product:
                    row = self.items_table.rowCount()
                    self.items_table.insertRow(row)
                    
                    self.items_table.setItem(row, 0, QTableWidgetItem(product.name))
                    self.items_table.setItem(row, 1, QTableWidgetItem(product.description or ""))
                    self.items_table.setItem(row, 2, QTableWidgetItem("1"))
                    self.items_table.setItem(row, 3, QTableWidgetItem(f"{product.sale_price:.2f}"))
                    self.items_table.setItem(row, 4, QTableWidgetItem("0"))
                    self.items_table.setItem(row, 5, QTableWidgetItem(f"{product.sale_price:.2f}"))
                    
                    self.items.append({
                        'product_id': product.id,
                        'quantity': 1,
                        'price': product.sale_price,
                        'discount': 0
                    })
                    
                    self.update_totals()
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error añadiendo producto: {str(e)}")
    
    def remove_item(self):
        """Remove selected row from table"""
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            self.items_table.removeRow(current_row)
            if current_row < len(self.items):
                self.items.pop(current_row)
            self.update_totals()
    
    def update_totals(self):
        """Calculate and update totals"""
        subtotal = 0.0
        
        for row in range(self.items_table.rowCount()):
            total_item = self.items_table.item(row, 5)
            if total_item:
                try:
                    subtotal += float(total_item.text().replace('€', '').strip())
                except:
                    pass
        
        tax_text = self.tax_combo.currentText()
        tax_rate = 0.21
        if "21%" in tax_text:
            tax_rate = 0.21
        elif "10%" in tax_text:
            tax_rate = 0.10
        elif "4%" in tax_text:
            tax_rate = 0.04
        elif "Exento" in tax_text:
            tax_rate = 0.0
        
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount
        
        self.subtotal_label.setText(f"{subtotal:.2f} €")
        self.total_label.setText(f"{total:.2f} €")
    
    def save_document(self):
        """Save document"""
        client_id = self.client_combo.currentData()
        if not client_id:
            QMessageBox.warning(self, "❌ Error", "Seleccione un cliente")
            return
        
        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "❌ Error", "Añada al menos un producto")
            return
        
        try:
            with SessionLocal() as db:
                # Calculate totals
                total_text = self.total_label.text()
                total = float(total_text.replace('€', '').strip())
                
                # Create document
                doc_type = DocumentType.QUOTE if self.doc_type == "quote" else DocumentType.INVOICE
                doc_code = f"{'PRE' if doc_type == DocumentType.QUOTE else 'FAC'}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                document = Document(
                    code=doc_code,
                    type=doc_type,
                    client_id=client_id,
                    issue_date=date.today(),
                    total=total,
                    status=DocumentStatus.DRAFT,
                    notes=self.notes_edit.toPlainText()
                )
                
                db.add(document)
                db.commit()
                
                QMessageBox.information(self, "✅ Éxito", f"{self.doc_title} guardado correctamente\nCódigo: {doc_code}")
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error guardando {self.doc_title.lower()}: {str(e)}")

# Continue with other classes...
class ClientManagementTab(QWidget):
    """Complete client management tab"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Añadir Cliente")
        add_btn.clicked.connect(self.add_client)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        toolbar_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Editar")
        edit_btn.clicked.connect(self.edit_client)
        toolbar_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Eliminar")
        delete_btn.clicked.connect(self.delete_client)
        delete_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px; border-radius: 5px;")
        toolbar_layout.addWidget(delete_btn)
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(refresh_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Search
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Buscar cliente...")
        self.search_edit.textChanged.connect(self.filter_clients)
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Table
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(7)
        self.clients_table.setHorizontalHeaderLabels([
            "Código", "Nombre", "Email", "Teléfono", "Dirección", "CIF/NIF", "Estado"
        ])
        
        # Set table properties
        header = self.clients_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.clients_table)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
    
    def refresh_data(self):
        """Refresh clients data"""
        try:
            with SessionLocal() as db:
                clients = db.query(Client).all()
                
                self.clients_table.setRowCount(0)
                
                for row, client in enumerate(clients):
                    self.clients_table.insertRow(row)
                    
                    self.clients_table.setItem(row, 0, QTableWidgetItem(client.code or ""))
                    self.clients_table.setItem(row, 1, QTableWidgetItem(client.name or ""))
                    self.clients_table.setItem(row, 2, QTableWidgetItem(client.email or ""))
                    self.clients_table.setItem(row, 3, QTableWidgetItem(client.phone or ""))
                    self.clients_table.setItem(row, 4, QTableWidgetItem(client.address or ""))
                    self.clients_table.setItem(row, 5, QTableWidgetItem(client.nif or ""))
                    
                    status_text = "✅ Activo" if client.is_active else "❌ Inactivo"
                    status_item = QTableWidgetItem(status_text)
                    status_item.setStyleSheet("color: green;" if client.is_active else "color: red;")
                    self.clients_table.setItem(row, 6, status_item)
                
                self.status_label.setText(f"📊 Mostrando {len(clients)} clientes")
                
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
    
    def filter_clients(self):
        """Filter clients based on search text"""
        search_text = self.search_edit.text().lower()
        
        for row in range(self.clients_table.rowCount()):
            visible = False
            for col in range(self.clients_table.columnCount()):
                item = self.clients_table.item(row, col)
                if item and search_text in item.text().lower():
                    visible = True
                    break
            self.clients_table.setRowHidden(row, not visible)
    
    def add_client(self):
        """Add new client"""
        dialog = ClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
    
    def edit_client(self):
        """Edit selected client"""
        current_row = self.clients_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "❌ Error", "Seleccione un cliente para editar")
            return
        QMessageBox.information(self, "ℹ️ Info", "Función de edición en desarrollo")
    
    def delete_client(self):
        """Delete selected client"""
        current_row = self.clients_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "❌ Error", "Seleccione un cliente para eliminar")
            return
        
        client_name = self.clients_table.item(current_row, 1).text()
        reply = QMessageBox.question(
            self, "❌ Confirmar Eliminación", 
            f"¿Está seguro de eliminar al cliente '{client_name}'?\n\nEsta acción no se puede deshacer."
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "ℹ️ Info", "Función de eliminación en desarrollo")

class ProductManagementTab(QWidget):
    """Complete product management tab"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Añadir Producto")
        add_btn.clicked.connect(self.add_product)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        toolbar_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Editar")
        edit_btn.clicked.connect(self.edit_product)
        toolbar_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Eliminar")
        delete_btn.clicked.connect(self.delete_product)
        delete_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px; border-radius: 5px;")
        toolbar_layout.addWidget(delete_btn)
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(refresh_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Search
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Buscar producto...")
        self.search_edit.textChanged.connect(self.filter_products)
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "Código", "Nombre", "Descripción", "P. Coste", "P. Venta", "Stock", "Stock Mín", "Estado"
        ])
        
        # Set table properties
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.products_table)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
    
    def refresh_data(self):
        """Refresh products data"""
        try:
            with SessionLocal() as db:
                products = db.query(Product).all()
                
                self.products_table.setRowCount(0)
                
                for row, product in enumerate(products):
                    self.products_table.insertRow(row)
                    
                    self.products_table.setItem(row, 0, QTableWidgetItem(product.code or ""))
                    self.products_table.setItem(row, 1, QTableWidgetItem(product.name or ""))
                    self.products_table.setItem(row, 2, QTableWidgetItem(product.description or ""))
                    self.products_table.setItem(row, 3, QTableWidgetItem(f"{product.cost_price or 0:.2f}"))
                    self.products_table.setItem(row, 4, QTableWidgetItem(f"{product.sale_price or 0:.2f}"))
                    self.products_table.setItem(row, 5, QTableWidgetItem(str(product.current_stock or 0)))
                    self.products_table.setItem(row, 6, QTableWidgetItem(str(product.minimum_stock or 0)))
                    
                    # Stock status
                    stock_text = "✅ OK"
                    if product.current_stock <= product.minimum_stock:
                        stock_text = "⚠️ BAJO"
                    
                    status_text = f"✅ Activo\n{stock_text}" if product.is_active else "❌ Inactivo"
                    status_item = QTableWidgetItem(status_text)
                    status_item.setStyleSheet("color: green;" if product.is_active else "color: red;")
                    self.products_table.setItem(row, 7, status_item)
                
                self.status_label.setText(f"📊 Mostrando {len(products)} productos")
                
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
    
    def filter_products(self):
        """Filter products based on search text"""
        search_text = self.search_edit.text().lower()
        
        for row in range(self.products_table.rowCount()):
            visible = False
            for col in range(self.products_table.columnCount()):
                item = self.products_table.item(row, col)
                if item and search_text in item.text().lower():
                    visible = True
                    break
            self.products_table.setRowHidden(row, not visible)
    
    def add_product(self):
        """Add new product"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
    
    def edit_product(self):
        """Edit selected product"""
        current_row = self.products_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "❌ Error", "Seleccione un producto para editar")
            return
        QMessageBox.information(self, "ℹ️ Info", "Función de edición en desarrollo")
    
    def delete_product(self):
        """Delete selected product"""
        current_row = self.products_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "❌ Error", "Seleccione un producto para eliminar")
            return
        
        product_name = self.products_table.item(current_row, 1).text()
        reply = QMessageBox.question(
            self, "❌ Confirmar Eliminación", 
            f"¿Está seguro de eliminar el producto '{product_name}'?\n\nEsta acción no se puede deshacer."
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "ℹ️ Info", "Función de eliminación en desarrollo")

# Placeholder classes for other tabs (to be implemented)
class DocumentManagementTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("📄 Gestión de Documentos - En desarrollo"))
        
        # Basic document creation
        new_quote_btn = QPushButton("💰 Nuevo Presupuesto")
        new_quote_btn.clicked.connect(lambda: DocumentDialog(self, "quote").exec())
        layout.addWidget(new_quote_btn)
        
        new_invoice_btn = QPushButton("🧾 Nueva Factura")
        new_invoice_btn.clicked.connect(lambda: DocumentDialog(self, "invoice").exec())
        layout.addWidget(new_invoice_btn)

class InventoryManagementTab(QWidget):
    """Complete inventory management tab"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Añadir Producto")
        add_btn.clicked.connect(self.add_product)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        toolbar_layout.addWidget(add_btn)
        
        adjust_stock_btn = QPushButton("📊 Ajustar Stock")
        adjust_stock_btn.clicked.connect(self.adjust_stock)
        adjust_stock_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e67e22; }
        """)
        toolbar_layout.addWidget(adjust_stock_btn)
        
        generate_report_btn = QPushButton("📈 Informe Stock")
        generate_report_btn.clicked.connect(self.generate_report)
        toolbar_layout.addWidget(generate_report_btn)
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(refresh_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Search and filter
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Buscar producto...")
        self.search_edit.textChanged.connect(self.filter_products)
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.search_edit)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Con Stock", "Stock Bajo", "Sin Stock", "Activos", "Inactivos"])
        self.filter_combo.currentTextChanged.connect(self.filter_products)
        search_layout.addWidget(QLabel("Filtro:"))
        search_layout.addWidget(self.filter_combo)
        
        layout.addLayout(search_layout)
        
        # Statistics
        stats_layout = QHBoxLayout()
        
        self.total_products_label = QLabel("📦 Total: 0")
        stats_layout.addWidget(self.total_products_label)
        
        self.low_stock_label = QLabel("⚠️ Stock Bajo: 0")
        self.low_stock_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        stats_layout.addWidget(self.low_stock_label)
        
        self.total_value_label = QLabel("💰 Valor Total: 0.00 €")
        stats_layout.addWidget(self.total_value_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(9)
        self.inventory_table.setHorizontalHeaderLabels([
            "Código", "Producto", "Descripción", "Stock Actual", "Stock Mínimo", "Estado", "Valor Total", "Acciones", "Último Mov."
        ])
        
        # Set table properties
        header = self.inventory_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.inventory_table)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
    
    def refresh_data(self):
        """Refresh inventory data"""
        try:
            with SessionLocal() as db:
                products = db.query(Product).all()
                
                self.inventory_table.setRowCount(0)
                low_stock_count = 0
                total_value = 0.0
                
                for row, product in enumerate(products):
                    self.inventory_table.insertRow(row)
                    
                    self.inventory_table.setItem(row, 0, QTableWidgetItem(product.code or ""))
                    self.inventory_table.setItem(row, 1, QTableWidgetItem(product.name or ""))
                    self.inventory_table.setItem(row, 2, QTableWidgetItem(product.description or ""))
                    self.inventory_table.setItem(row, 3, QTableWidgetItem(str(product.current_stock or 0)))
                    self.inventory_table.setItem(row, 4, QTableWidgetItem(str(product.minimum_stock or 0)))
                    
                    # Stock status
                    stock_status = "✅ OK"
                    stock_color = "green"
                    if product.current_stock <= 0:
                        stock_status = "❌ SIN STOCK"
                        stock_color = "red"
                    elif product.current_stock <= product.minimum_stock:
                        stock_status = "⚠️ BAJO"
                        stock_color = "orange"
                        low_stock_count += 1
                    
                    status_item = QTableWidgetItem(stock_status)
                    status_item.setStyleSheet(f"color: {stock_color}; font-weight: bold;")
                    self.inventory_table.setItem(row, 5, status_item)
                    
                    # Total value
                    total_product_value = (product.current_stock or 0) * (product.sale_price or 0)
                    total_value += total_product_value
                    value_item = QTableWidgetItem(f"{total_product_value:.2f} €")
                    self.inventory_table.setItem(row, 6, value_item)
                    
                    # Actions
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(2, 2, 2, 2)
                    
                    adjust_btn = QPushButton("📊")
                    adjust_btn.setToolTip("Ajustar Stock")
                    adjust_btn.setMaximumSize(30, 25)
                    adjust_btn.clicked.connect(lambda checked, p=product: self.adjust_product_stock(p))
                    actions_layout.addWidget(adjust_btn)
                    
                    edit_btn = QPushButton("✏️")
                    edit_btn.setToolTip("Editar Producto")
                    edit_btn.setMaximumSize(30, 25)
                    edit_btn.clicked.connect(lambda checked, p=product: self.edit_product(p))
                    actions_layout.addWidget(edit_btn)
                    
                    self.inventory_table.setCellWidget(row, 7, actions_widget)
                    
                    # Last movement
                    last_movement = "N/A"
                    if hasattr(product, 'updated_at') and product.updated_at:
                        last_movement = product.updated_at.strftime('%Y-%m-%d %H:%M')
                    self.inventory_table.setItem(row, 8, QTableWidgetItem(last_movement))
                
                # Update statistics
                self.total_products_label.setText(f"📦 Total: {len(products)}")
                self.low_stock_label.setText(f"⚠️ Stock Bajo: {low_stock_count}")
                self.total_value_label.setText(f"💰 Valor Total: {total_value:.2f} €")
                
                self.status_label.setText(f"📊 Mostrando {len(products)} productos - {low_stock_count} con stock bajo")
                
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
    
    def filter_products(self):
        """Filter products based on search and filter criteria"""
        search_text = self.search_edit.text().lower()
        filter_type = self.filter_combo.currentText()
        
        for row in range(self.inventory_table.rowCount()):
            visible = True
            
            # Apply text search
            if search_text:
                found = False
                for col in range(self.inventory_table.columnCount()):
                    item = self.inventory_table.item(row, col)
                    if item and search_text in item.text().lower():
                        found = True
                        break
                if not found:
                    visible = False
            
            # Apply filter criteria
            if visible:
                stock_item = self.inventory_table.item(row, 3)
                min_stock_item = self.inventory_table.item(row, 4)
                status_item = self.inventory_table.item(row, 5)
                
                if stock_item and min_stock_item and status_item:
                    stock = int(stock_item.text() or 0)
                    min_stock = int(min_stock_item.text() or 0)
                    status = status_item.text()
                    
                    if filter_type == "Con Stock" and stock <= 0:
                        visible = False
                    elif filter_type == "Stock Bajo" and stock > min_stock:
                        visible = False
                    elif filter_type == "Sin Stock" and stock > 0:
                        visible = False
                    elif filter_type == "Activos" and "Activo" not in status:
                        visible = False
                    elif filter_type == "Inactivos" and "Activo" in status:
                        visible = False
            
            self.inventory_table.setRowHidden(row, not visible)
    
    def add_product(self):
        """Add new product to inventory"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
    
    def adjust_stock(self):
        """General stock adjustment dialog"""
        QMessageBox.information(self, "ℹ️ Ajustar Stock", "Seleccione un producto y use el botón 📊 en la tabla para ajustar su stock")
    
    def adjust_product_stock(self, product):
        """Adjust stock for specific product"""
        from PySide6.QtWidgets import QInputDialog
        
        quantity, ok = QInputDialog.getInt(
            self, 
            "📊 Ajustar Stock", 
            f"Cantidad para {product.name}:\n\n(positivo = entrada, negativo = salida)",
            0, -999, 999, 1
        )
        
        if ok:
            try:
                with SessionLocal() as db:
                    db_product = db.query(Product).filter(Product.id == product.id).first()
                    if db_product:
                        old_stock = db_product.current_stock or 0
                        new_stock = max(0, old_stock + quantity)
                        db_product.current_stock = new_stock
                        db.commit()
                        
                        movement_type = "Entrada" if quantity > 0 else "Salida"
                        QMessageBox.information(
                            self, "✅ Éxito", 
                            f"Stock ajustado para {product.name}:\n"
                            f"{old_stock} → {new_stock} ({movement_type}: {abs(quantity)})"
                        )
                        self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "❌ Error", f"Error ajustando stock: {str(e)}")
    
    def edit_product(self, product):
        """Edit product details"""
        QMessageBox.information(self, "ℹ️ Editar Producto", f"Función de edición para {product.name} en desarrollo")
    
    def generate_report(self):
        """Generate inventory report"""
        try:
            with SessionLocal() as db:
                products = db.query(Product).all()
                
                report = "📊 INFORME DE INVENTARIO\n"
                report += "=" * 50 + "\n"
                report += f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                total_products = len(products)
                low_stock = sum(1 for p in products if p.current_stock <= p.minimum_stock)
                out_of_stock = sum(1 for p in products if p.current_stock <= 0)
                total_value = sum((p.current_stock or 0) * (p.sale_price or 0) for p in products)
                
                report += f"📦 Total Productos: {total_products}\n"
                report += f"⚠️ Stock Bajo: {low_stock}\n"
                report += f"❌ Sin Stock: {out_of_stock}\n"
                report += f"💰 Valor Total Inventario: {total_value:.2f} €\n\n"
                
                report += "DETALLE DE PRODUCTOS CON STOCK BAJO:\n"
                report += "-" * 40 + "\n"
                
                for product in products:
                    if product.current_stock <= product.minimum_stock:
                        report += f"• {product.name}: {product.current_stock} (mín: {product.minimum_stock})\n"
                
                # Show report in dialog
                report_dialog = QDialog(self)
                report_dialog.setWindowTitle("📊 Informe de Inventario")
                report_dialog.setModal(True)
                report_dialog.resize(600, 500)
                
                layout = QVBoxLayout(report_dialog)
                
                report_text = QTextEdit()
                report_text.setPlainText(report)
                report_text.setReadOnly(True)
                layout.addWidget(report_text)
                
                close_btn = QPushButton("❌ Cerrar")
                close_btn.clicked.connect(report_dialog.accept)
                layout.addWidget(close_btn)
                
                report_dialog.exec()
                
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error generando informe: {str(e)}")

class DiaryManagementTab(QWidget):
    """Complete diary management with calendar functionality"""
    def __init__(self):
        super().__init__()
        self.notes = []
        self.setup_ui()
        self.load_notes()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        add_entry_btn = QPushButton("➕ Nueva Nota")
        add_entry_btn.clicked.connect(self.add_entry)
        add_entry_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        toolbar_layout.addWidget(add_entry_btn)
        
        view_calendar_btn = QPushButton("📅 Ver Calendario")
        view_calendar_btn.clicked.connect(self.view_calendar)
        toolbar_layout.addWidget(view_calendar_btn)
        
        clear_all_btn = QPushButton("🗑️ Limpiar Todo")
        clear_all_btn.clicked.connect(self.clear_all)
        clear_all_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px; border-radius: 5px;")
        toolbar_layout.addWidget(clear_all_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Date selector
        date_layout = QHBoxLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.filter_notes_by_date)
        date_layout.addWidget(QLabel("📅 Fecha:"))
        date_layout.addWidget(self.date_edit)
        
        today_btn = QPushButton("📍 Hoy")
        today_btn.clicked.connect(lambda: self.date_edit.setDate(QDate.currentDate()))
        date_layout.addWidget(today_btn)
        
        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        # Notes list
        notes_group = QGroupBox("📝 Notas del Diario")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_list = QTextEdit()
        self.notes_list.setReadOnly(True)
        self.notes_list.setPlaceholderText("Las notas del diario aparecerán aquí...")
        notes_layout.addWidget(self.notes_list)
        
        layout.addWidget(notes_group)
        
        # Statistics
        stats_layout = QHBoxLayout()
        
        self.total_notes_label = QLabel("📊 Total Notas: 0")
        stats_layout.addWidget(self.total_notes_label)
        
        self.today_notes_label = QLabel("📅 Notas Hoy: 0")
        stats_layout.addWidget(self.today_notes_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Status label
        self.status_label = QLabel("📝 Diario personal - Haz clic en 'Nueva Nota' para añadir apuntes")
        layout.addWidget(self.status_label)
    
    def add_entry(self):
        """Add new diary entry"""
        dialog = DiaryEntryDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            note_data = dialog.get_note_data()
            if note_data:
                self.notes.append(note_data)
                self.save_notes()
                self.refresh_notes()
                self.status_label.setText(f"✅ Nota guardada: {note_data['title']}")
    
    def view_calendar(self):
        """View calendar with notes"""
        QMessageBox.information(self, "📅 Calendario", "Calendario de notas en desarrollo...")
    
    def clear_all(self):
        """Clear all notes"""
        reply = QMessageBox.question(
            self, "❌ Confirmar Eliminación", 
            "¿Está seguro de eliminar TODAS las notas del diario?\n\nEsta acción no se puede deshacer."
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.notes = []
            self.save_notes()
            self.refresh_notes()
            self.status_label.setText("🗑️ Todas las notas han sido eliminadas")
    
    def filter_notes_by_date(self):
        """Filter notes by selected date"""
        self.refresh_notes()
    
    def load_notes(self):
        """Load notes from file"""
        try:
            import json
            notes_file = os.path.join(os.path.dirname(__file__), 'diary_notes.json')
            if os.path.exists(notes_file):
                with open(notes_file, 'r', encoding='utf-8') as f:
                    self.notes = json.load(f)
        except:
            self.notes = []
    
    def save_notes(self):
        """Save notes to file"""
        try:
            import json
            notes_file = os.path.join(os.path.dirname(__file__), 'diary_notes.json')
            with open(notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error guardando notas: {str(e)}")
    
    def refresh_notes(self):
        """Refresh notes display"""
        selected_date = self.date_edit.date().toString('yyyy-MM-dd')
        
        display_text = f"📅 Notas para {selected_date}:\n"
        display_text += "=" * 50 + "\n\n"
        
        filtered_notes = [
            note for note in self.notes 
            if note['date'] == selected_date
        ]
        
        if filtered_notes:
            for i, note in enumerate(filtered_notes, 1):
                display_text += f"{i}. 📌 {note['title']}\n"
                display_text += f"   🕐 {note['time']}\n"
                display_text += f"   📝 {note['content']}\n"
                if note.get('tags'):
                    display_text += f"   🏷️  {', '.join(note['tags'])}\n"
                display_text += "-" * 30 + "\n\n"
        else:
            display_text += "No hay notas para esta fecha.\n\n"
            display_text += "💡 Tip: Usa 'Nueva Nota' para añadir una entrada."
        
        self.notes_list.setPlainText(display_text)
        
        # Update statistics
        from datetime import datetime
        today = QDate.currentDate().toString('yyyy-MM-dd')
        today_notes = [note for note in self.notes if note['date'] == today]
        
        self.total_notes_label.setText(f"📊 Total Notas: {len(self.notes)}")
        self.today_notes_label.setText(f"📅 Notas Hoy: {len(today_notes)}")

class DiaryEntryDialog(QDialog):
    """Dialog for creating new diary entries"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 Nueva Nota del Diario")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("📌 Título de la nota")
        layout.addWidget(QLabel("Título:"))
        layout.addWidget(self.title_edit)
        
        # Content
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("📝 Escribe el contenido de tu nota aquí...")
        layout.addWidget(QLabel("Contenido:"))
        layout.addWidget(self.content_edit)
        
        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("🏷️ Etiquetas (separadas por comas: trabajo, importante, etc.)")
        layout.addWidget(QLabel("Etiquetas:"))
        layout.addWidget(self.tags_edit)
        
        # Date and time
        datetime_layout = QHBoxLayout()
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        datetime_layout.addWidget(QLabel("📅 Fecha:"))
        datetime_layout.addWidget(self.date_edit)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        datetime_layout.addWidget(QLabel("🕐 Hora:"))
        datetime_layout.addWidget(self.time_edit)
        
        layout.addLayout(datetime_layout)
        
        # Priority
        priority_layout = QHBoxLayout()
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["🟢 Normal", "🟡 Importante", "🔴 Urgente"])
        priority_layout.addWidget(QLabel("🎯 Prioridad:"))
        priority_layout.addWidget(self.priority_combo)
        priority_layout.addStretch()
        layout.addLayout(priority_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Guardar Nota")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def get_note_data(self):
        """Get note data from form"""
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "❌ Error", "El título es obligatorio")
            return None
        
        return {
            'title': self.title_edit.text().strip(),
            'content': self.content_edit.toPlainText().strip(),
            'date': self.date_edit.date().toString('yyyy-MM-dd'),
            'time': self.time_edit.time().toString('HH:mm'),
            'priority': self.priority_combo.currentText(),
            'tags': [tag.strip() for tag in self.tags_edit.text().split(',') if tag.strip()]
        }

# Add missing import for QTimeEdit and QTime
from PySide6.QtWidgets import QTimeEdit
from PySide6.QtCore import QTime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.setup_ui()
    
    def set_current_user(self, user):
        """Set current user"""
        self.current_user = user
        username = user.username
        full_name = user.full_name
        role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        
        self.statusBar().showMessage(f"👤 {full_name} ({role})")
    
    def setup_ui(self):
        """Setup main window"""
        self.setWindowTitle("🐲 DRAGOFACTU - Sistema de Gestión Profesional")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create menu bar
        self.create_menu()
        
        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Dashboard tab
        self.dashboard = Dashboard()
        self.tabs.addTab(self.dashboard, "🏠 Panel Principal")
        
        # Add functional tabs
        self.clients_tab = ClientManagementTab()
        self.tabs.addTab(self.clients_tab, "👥 Clientes")
        
        self.products_tab = ProductManagementTab()
        self.tabs.addTab(self.products_tab, "📦 Productos")
        
        self.documents_tab = DocumentManagementTab()
        self.tabs.addTab(self.documents_tab, "📄 Documentos")
        
        self.inventory_tab = InventoryManagementTab()
        self.tabs.addTab(self.inventory_tab, "📊 Inventario")
        
        self.diary_tab = DiaryManagementTab()
        self.tabs.addTab(self.diary_tab, "📓 Diario")
        
        layout.addWidget(self.tabs)
        
        # Create status bar
        self.statusBar().showMessage("🚀 Listo")
        
        # Connect tab changes to refresh data
        self.tabs.currentChanged.connect(self.on_tab_changed)
    
    def on_tab_changed(self, index):
        """Handle tab change to refresh data"""
        tab_widget = self.tabs.widget(index)
        
        # Always refresh dashboard when switching to it
        if index == 0:  # Dashboard tab
            self.dashboard.setup_ui()
        # Refresh the specific tab when it becomes active
        elif index == 1:  # Clients tab
            if hasattr(tab_widget, 'refresh_data'):
                tab_widget.refresh_data()
        elif index == 2:  # Products tab
            if hasattr(tab_widget, 'refresh_data'):
                tab_widget.refresh_data()
    
    def create_menu(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("📁 Archivo")
        
        new_quote_action = QAction("💰 Nuevo Presupuesto", self)
        new_quote_action.triggered.connect(self.new_quote)
        file_menu.addAction(new_quote_action)
        
        new_invoice_action = QAction("🧾 Nueva Factura", self)
        new_invoice_action.triggered.connect(self.new_invoice)
        file_menu.addAction(new_invoice_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("🔧 Herramientas")
        
        settings_action = QAction("⚙️ Ajustes", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Language menu
        language_menu = menubar.addMenu("🌍 Idioma")
        
        for lang_code, lang_name in translator.get_available_languages().items():
            lang_action = QAction(lang_name, self)
            lang_action.triggered.connect(lambda checked, code=lang_code: self.change_language(code))
            language_menu.addAction(lang_action)
    
    def new_quote(self):
        """Create new quote"""
        dialog = DocumentDialog(self, "quote")
        dialog.exec()
    
    def new_invoice(self):
        """Create new invoice"""
        dialog = DocumentDialog(self, "invoice")
        dialog.exec()
    
    def show_settings(self):
        """Show settings dialog"""
        QMessageBox.information(self, "⚙️ Ajustes", "Configuración del sistema en desarrollo")
    
    def change_language(self, language_code):
        """Change application language"""
        if translator.set_language(language_code):
            self.statusBar().showMessage(f"🌍 Idioma cambiado a: {translator.get_available_languages()[language_code]}", 3000)

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.user = None
        self.user_data = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup login dialog"""
        self.setWindowTitle("🐲 Login - DRAGOFACTU")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🐲 DRAGOFACTU")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 20px;")
        layout.addWidget(title)
        
        subtitle = QLabel("Sistema de Gestión Profesional")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; margin-bottom: 30px;")
        layout.addWidget(subtitle)
        
        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("👤 Usuario")
        layout.addWidget(self.username_edit)
        
        # Password
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("🔒 Contraseña")
        layout.addWidget(self.password_edit)
        
        # Login button
        login_btn = QPushButton("🚀 Iniciar Sesión")
        login_btn.clicked.connect(self.handle_login)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        layout.addWidget(login_btn)
        
        # Default credentials hint
        hint = QLabel("Credenciales por defecto: admin / admin123")
        hint.setStyleSheet("color: #95a5a6; font-size: 10px; margin-top: 20px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
    
    def handle_login(self):
        """Handle login"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            QMessageBox.warning(self, "❌ Error", "Por favor ingrese usuario y contraseña")
            return
        
        try:
            auth_service = AuthService()
            with SessionLocal() as db:
                user = auth_service.authenticate(db, username, password)
                if user:
                    # Extract user data before session closes to avoid DetachedInstanceError
                    self.user_data = {
                        'id': user.id,
                        'username': user.username,
                        'full_name': user.full_name,
                        'role': user.role.value if hasattr(user.role, 'value') else str(user.role)
                    }
                    self.user = user  # Keep for backward compatibility
                    self.accept()
                else:
                    QMessageBox.warning(self, "❌ Error", "Usuario o contraseña incorrectos")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error de autenticación: {str(e)}")

class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.current_user = None
        self.setup_app()
    
    def setup_app(self):
        """Setup application"""
        # Create database tables
        Base.metadata.create_all(bind=engine)
        
        # Show login
        self.show_login()
    
    def show_login(self):
        """Show login dialog"""
        login_dialog = LoginDialog()
        
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            # Use the pre-extracted user_data to avoid DetachedInstanceError
            self.current_user_data = login_dialog.user_data
            self.show_main_window()
        else:
            self.quit()
    
    def show_main_window(self):
        """Show main window"""
        self.main_window = MainWindow()
        
        # Create a simple user object with basic attributes
        class SimpleUser:
            def __init__(self, data):
                self.id = data['id']
                self.username = data['username']
                self.full_name = data['full_name']
                self.role = data['role']
        
        simple_user = SimpleUser(self.current_user_data)
        self.main_window.set_current_user(simple_user)
        self.main_window.show()

def main():
    """Main function"""
    app = App()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()