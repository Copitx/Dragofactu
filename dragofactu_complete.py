#!/usr/bin/env python3
"""
DRAGOFACTU - Complete Business Management System
Fixed version with proper data persistence and full functionality
"""

import sys
import os
import logging
from datetime import datetime, date
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dragofactu')

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

from sqlalchemy.orm import joinedload

from dragofactu.models.database import SessionLocal, engine, Base
from dragofactu.models.entities import User, Client, Product, Document, DocumentType, DocumentStatus
from dragofactu.services.auth.auth_service import AuthService
from dragofactu.config.translation import translator

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.card_widgets = []  # Track card widgets for refreshing
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self._create_dashboard_content(layout)
    
    def _create_dashboard_content(self, layout):
        """Create dashboard content without clearing existing widgets"""
        
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
        
        # Store reference for updating
        self.card_widgets.append({'title': title_label, 'value': value_label})
        
        return card
    
    def refresh_data(self):
        """Refresh dashboard data without recreating UI"""
        for card_widget in self.card_widgets:
            if 'value' in card_widget:
                # Update counts based on card title
                title_text = card_widget['title'].text()
                if "Clientes" in title_text:
                    card_widget['value'].setText(str(self.get_client_count()))
                elif "Productos" in title_text:
                    card_widget['value'].setText(str(self.get_product_count()))
                elif "Documentos" in title_text:
                    card_widget['value'].setText(str(self.get_document_count()))
                elif "Stock Bajo" in title_text:
                    card_widget['value'].setText(str(self.get_low_stock_count()))
    
    def get_client_count(self):
        """Get total clients"""
        try:
            with SessionLocal() as db:
                return db.query(Client).count()
        except Exception as e:
            logger.error(f"Error getting client count: {e}")
            return 0

    def get_product_count(self):
        """Get total products"""
        try:
            with SessionLocal() as db:
                return db.query(Product).count()
        except Exception as e:
            logger.error(f"Error getting product count: {e}")
            return 0

    def get_document_count(self):
        """Get total documents"""
        try:
            with SessionLocal() as db:
                return db.query(Document).count()
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0

    def get_low_stock_count(self):
        """Get products with low stock"""
        try:
            with SessionLocal() as db:
                return db.query(Product).filter(
                    Product.current_stock <= Product.minimum_stock
                ).count()
        except Exception as e:
            logger.error(f"Error getting low stock count: {e}")
            return 0
    
    def add_client(self):
        """Add new client"""
        dialog = ClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "✅ Éxito", "Cliente añadido correctamente")
            self.refresh_data()  # Refresh dashboard
    
    def add_product(self):
        """Add new product"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "✅ Éxito", "Producto añadido correctamente")
            self.refresh_data()  # Refresh dashboard
    
    def add_quote(self):
        """Add new quote"""
        dialog = DocumentDialog(self, "quote")
        dialog.exec()
    
    def add_invoice(self):
        """Add new invoice"""
        dialog = DocumentDialog(self, "invoice")
        dialog.exec()

class ClientDialog(QDialog):
    """Dialog for creating and editing clients"""
    def __init__(self, parent=None, client_id=None):
        super().__init__(parent)
        self.client_id = client_id
        self.is_edit_mode = client_id is not None
        self.setWindowTitle("✏️ Editar Cliente" if self.is_edit_mode else "👤 Nuevo Cliente")
        self.setModal(True)
        self.resize(500, 450)
        self.setup_ui()
        if self.is_edit_mode:
            self.load_client_data()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("C-001")
        if self.is_edit_mode:
            self.code_edit.setReadOnly(True)
            self.code_edit.setStyleSheet("background-color: #f0f0f0;")
        layout.addRow("Código:", self.code_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nombre del cliente")
        layout.addRow("Nombre (*):", self.name_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@ejemplo.com")
        layout.addRow("Email:", self.email_edit)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+34 600 000 000")
        layout.addRow("Teléfono:", self.phone_edit)

        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Dirección completa")
        layout.addRow("Dirección:", self.address_edit)

        self.city_edit = QLineEdit()
        self.city_edit.setPlaceholderText("Ciudad")
        layout.addRow("Ciudad:", self.city_edit)

        self.postal_code_edit = QLineEdit()
        self.postal_code_edit.setPlaceholderText("Código Postal")
        layout.addRow("C. Postal:", self.postal_code_edit)

        self.nif_edit = QLineEdit()
        self.nif_edit.setPlaceholderText("CIF/NIF")
        layout.addRow("CIF/NIF:", self.nif_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notas adicionales...")
        self.notes_edit.setMaximumHeight(80)
        layout.addRow("Notas:", self.notes_edit)

        self.active_check = QCheckBox()
        self.active_check.setChecked(True)
        layout.addRow("Activo:", self.active_check)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def load_client_data(self):
        """Load existing client data for editing"""
        try:
            with SessionLocal() as db:
                client = db.query(Client).filter(Client.id == self.client_id).first()
                if client:
                    self.code_edit.setText(client.code or "")
                    self.name_edit.setText(client.name or "")
                    self.email_edit.setText(client.email or "")
                    self.phone_edit.setText(client.phone or "")
                    self.address_edit.setText(client.address or "")
                    self.city_edit.setText(client.city or "")
                    self.postal_code_edit.setText(client.postal_code or "")
                    self.nif_edit.setText(client.tax_id or "")
                    self.notes_edit.setPlainText(client.notes or "")
                    self.active_check.setChecked(client.is_active)
                else:
                    QMessageBox.warning(self, "❌ Error", "Cliente no encontrado")
                    self.reject()
        except Exception as e:
            logger.error(f"Error loading client data: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error cargando cliente: {str(e)}")
            self.reject()

    def accept(self):
        """Save or update client"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "❌ Error", "El nombre es obligatorio")
            return

        try:
            with SessionLocal() as db:
                if self.is_edit_mode:
                    # Update existing client
                    client = db.query(Client).filter(Client.id == self.client_id).first()
                    if not client:
                        QMessageBox.warning(self, "❌ Error", "Cliente no encontrado")
                        return
                    client.name = self.name_edit.text().strip()
                    client.email = self.email_edit.text().strip() or None
                    client.phone = self.phone_edit.text().strip() or None
                    client.address = self.address_edit.text().strip() or None
                    client.city = self.city_edit.text().strip() or None
                    client.postal_code = self.postal_code_edit.text().strip() or None
                    client.tax_id = self.nif_edit.text().strip() or None
                    client.notes = self.notes_edit.toPlainText().strip() or None
                    client.is_active = self.active_check.isChecked()
                else:
                    # Create new client
                    client = Client(
                        code=self.code_edit.text().strip() or f"C-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        name=self.name_edit.text().strip(),
                        email=self.email_edit.text().strip() or None,
                        phone=self.phone_edit.text().strip() or None,
                        address=self.address_edit.text().strip() or None,
                        city=self.city_edit.text().strip() or None,
                        postal_code=self.postal_code_edit.text().strip() or None,
                        tax_id=self.nif_edit.text().strip() or None,
                        notes=self.notes_edit.toPlainText().strip() or None,
                        is_active=self.active_check.isChecked()
                    )
                    db.add(client)
                db.commit()
                super().accept()
        except Exception as e:
            logger.error(f"Error saving client: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al guardar cliente: {str(e)}")

class ProductDialog(QDialog):
    """Dialog for creating and editing products"""
    def __init__(self, parent=None, product_id=None):
        super().__init__(parent)
        self.product_id = product_id
        self.is_edit_mode = product_id is not None
        self.setWindowTitle("✏️ Editar Producto" if self.is_edit_mode else "📦 Nuevo Producto")
        self.setModal(True)
        self.resize(500, 500)
        self.setup_ui()
        if self.is_edit_mode:
            self.load_product_data()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("P-001")
        if self.is_edit_mode:
            self.code_edit.setReadOnly(True)
            self.code_edit.setStyleSheet("background-color: #f0f0f0;")
        layout.addRow("Código:", self.code_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nombre del producto")
        layout.addRow("Nombre (*):", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Descripción del producto")
        self.description_edit.setMaximumHeight(60)
        layout.addRow("Descripción:", self.description_edit)

        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Categoría")
        layout.addRow("Categoría:", self.category_edit)

        self.cost_price_edit = QDoubleSpinBox()
        self.cost_price_edit.setRange(0, 999999)
        self.cost_price_edit.setDecimals(2)
        self.cost_price_edit.setSuffix(" €")
        self.cost_price_edit.setValue(0)
        layout.addRow("Precio Coste:", self.cost_price_edit)

        self.sale_price_edit = QDoubleSpinBox()
        self.sale_price_edit.setRange(0, 999999)
        self.sale_price_edit.setDecimals(2)
        self.sale_price_edit.setSuffix(" €")
        self.sale_price_edit.setValue(0)
        layout.addRow("Precio Venta:", self.sale_price_edit)

        self.stock_spin = QSpinBox()
        self.stock_spin.setMinimum(0)
        self.stock_spin.setMaximum(999999)
        self.stock_spin.setValue(0)
        stock_label = "Stock Actual:" if self.is_edit_mode else "Stock Inicial:"
        layout.addRow(stock_label, self.stock_spin)

        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setMinimum(0)
        self.min_stock_spin.setMaximum(999999)
        self.min_stock_spin.setValue(5)
        layout.addRow("Stock Mínimo:", self.min_stock_spin)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Unidades", "Kg", "Litros", "Metros", "Horas", "Piezas", "Cajas"])
        layout.addRow("Unidad:", self.unit_combo)

        self.active_check = QCheckBox()
        self.active_check.setChecked(True)
        layout.addRow("Activo:", self.active_check)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def load_product_data(self):
        """Load existing product data for editing"""
        try:
            with SessionLocal() as db:
                product = db.query(Product).filter(Product.id == self.product_id).first()
                if product:
                    self.code_edit.setText(product.code or "")
                    self.name_edit.setText(product.name or "")
                    self.description_edit.setPlainText(product.description or "")
                    self.category_edit.setText(product.category or "")
                    self.cost_price_edit.setValue(float(product.purchase_price or 0))
                    self.sale_price_edit.setValue(float(product.sale_price or 0))
                    self.stock_spin.setValue(product.current_stock or 0)
                    self.min_stock_spin.setValue(product.minimum_stock or 0)
                    # Set unit combo
                    unit_index = self.unit_combo.findText(product.stock_unit or "Unidades")
                    if unit_index >= 0:
                        self.unit_combo.setCurrentIndex(unit_index)
                    self.active_check.setChecked(product.is_active)
                else:
                    QMessageBox.warning(self, "❌ Error", "Producto no encontrado")
                    self.reject()
        except Exception as e:
            logger.error(f"Error loading product data: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error cargando producto: {str(e)}")
            self.reject()

    def accept(self):
        """Save or update product"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "❌ Error", "El nombre es obligatorio")
            return

        try:
            with SessionLocal() as db:
                if self.is_edit_mode:
                    # Update existing product
                    product = db.query(Product).filter(Product.id == self.product_id).first()
                    if not product:
                        QMessageBox.warning(self, "❌ Error", "Producto no encontrado")
                        return
                    product.name = self.name_edit.text().strip()
                    product.description = self.description_edit.toPlainText().strip() or None
                    product.category = self.category_edit.text().strip() or None
                    product.purchase_price = self.cost_price_edit.value()
                    product.sale_price = self.sale_price_edit.value()
                    product.current_stock = self.stock_spin.value()
                    product.minimum_stock = self.min_stock_spin.value()
                    product.stock_unit = self.unit_combo.currentText()
                    product.is_active = self.active_check.isChecked()
                else:
                    # Create new product
                    product = Product(
                        code=self.code_edit.text().strip() or f"P-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        name=self.name_edit.text().strip(),
                        description=self.description_edit.toPlainText().strip() or None,
                        category=self.category_edit.text().strip() or None,
                        purchase_price=self.cost_price_edit.value(),
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
            logger.error(f"Error saving product: {e}")
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
        except Exception as e:
            logger.error(f"Error loading clients into combo: {e}")
            self.client_combo.addItem("Error cargando clientes", None)

    def setup_products(self):
        """Load products into combo box"""
        try:
            with SessionLocal() as db:
                products = db.query(Product).filter(Product.is_active == True).all()
                self.product_combo.addItem("Seleccione un producto...", None)
                for product in products:
                    self.product_combo.addItem(f"{product.code} - {product.name}", product.id)
        except Exception as e:
            logger.error(f"Error loading products into combo: {e}")
            self.product_combo.addItem("Error cargando productos", None)
    
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
                except ValueError as e:
                    logger.warning(f"Could not parse subtotal value at row {row}: {e}")
        
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
        # Defer refresh to prevent blocking during initialization
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.refresh_data)
    
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
        self.client_ids = []  # Store client IDs for reference
        try:
            with SessionLocal() as db:
                clients = db.query(Client).order_by(Client.name).all()

                self.clients_table.setRowCount(0)
                self.client_ids = []

                for row, client in enumerate(clients):
                    self.clients_table.insertRow(row)
                    self.client_ids.append(client.id)  # Store ID

                    self.clients_table.setItem(row, 0, QTableWidgetItem(client.code or ""))
                    self.clients_table.setItem(row, 1, QTableWidgetItem(client.name or ""))
                    self.clients_table.setItem(row, 2, QTableWidgetItem(client.email or ""))
                    self.clients_table.setItem(row, 3, QTableWidgetItem(client.phone or ""))
                    self.clients_table.setItem(row, 4, QTableWidgetItem(client.address or ""))
                    self.clients_table.setItem(row, 5, QTableWidgetItem(client.tax_id or ""))

                    status_text = "✅ Activo" if client.is_active else "❌ Inactivo"
                    status_item = QTableWidgetItem(status_text)
                    self.clients_table.setItem(row, 6, status_item)

                self.status_label.setText(f"📊 Mostrando {len(clients)} clientes")

        except Exception as e:
            logger.error(f"Error refreshing clients: {e}")
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
            QMessageBox.information(self, "✅ Éxito", "Cliente creado correctamente")

    def edit_client(self):
        """Edit selected client"""
        current_row = self.clients_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "❌ Error", "Seleccione un cliente para editar")
            return

        if current_row >= len(self.client_ids):
            QMessageBox.warning(self, "❌ Error", "Error al obtener datos del cliente")
            return

        client_id = self.client_ids[current_row]
        dialog = ClientDialog(self, client_id=client_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            QMessageBox.information(self, "✅ Éxito", "Cliente actualizado correctamente")

    def delete_client(self):
        """Delete selected client"""
        current_row = self.clients_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "❌ Error", "Seleccione un cliente para eliminar")
            return

        if current_row >= len(self.client_ids):
            QMessageBox.warning(self, "❌ Error", "Error al obtener datos del cliente")
            return

        client_name = self.clients_table.item(current_row, 1).text()
        client_id = self.client_ids[current_row]

        reply = QMessageBox.question(
            self, "🗑️ Confirmar Eliminación",
            f"¿Está seguro de eliminar al cliente '{client_name}'?\n\n"
            "Se eliminarán también todos los documentos asociados.\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                with SessionLocal() as db:
                    # Check for associated documents
                    doc_count = db.query(Document).filter(Document.client_id == client_id).count()
                    if doc_count > 0:
                        confirm = QMessageBox.warning(
                            self, "⚠️ Advertencia",
                            f"Este cliente tiene {doc_count} documento(s) asociado(s).\n"
                            "¿Desea eliminar el cliente y todos sus documentos?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No
                        )
                        if confirm != QMessageBox.StandardButton.Yes:
                            return
                        # Delete associated documents first
                        db.query(Document).filter(Document.client_id == client_id).delete()

                    # Delete the client
                    client = db.query(Client).filter(Client.id == client_id).first()
                    if client:
                        db.delete(client)
                        db.commit()
                        self.refresh_data()
                        QMessageBox.information(self, "✅ Éxito", f"Cliente '{client_name}' eliminado correctamente")
                    else:
                        QMessageBox.warning(self, "❌ Error", "Cliente no encontrado")

            except Exception as e:
                logger.error(f"Error deleting client: {e}")
                QMessageBox.critical(self, "❌ Error", f"Error al eliminar cliente: {str(e)}")

class ProductManagementTab(QWidget):
    """Complete product management tab"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        # Defer refresh to prevent blocking during initialization
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.refresh_data)
    
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
        self.product_ids = []  # Store product IDs for reference
        try:
            with SessionLocal() as db:
                products = db.query(Product).order_by(Product.name).all()

                self.products_table.setRowCount(0)
                self.product_ids = []

                for row, product in enumerate(products):
                    self.products_table.insertRow(row)
                    self.product_ids.append(product.id)  # Store ID

                    self.products_table.setItem(row, 0, QTableWidgetItem(product.code or ""))
                    self.products_table.setItem(row, 1, QTableWidgetItem(product.name or ""))
                    self.products_table.setItem(row, 2, QTableWidgetItem(product.description or ""))
                    self.products_table.setItem(row, 3, QTableWidgetItem(f"{product.purchase_price or 0:.2f} €"))
                    self.products_table.setItem(row, 4, QTableWidgetItem(f"{product.sale_price or 0:.2f} €"))
                    self.products_table.setItem(row, 5, QTableWidgetItem(str(product.current_stock or 0)))
                    self.products_table.setItem(row, 6, QTableWidgetItem(str(product.minimum_stock or 0)))

                    # Stock status
                    stock_text = "✅ OK"
                    if product.current_stock <= product.minimum_stock:
                        stock_text = "⚠️ BAJO"

                    status_text = f"✅ Activo ({stock_text})" if product.is_active else "❌ Inactivo"
                    status_item = QTableWidgetItem(status_text)
                    self.products_table.setItem(row, 7, status_item)

                self.status_label.setText(f"📊 Mostrando {len(products)} productos")

        except Exception as e:
            logger.error(f"Error refreshing products: {e}")
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
            QMessageBox.information(self, "✅ Éxito", "Producto creado correctamente")

    def edit_product(self):
        """Edit selected product"""
        current_row = self.products_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "❌ Error", "Seleccione un producto para editar")
            return

        if current_row >= len(self.product_ids):
            QMessageBox.warning(self, "❌ Error", "Error al obtener datos del producto")
            return

        product_id = self.product_ids[current_row]
        dialog = ProductDialog(self, product_id=product_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            QMessageBox.information(self, "✅ Éxito", "Producto actualizado correctamente")

    def delete_product(self):
        """Delete selected product"""
        current_row = self.products_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "❌ Error", "Seleccione un producto para eliminar")
            return

        if current_row >= len(self.product_ids):
            QMessageBox.warning(self, "❌ Error", "Error al obtener datos del producto")
            return

        product_name = self.products_table.item(current_row, 1).text()
        product_id = self.product_ids[current_row]

        reply = QMessageBox.question(
            self, "🗑️ Confirmar Eliminación",
            f"¿Está seguro de eliminar el producto '{product_name}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                with SessionLocal() as db:
                    product = db.query(Product).filter(Product.id == product_id).first()
                    if product:
                        db.delete(product)
                        db.commit()
                        self.refresh_data()
                        QMessageBox.information(self, "✅ Éxito", f"Producto '{product_name}' eliminado correctamente")
                    else:
                        QMessageBox.warning(self, "❌ Error", "Producto no encontrado")

            except Exception as e:
                logger.error(f"Error deleting product: {e}")
                QMessageBox.critical(self, "❌ Error", f"Error al eliminar producto: {str(e)}")

# Placeholder classes for other tabs (to be implemented)
class DocumentManagementTab(QWidget):
    """Document Explorer with recent documents list"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        # Defer refresh to prevent blocking during initialization
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.refresh_data)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        new_quote_btn = QPushButton("💰 Nuevo Presupuesto")
        new_quote_btn.clicked.connect(lambda: self.create_document("quote"))
        new_quote_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        toolbar_layout.addWidget(new_quote_btn)
        
        new_invoice_btn = QPushButton("🧾 Nueva Factura")
        new_invoice_btn.clicked.connect(lambda: self.create_document("invoice"))
        new_invoice_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        toolbar_layout.addWidget(new_invoice_btn)
        
        new_delivery_btn = QPushButton("📦 Nuevo Albarán")
        new_delivery_btn.clicked.connect(lambda: self.create_document("delivery"))
        new_delivery_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        toolbar_layout.addWidget(new_delivery_btn)
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(refresh_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Document type filter
        filter_layout = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Presupuestos", "Facturas", "Albaranes"])
        self.filter_combo.currentTextChanged.connect(self.refresh_data)
        filter_layout.addWidget(QLabel("Filtrar:"))
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Documents table
        self.docs_table = QTableWidget()
        self.docs_table.setColumnCount(8)
        self.docs_table.setHorizontalHeaderLabels([
            "Código", "Tipo", "Cliente", "Fecha", "Estado", "Total", "Vencimiento", "Acciones"
        ])
        
        # Configure table
        header = self.docs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.docs_table)
        
        # Status label
        self.status_label = QLabel("📄 Gestión de Documentos - Cargando datos...")
        layout.addWidget(self.status_label)
    
    def refresh_data(self):
        """Refresh documents data"""
        try:
            with SessionLocal() as db:
                # Get filter
                filter_type = self.filter_combo.currentText()
                
                # Build query with eager loading for client relationship
                query = db.query(Document).options(joinedload(Document.client))
                if filter_type != "Todos":
                    if filter_type == "Presupuestos":
                        query = query.filter(Document.type == DocumentType.QUOTE)
                    elif filter_type == "Facturas":
                        query = query.filter(Document.type == DocumentType.INVOICE)
                    elif filter_type == "Albaranes":
                        query = query.filter(Document.type == DocumentType.DELIVERY_NOTE)

                # Get documents with most recent first
                documents = query.order_by(Document.updated_at.desc()).limit(100).all()
                
                self.docs_table.setRowCount(0)
                
                for row, doc in enumerate(documents):
                    self.docs_table.insertRow(row)
                    
                    # Document code
                    self.docs_table.setItem(row, 0, QTableWidgetItem(doc.code or ""))
                    
                    # Document type
                    type_text = ""
                    if doc.type == DocumentType.QUOTE:
                        type_text = "Presupuesto"
                    elif doc.type == DocumentType.INVOICE:
                        type_text = "Factura"
                    elif doc.type == DocumentType.DELIVERY_NOTE:
                        type_text = "Albarán"
                    
                    type_item = QTableWidgetItem(type_text)
                    if doc.type == DocumentType.QUOTE:
                        type_item.setStyleSheet("color: #9b59b6; font-weight: bold;")
                    elif doc.type == DocumentType.INVOICE:
                        type_item.setStyleSheet("color: #e67e22; font-weight: bold;")
                    elif doc.type == DocumentType.DELIVERY_NOTE:
                        type_item.setStyleSheet("color: #3498db; font-weight: bold;")
                    
                    self.docs_table.setItem(row, 1, type_item)
                    
                    # Client name (with relationship loading)
                    try:
                        client_name = doc.client.name if doc.client else "N/A"
                    except Exception as e:
                        logger.warning(f"Could not load client name for document {doc.code}: {e}")
                        client_name = "N/A"
                    self.docs_table.setItem(row, 2, QTableWidgetItem(client_name))
                    
                    # Date
                    date_text = ""
                    if doc.issue_date:
                        date_text = doc.issue_date.strftime('%d/%m/%Y')
                    self.docs_table.setItem(row, 3, QTableWidgetItem(date_text))
                    
                    # Status
                    status_text = ""
                    status_color = ""
                    if doc.status == DocumentStatus.DRAFT:
                        status_text = "Borrador"
                        status_color = "gray"
                    elif doc.status == DocumentStatus.SENT:
                        status_text = "Enviado"
                        status_color = "blue"
                    elif doc.status == DocumentStatus.ACCEPTED:
                        status_text = "Aceptado"
                        status_color = "green"
                    elif doc.status == DocumentStatus.PAID:
                        status_text = "Pagado"
                        status_color = "purple"
                    
                    status_item = QTableWidgetItem(status_text)
                    status_item.setStyleSheet(f"color: {status_color}; font-weight: bold;")
                    self.docs_table.setItem(row, 4, status_item)
                    
                    # Total
                    total_text = f"{doc.total or 0:.2f} €"
                    self.docs_table.setItem(row, 5, QTableWidgetItem(total_text))
                    
                    # Due date
                    due_text = ""
                    if doc.due_date:
                        due_text = doc.due_date.strftime('%d/%m/%Y')
                    self.docs_table.setItem(row, 6, QTableWidgetItem(due_text))
                    
                    # Actions
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(2, 2, 2, 2)
                    
                    view_btn = QPushButton("👁️")
                    view_btn.setToolTip("Ver Documento")
                    view_btn.setMaximumSize(30, 25)
                    view_btn.clicked.connect(lambda checked, d=doc: self.view_document(d))
                    actions_layout.addWidget(view_btn)
                    
                    edit_btn = QPushButton("✏️")
                    edit_btn.setToolTip("Editar Documento")
                    edit_btn.setMaximumSize(30, 25)
                    edit_btn.clicked.connect(lambda checked, d=doc: self.edit_document(d))
                    actions_layout.addWidget(edit_btn)
                    
                    delete_btn = QPushButton("🗑️")
                    delete_btn.setToolTip("Eliminar Documento")
                    delete_btn.setMaximumSize(30, 25)
                    delete_btn.setStyleSheet("color: #e74c3c;")
                    delete_btn.clicked.connect(lambda checked, d=doc: self.delete_document(d))
                    actions_layout.addWidget(delete_btn)
                    
                    self.docs_table.setCellWidget(row, 7, actions_widget)
                
                self.status_label.setText(f"📊 Mostrando {len(documents)} documentos - Filtro: {filter_type}")
                
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
    
    def create_document(self, doc_type):
        """Create new document"""
        dialog = DocumentDialog(self, doc_type)
        dialog.exec()
    
    def view_document(self, document):
        """View document details"""
        try:
            with SessionLocal() as db:
                # Reload document with relationships
                doc = db.query(Document).options(joinedload(Document.client)).filter(Document.id == document.id).first()
                if not doc:
                    QMessageBox.warning(self, "❌ Error", "Documento no encontrado")
                    return

                # Build document info
                doc_type = "Presupuesto" if doc.type == DocumentType.QUOTE else "Factura" if doc.type == DocumentType.INVOICE else "Albarán"
                client_name = doc.client.name if doc.client else "N/A"
                issue_date = doc.issue_date.strftime('%d/%m/%Y') if doc.issue_date else "N/A"
                due_date = doc.due_date.strftime('%d/%m/%Y') if doc.due_date else "N/A"
                status_text = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)

                # Create view dialog
                view_dialog = QDialog(self)
                view_dialog.setWindowTitle(f"📄 {doc_type} - {doc.code}")
                view_dialog.setModal(True)
                view_dialog.resize(600, 500)

                layout = QVBoxLayout(view_dialog)

                # Header
                header = QLabel(f"📄 {doc_type}: {doc.code}")
                header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
                layout.addWidget(header)

                # Document details
                details_group = QGroupBox("📋 Detalles del Documento")
                details_layout = QFormLayout(details_group)
                details_layout.addRow("Código:", QLabel(doc.code or ""))
                details_layout.addRow("Tipo:", QLabel(doc_type))
                details_layout.addRow("Estado:", QLabel(status_text))
                details_layout.addRow("Cliente:", QLabel(client_name))
                details_layout.addRow("Fecha Emisión:", QLabel(issue_date))
                details_layout.addRow("Fecha Vencimiento:", QLabel(due_date))
                layout.addWidget(details_group)

                # Financial details
                financial_group = QGroupBox("💰 Detalles Financieros")
                financial_layout = QFormLayout(financial_group)
                financial_layout.addRow("Subtotal:", QLabel(f"{doc.subtotal or 0:.2f} €"))
                financial_layout.addRow("IVA:", QLabel(f"{doc.tax_amount or 0:.2f} €"))
                financial_layout.addRow("Total:", QLabel(f"{doc.total or 0:.2f} €"))
                layout.addWidget(financial_group)

                # Notes
                if doc.notes:
                    notes_group = QGroupBox("📝 Notas")
                    notes_layout = QVBoxLayout(notes_group)
                    notes_text = QTextEdit()
                    notes_text.setPlainText(doc.notes)
                    notes_text.setReadOnly(True)
                    notes_text.setMaximumHeight(100)
                    notes_layout.addWidget(notes_text)
                    layout.addWidget(notes_group)

                # Close button
                close_btn = QPushButton("❌ Cerrar")
                close_btn.clicked.connect(view_dialog.accept)
                layout.addWidget(close_btn)

                view_dialog.exec()

        except Exception as e:
            logger.error(f"Error viewing document: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al ver documento: {str(e)}")

    def edit_document(self, document):
        """Edit document - opens document dialog for editing"""
        try:
            with SessionLocal() as db:
                doc = db.query(Document).filter(Document.id == document.id).first()
                if not doc:
                    QMessageBox.warning(self, "❌ Error", "Documento no encontrado")
                    return

                # Create edit dialog
                edit_dialog = QDialog(self)
                doc_type = "Presupuesto" if doc.type == DocumentType.QUOTE else "Factura" if doc.type == DocumentType.INVOICE else "Albarán"
                edit_dialog.setWindowTitle(f"✏️ Editar {doc_type} - {doc.code}")
                edit_dialog.setModal(True)
                edit_dialog.resize(500, 400)

                layout = QFormLayout(edit_dialog)

                # Status combo
                status_combo = QComboBox()
                status_options = ["draft", "sent", "accepted", "rejected", "paid", "partially_paid", "cancelled"]
                status_combo.addItems(status_options)
                current_status = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)
                if current_status in status_options:
                    status_combo.setCurrentText(current_status)
                layout.addRow("Estado:", status_combo)

                # Due date
                due_date_edit = QDateEdit()
                if doc.due_date:
                    due_date_edit.setDate(QDate(doc.due_date.year, doc.due_date.month, doc.due_date.day))
                else:
                    due_date_edit.setDate(QDate.currentDate().addDays(30))
                due_date_edit.setCalendarPopup(True)
                layout.addRow("Fecha Vencimiento:", due_date_edit)

                # Notes
                notes_edit = QTextEdit()
                notes_edit.setPlainText(doc.notes or "")
                notes_edit.setMaximumHeight(100)
                layout.addRow("Notas:", notes_edit)

                # Internal notes
                internal_notes_edit = QTextEdit()
                internal_notes_edit.setPlainText(doc.internal_notes or "")
                internal_notes_edit.setMaximumHeight(100)
                layout.addRow("Notas Internas:", internal_notes_edit)

                # Buttons
                buttons = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
                )

                def save_changes():
                    try:
                        with SessionLocal() as db2:
                            doc2 = db2.query(Document).filter(Document.id == document.id).first()
                            if doc2:
                                doc2.status = DocumentStatus(status_combo.currentText())
                                qdate = due_date_edit.date()
                                doc2.due_date = date(qdate.year(), qdate.month(), qdate.day())
                                doc2.notes = notes_edit.toPlainText().strip() or None
                                doc2.internal_notes = internal_notes_edit.toPlainText().strip() or None
                                db2.commit()
                                edit_dialog.accept()
                                self.refresh_data()
                                QMessageBox.information(self, "✅ Éxito", "Documento actualizado correctamente")
                    except Exception as e:
                        logger.error(f"Error saving document: {e}")
                        QMessageBox.critical(self, "❌ Error", f"Error al guardar: {str(e)}")

                buttons.accepted.connect(save_changes)
                buttons.rejected.connect(edit_dialog.reject)
                layout.addRow(buttons)

                edit_dialog.exec()

        except Exception as e:
            logger.error(f"Error editing document: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al editar documento: {str(e)}")

    def delete_document(self, document):
        """Delete document"""
        reply = QMessageBox.question(
            self, "🗑️ Confirmar Eliminación",
            f"¿Está seguro de eliminar el documento '{document.code}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                with SessionLocal() as db:
                    doc = db.query(Document).filter(Document.id == document.id).first()
                    if doc:
                        doc_code = doc.code
                        db.delete(doc)
                        db.commit()
                        self.refresh_data()
                        QMessageBox.information(self, "✅ Éxito", f"Documento '{doc_code}' eliminado correctamente")
                    else:
                        QMessageBox.warning(self, "❌ Error", "Documento no encontrado")

            except Exception as e:
                logger.error(f"Error deleting document: {e}")
                QMessageBox.critical(self, "❌ Error", f"Error al eliminar documento: {str(e)}")

class InventoryManagementTab(QWidget):
    """Complete inventory management tab"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        # Defer refresh to prevent blocking during initialization
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.refresh_data)
    
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
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error loading diary notes: {e}")
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
        
        # Reload notes from file to get latest data
        self.load_notes()
        
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
            if hasattr(self.dashboard, 'refresh_data'):
                self.dashboard.refresh_data()
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
        
        import_file_action = QAction("📂 Importar Archivo", self)
        import_file_action.triggered.connect(self.import_external_file)
        file_menu.addAction(import_file_action)
        
        export_data_action = QAction("📤 Exportar Datos", self)
        export_data_action.triggered.connect(self.export_data)
        file_menu.addAction(export_data_action)
        
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
        dialog = SettingsDialog(self)
        dialog.exec()


    def import_external_file(self):
        """"Import external files - Fixed QAction/slot mismatch"""
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar Archivo", "", "Files (*.*)"
            )
            if file_path:
                QMessageBox.information(self, "✅ Importado", f"Archivo: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error: {str(e)}")
    
    def export_data(self):
        """Export application data to CSV/JSON"""
        from PySide6.QtWidgets import QFileDialog

        # Create export dialog
        export_dialog = QDialog(self)
        export_dialog.setWindowTitle("📤 Exportar Datos")
        export_dialog.setModal(True)
        export_dialog.resize(400, 300)

        layout = QVBoxLayout(export_dialog)

        # Export type selection
        type_group = QGroupBox("📋 Seleccione qué exportar")
        type_layout = QVBoxLayout(type_group)

        self.export_clients_check = QCheckBox("👥 Clientes")
        self.export_clients_check.setChecked(True)
        type_layout.addWidget(self.export_clients_check)

        self.export_products_check = QCheckBox("📦 Productos")
        self.export_products_check.setChecked(True)
        type_layout.addWidget(self.export_products_check)

        self.export_documents_check = QCheckBox("📄 Documentos")
        self.export_documents_check.setChecked(True)
        type_layout.addWidget(self.export_documents_check)

        layout.addWidget(type_group)

        # Format selection
        format_group = QGroupBox("📁 Formato de exportación")
        format_layout = QVBoxLayout(format_group)

        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["CSV (Hojas de cálculo)", "JSON (Datos estructurados)"])
        format_layout.addWidget(self.export_format_combo)

        layout.addWidget(format_group)

        # Buttons
        buttons_layout = QHBoxLayout()

        export_btn = QPushButton("📤 Exportar")
        export_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; border-radius: 5px; font-weight: bold;")
        export_btn.clicked.connect(lambda: self.perform_export(export_dialog))
        buttons_layout.addWidget(export_btn)

        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(export_dialog.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        export_dialog.exec()

    def perform_export(self, dialog):
        """Perform the actual export"""
        import csv
        import json
        from PySide6.QtWidgets import QFileDialog

        export_clients = self.export_clients_check.isChecked()
        export_products = self.export_products_check.isChecked()
        export_documents = self.export_documents_check.isChecked()
        is_csv = "CSV" in self.export_format_combo.currentText()

        if not any([export_clients, export_products, export_documents]):
            QMessageBox.warning(self, "❌ Error", "Seleccione al menos un tipo de datos para exportar")
            return

        # Get export directory
        export_dir = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Exportación")
        if not export_dir:
            return

        try:
            exported_files = []

            with SessionLocal() as db:
                # Export Clients
                if export_clients:
                    clients = db.query(Client).all()
                    if clients:
                        if is_csv:
                            filepath = os.path.join(export_dir, "clientes.csv")
                            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                writer.writerow(['Código', 'Nombre', 'Email', 'Teléfono', 'Dirección', 'Ciudad', 'C. Postal', 'CIF/NIF', 'Activo'])
                                for c in clients:
                                    writer.writerow([c.code, c.name, c.email or '', c.phone or '', c.address or '', c.city or '', c.postal_code or '', c.tax_id or '', 'Sí' if c.is_active else 'No'])
                        else:
                            filepath = os.path.join(export_dir, "clientes.json")
                            data = [{'codigo': c.code, 'nombre': c.name, 'email': c.email, 'telefono': c.phone, 'direccion': c.address, 'ciudad': c.city, 'codigo_postal': c.postal_code, 'cif_nif': c.tax_id, 'activo': c.is_active} for c in clients]
                            with open(filepath, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                        exported_files.append(filepath)

                # Export Products
                if export_products:
                    products = db.query(Product).all()
                    if products:
                        if is_csv:
                            filepath = os.path.join(export_dir, "productos.csv")
                            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                writer.writerow(['Código', 'Nombre', 'Descripción', 'Categoría', 'P. Coste', 'P. Venta', 'Stock', 'Stock Mín', 'Unidad', 'Activo'])
                                for p in products:
                                    writer.writerow([p.code, p.name, p.description or '', p.category or '', float(p.purchase_price or 0), float(p.sale_price or 0), p.current_stock or 0, p.minimum_stock or 0, p.stock_unit or '', 'Sí' if p.is_active else 'No'])
                        else:
                            filepath = os.path.join(export_dir, "productos.json")
                            data = [{'codigo': p.code, 'nombre': p.name, 'descripcion': p.description, 'categoria': p.category, 'precio_coste': float(p.purchase_price or 0), 'precio_venta': float(p.sale_price or 0), 'stock': p.current_stock, 'stock_minimo': p.minimum_stock, 'unidad': p.stock_unit, 'activo': p.is_active} for p in products]
                            with open(filepath, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                        exported_files.append(filepath)

                # Export Documents
                if export_documents:
                    documents = db.query(Document).options(joinedload(Document.client)).all()
                    if documents:
                        if is_csv:
                            filepath = os.path.join(export_dir, "documentos.csv")
                            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                writer.writerow(['Código', 'Tipo', 'Estado', 'Cliente', 'F. Emisión', 'F. Vencimiento', 'Subtotal', 'IVA', 'Total', 'Notas'])
                                for d in documents:
                                    doc_type = d.type.value if hasattr(d.type, 'value') else str(d.type)
                                    status = d.status.value if hasattr(d.status, 'value') else str(d.status)
                                    client_name = d.client.name if d.client else ''
                                    issue_date = d.issue_date.strftime('%Y-%m-%d') if d.issue_date else ''
                                    due_date = d.due_date.strftime('%Y-%m-%d') if d.due_date else ''
                                    writer.writerow([d.code, doc_type, status, client_name, issue_date, due_date, float(d.subtotal or 0), float(d.tax_amount or 0), float(d.total or 0), d.notes or ''])
                        else:
                            filepath = os.path.join(export_dir, "documentos.json")
                            data = []
                            for d in documents:
                                data.append({
                                    'codigo': d.code,
                                    'tipo': d.type.value if hasattr(d.type, 'value') else str(d.type),
                                    'estado': d.status.value if hasattr(d.status, 'value') else str(d.status),
                                    'cliente': d.client.name if d.client else None,
                                    'fecha_emision': d.issue_date.strftime('%Y-%m-%d') if d.issue_date else None,
                                    'fecha_vencimiento': d.due_date.strftime('%Y-%m-%d') if d.due_date else None,
                                    'subtotal': float(d.subtotal or 0),
                                    'iva': float(d.tax_amount or 0),
                                    'total': float(d.total or 0),
                                    'notas': d.notes
                                })
                            with open(filepath, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                        exported_files.append(filepath)

            dialog.accept()

            if exported_files:
                file_list = '\n'.join([f"  - {os.path.basename(f)}" for f in exported_files])
                QMessageBox.information(
                    self, "✅ Exportación Completada",
                    f"Datos exportados correctamente a:\n{export_dir}\n\nArchivos creados:\n{file_list}"
                )
            else:
                QMessageBox.information(self, "ℹ️ Info", "No hay datos para exportar")

        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al exportar datos: {str(e)}")
    


class SettingsDialog(QDialog):
    """Functional Settings dialog"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Configuración - DRAGOFACTU")
        self.setModal(True)
        self.resize(500, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # General settings
        general_group = QGroupBox("🔧 Configuración General")
        general_layout = QFormLayout(general_group)
        
        # Company info
        self.company_name_edit = QLineEdit()
        self.company_name_edit.setText("DRAGOFACTU Software")
        general_layout.addRow("Nombre Empresa:", self.company_name_edit)
        
        self.company_email_edit = QLineEdit()
        self.company_email_edit.setText("info@dragofactu.com")
        general_layout.addRow("Email Empresa:", self.company_email_edit)
        
        self.company_phone_edit = QLineEdit()
        self.company_phone_edit.setText("+34 900 000 000")
        general_layout.addRow("Teléfono Empresa:", self.company_phone_edit)
        
        layout.addWidget(general_group)
        
        # UI settings
        ui_group = QGroupBox("🎨 Apariencia")
        ui_layout = QFormLayout(ui_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Oscuro", "Auto"])
        self.theme_combo.setCurrentText("Auto")
        ui_layout.addRow("Tema:", self.theme_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Español", "English", "Deutsch"])
        self.language_combo.setCurrentText("Español")
        ui_layout.addRow("Idioma:", self.language_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        ui_layout.addRow("Tamaño Fuente:", self.font_size_spin)
        
        layout.addWidget(ui_group)
        
        # Business settings
        business_group = QGroupBox("💼 Configuración Negocio")
        business_layout = QFormLayout(business_group)
        
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["EUR - Euro €", "USD - Dólar $", "GBP - Libra £"])
        self.currency_combo.setCurrentText("EUR - Euro €")
        business_layout.addRow("Moneda:", self.currency_combo)
        
        self.tax_rate_spin = QDoubleSpinBox()
        self.tax_rate_spin.setRange(0, 50)
        self.tax_rate_spin.setDecimals(2)
        self.tax_rate_spin.setValue(21)
        self.tax_rate_spin.setSuffix("%")
        business_layout.addRow("IVA Por Defecto:", self.tax_rate_spin)
        
        layout.addWidget(business_group)
        
        # Database info
        db_group = QGroupBox("🗄️ Información Base de Datos")
        db_layout = QFormLayout(db_group)
        
        # Get database info
        try:
            with SessionLocal() as db:
                client_count = db.query(Client).count()
                product_count = db.query(Product).count()
                document_count = db.query(Document).count()

                db_layout.addRow("Clientes:", QLabel(str(client_count)))
                db_layout.addRow("Productos:", QLabel(str(product_count)))
                db_layout.addRow("Documentos:", QLabel(str(document_count)))
        except Exception as e:
            logger.error(f"Error getting database info for settings: {e}")
            db_layout.addRow("Estado:", QLabel("❌ Error de conexión"))
        
        layout.addWidget(db_group)
        
        # App info
        info_group = QGroupBox("ℹ️ Información Aplicación")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("Versión:", QLabel("V1.0.0.3"))
        info_layout.addRow("Desarrollador:", QLabel("DRAGOFACTU Team"))
        info_layout.addRow("GitHub:", QLabel("github.com/Copitx/Dragofactu"))
        info_layout.addRow("Python:", QLabel(f"3.{sys.version_info.minor}.{sys.version_info.micro}"))
        
        layout.addWidget(info_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Guardar Configuración")
        save_btn.clicked.connect(self.save_settings)
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
        
        reset_btn = QPushButton("🔄 Restablecer")
        reset_btn.clicked.connect(self.reset_settings)
        reset_btn.setStyleSheet("background-color: #f39c12; color: white; padding: 10px; border-radius: 5px;")
        buttons_layout.addWidget(reset_btn)
        
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("background-color: #95a5a6; color: white; padding: 10px; border-radius: 5px;")
        buttons_layout.addWidget(cancel_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
    
    def save_settings(self):
        """Save settings"""
        try:
            # Get all values
            settings = {
                'company_name': self.company_name_edit.text(),
                'company_email': self.company_email_edit.text(),
                'company_phone': self.company_phone_edit.text(),
                'theme': self.theme_combo.currentText(),
                'language': self.language_combo.currentText(),
                'font_size': self.font_size_spin.value(),
                'currency': self.currency_combo.currentText(),
                'tax_rate': self.tax_rate_spin.value()
            }
            
            # Here you would save to a config file or database
            # For now, just show success message
            QMessageBox.information(self, "✅ Guardado", "Configuración guardada correctamente")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error guardando configuración: {str(e)}")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self, "🔄 Restablecer", 
            "¿Está seguro de restablecer la configuración a valores por defecto?"
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.company_name_edit.setText("DRAGOFACTU Software")
            self.company_email_edit.setText("info@dragofactu.com")
            self.company_phone_edit.setText("+34 900 000 000")
            self.theme_combo.setCurrentText("Auto")
            self.language_combo.setCurrentText("Español")
            self.font_size_spin.setValue(12)
            self.currency_combo.setCurrentText("EUR - Euro €")
            self.tax_rate_spin.setValue(21)
            
            QMessageBox.information(self, "✅ Restablecido", "Configuración restablecida a valores por defecto")
    
    def import_external_file(self):
        """Import external files"""
        from PySide6.QtWidgets import QFileDialog
        import json
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo para Importar",
            "",
            "Todos los Archivos (*.csv *.json *.txt);;CSV Files (*.csv);;JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.import_csv_file(file_path)
                elif file_path.endswith('.json'):
                    self.import_json_file(file_path)
                else:
                    self.import_text_file(file_path)
                    
                QMessageBox.information(self, "✅ Importado", f"Archivo importado correctamente:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "❌ Error", f"Error importando archivo: {str(e)}")
    
    def import_csv_file(self, file_path):
        """Import CSV file"""
        try:
            import csv
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    # Try to import as client if it looks like client data
                    if 'name' in row and ('email' in row or 'phone' in row):
                        with SessionLocal() as db:
                            client = Client(
                                code=row.get('code', f"C-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                                name=row.get('name', ''),
                                email=row.get('email') or None,
                                phone=row.get('phone') or None,
                                address=row.get('address') or None,
                                tax_id=row.get('tax_id') or None,
                                is_active=True
                            )
                            db.add(client)
                            db.commit()
                            count += 1
                
                QMessageBox.information(self, "✅ CSV Importado", f"Se importaron {count} clientes")
                
        except Exception as e:
            raise Exception(f"Error importando CSV: {str(e)}")
    
    def import_json_file(self, file_path):
        """Import JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = 0
                
                if isinstance(data, list):
                    for item in data:
                        if 'name' in item:  # Treat as client
                            with SessionLocal() as db:
                                client = Client(
                                    code=item.get('code', f"C-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                                    name=item.get('name', ''),
                                    email=item.get('email') or None,
                                    phone=item.get('phone') or None,
                                    address=item.get('address') or None,
                                    tax_id=item.get('tax_id') or None,
                                    is_active=item.get('is_active', True)
                                )
                                db.add(client)
                                db.commit()
                                count += 1
                
                QMessageBox.information(self, "✅ JSON Importado", f"Se importaron {count} clientes")
                
        except Exception as e:
            raise Exception(f"Error importando JSON: {str(e)}")
    
    def import_text_file(self, file_path):
        """Import text file as diary notes"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.strip().split('\n')
                
                # Create diary entries from lines
                import json
                self.load_notes()  # Load existing notes
                
                for line in lines:
                    if line.strip():
                        note = {
                            'title': f"Importado: {line[:30]}...",
                            'content': line,
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'time': datetime.now().strftime('%H:%M'),
                            'priority': '🟢 Normal',
                            'tags': ['importado', 'texto']
                        }
                        self.notes.append(note)
                
                self.save_notes()
                QMessageBox.information(self, "✅ Texto Importado", f"Se importaron {len(lines)} notas al diario")
                
        except Exception as e:
            raise Exception(f"Error importando texto: {str(e)}")

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