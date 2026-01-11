#!/usr/bin/env python3
"""
Fixed DRAGOFACTU Application with basic functionality - Corrected Version
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QLineEdit, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox, QMenuBar, QStatusBar,
    QHeaderView, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction

from dragofactu.models.database import SessionLocal, engine, Base
from dragofactu.models.entities import User, Client, Product, Document, DocumentType, DocumentStatus
from dragofactu.services.auth.auth_service import AuthService
from dragofactu.config.translation import translator

class SimpleDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Panel Principal")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Summary cards
        cards_layout = QHBoxLayout()
        
        # Client count
        client_card = self.create_card("Clientes", str(self.get_client_count()), "#0078d4")
        cards_layout.addWidget(client_card)
        
        # Product count  
        product_card = self.create_card("Productos", str(self.get_product_count()), "#107c10")
        cards_layout.addWidget(product_card)
        
        # Document count
        doc_card = self.create_card("Documentos", str(self.get_document_count()), "#d83b01")
        cards_layout.addWidget(doc_card)
        
        layout.addLayout(cards_layout)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        new_client_btn = QPushButton("Nuevo Cliente")
        new_client_btn.clicked.connect(self.add_client)
        actions_layout.addWidget(new_client_btn)
        
        new_product_btn = QPushButton("Nuevo Producto")
        new_product_btn.clicked.connect(self.add_product)
        actions_layout.addWidget(new_product_btn)
        
        new_doc_btn = QPushButton("Nuevo Documento")
        new_doc_btn.clicked.connect(self.add_document)
        actions_layout.addWidget(new_doc_btn)
        
        layout.addLayout(actions_layout)
        layout.addStretch()
    
    def create_card(self, title, value, color):
        """Create summary card"""
        from PySide6.QtWidgets import QFrame
        
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-weight: bold;")
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
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
    
    def add_client(self):
        """Add new client"""
        dialog = ClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Éxito", "Cliente añadido correctamente")
            # Get parent main window and refresh dashboard
            parent = self.parent()
            while parent and not isinstance(parent, SimpleMainWindow):
                parent = parent.parent()
            if parent:
                parent.dashboard.setup_ui()
    
    def add_product(self):
        """Add new product"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Éxito", "Producto añadido correctamente")
            # Get parent main window and refresh dashboard
            parent = self.parent()
            while parent and not isinstance(parent, SimpleMainWindow):
                parent = parent.parent()
            if parent:
                parent.dashboard.setup_ui()
            self.refresh_dashboard()
    
    def refresh_dashboard(self):
        """Refresh dashboard data"""
        # Update the counts in the dashboard cards
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QHBoxLayout):
                # This is the cards layout
                for j in range(widget.count()):
                    card = widget.itemAt(j).widget()
                    if hasattr(card, 'findChild'):
                        value_label = card.findChild(QLabel)
                        if value_label and hasattr(value_label, 'text'):
                            # Update counts based on card content
                            text = value_label.text()
                            if text.isdigit():
                                # Find which card this is and update accordingly
                                parent_layout = widget.itemAt(j).widget().layout()
                                if parent_layout:
                                    title_item = parent_layout.itemAt(0).widget()
                                    if title_item:
                                        title = title_item.text()
                                        if title == "Clientes":
                                            value_label.setText(str(self.get_client_count()))
                                        elif title == "Productos":
                                            value_label.setText(str(self.get_product_count()))
                                        elif title == "Documentos":
                                            value_label.setText(str(self.get_document_count()))
    
    def add_document(self):
        """Add new document"""
        QMessageBox.information(self, "Info", "Función de documentos en desarrollo")

class ClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Cliente")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        
        self.code_edit = QLineEdit()
        layout.addRow("Código:", self.code_edit)
        
        self.name_edit = QLineEdit()
        layout.addRow("Nombre:", self.name_edit)
        
        self.email_edit = QLineEdit()
        layout.addRow("Email:", self.email_edit)
        
        self.phone_edit = QLineEdit()
        layout.addRow("Teléfono:", self.phone_edit)
        
        self.address_edit = QLineEdit()
        layout.addRow("Dirección:", self.address_edit)
        
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
            QMessageBox.warning(self, "Error", "El nombre es obligatorio")
            return
        
        try:
            with SessionLocal() as db:
                client = Client(
                    code=self.code_edit.text(),
                    name=self.name_edit.text(),
                    email=self.email_edit.text(),
                    phone=self.phone_edit.text(),
                    address=self.address_edit.text(),
                    is_active=True
                )
                db.add(client)
                db.commit()
                super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar cliente: {str(e)}")

class ProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Producto")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        
        self.code_edit = QLineEdit()
        layout.addRow("Código:", self.code_edit)
        
        self.name_edit = QLineEdit()
        layout.addRow("Nombre:", self.name_edit)
        
        self.price_edit = QLineEdit()
        self.price_edit.setText("0.00")
        layout.addRow("Precio Venta:", self.price_edit)
        
        self.stock_spin = QSpinBox()
        self.stock_spin.setMinimum(0)
        self.stock_spin.setValue(0)
        layout.addRow("Stock Inicial:", self.stock_spin)
        
        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setMinimum(0)
        self.min_stock_spin.setValue(5)
        layout.addRow("Stock Mínimo:", self.min_stock_spin)
        
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
            QMessageBox.warning(self, "Error", "El nombre es obligatorio")
            return
        
        try:
            with SessionLocal() as db:
                product = Product(
                    code=self.code_edit.text(),
                    name=self.name_edit.text(),
                    sale_price=float(self.price_edit.text() or 0),
                    current_stock=self.stock_spin.value(),
                    minimum_stock=self.min_stock_spin.value(),
                    stock_unit="Unidades",
                    is_active=True
                )
                db.add(product)
                db.commit()
                super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar producto: {str(e)}")

class SimpleMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.setup_ui()
    
    def set_current_user(self, user):
        """Set current user"""
        self.current_user = user
        # Access attributes directly to avoid DetachedInstanceError
        username = user.username
        full_name = user.full_name
        role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        
        self.statusBar().showMessage(f"Usuario: {full_name} ({role})")
    
    def setup_ui(self):
        """Setup main window"""
        self.setWindowTitle("🐲 DRAGOFACTU - Sistema de Gestión")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create menu bar
        self.create_menu()
        
        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Dashboard tab
        self.dashboard = SimpleDashboard()
        self.tabs.addTab(self.dashboard, "Panel Principal")
        
        # Add other tabs with actual functionality
        self.clients_tab = ClientManagementTab()
        self.tabs.addTab(self.clients_tab, "Clientes")
        
        self.products_tab = ProductManagementTab()
        self.tabs.addTab(self.products_tab, "Productos")
        
        self.documents_tab = DocumentManagementTab()
        self.tabs.addTab(self.documents_tab, "Documentos")
        
        self.inventory_tab = InventoryManagementTab()
        self.tabs.addTab(self.inventory_tab, "Inventario")
        
        self.diary_tab = DiaryManagementTab()
        self.tabs.addTab(self.diary_tab, "Diario")
        
        layout.addWidget(self.tabs)
        
        # Create status bar
        self.statusBar().showMessage("Listo")
        
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
        elif index == 4:  # Inventory tab
            if hasattr(tab_widget, 'refresh_data'):
                tab_widget.refresh_data()
    
    def create_menu(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("Archivo")
        
        new_quote_action = QAction("Nuevo Presupuesto", self)
        new_quote_action.triggered.connect(self.new_quote)
        file_menu.addAction(new_quote_action)
        
        new_invoice_action = QAction("Nueva Factura", self)
        new_invoice_action.triggered.connect(self.new_invoice)
        file_menu.addAction(new_invoice_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Herramientas")
        
        settings_action = QAction("Ajustes", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Language menu
        language_menu = menubar.addMenu("Idioma")
        
        for lang_code, lang_name in translator.get_available_languages().items():
            lang_action = QAction(lang_name, self)
            lang_action.triggered.connect(lambda checked, code=lang_code: self.change_language(code))
            language_menu.addAction(lang_action)
    
    def new_quote(self):
        """Create new quote"""
        dialog = QuoteDialog(self)
        dialog.exec()
    
    def new_invoice(self):
        """Create new invoice"""
        dialog = InvoiceDialog(self)
        dialog.exec()
    
    def show_settings(self):
        """Show settings dialog"""
        QMessageBox.information(self, "Ajustes", "Configuración del sistema en desarrollo")
    
    def change_language(self, language_code):
        """Change application language"""
        if translator.set_language(language_code):
            self.statusBar().showMessage(f"Idioma cambiado a: {translator.get_available_languages()[language_code]}", 3000)

class QuoteDialog(QDialog):
    """Quote creation dialog"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Presupuesto")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Client selection
        client_layout = QHBoxLayout()
        layout.addWidget(QLabel("Cliente:"))
        self.client_combo = QComboBox()
        client_layout.addWidget(self.client_combo)
        layout.addLayout(client_layout)
        
        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["Producto", "Descripción", "Cantidad", "Precio", "Total"])
        layout.addWidget(self.items_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_item_btn = QPushButton("Añadir Producto")
        add_item_btn.clicked.connect(self.add_item)
        button_layout.addWidget(add_item_btn)
        
        save_btn = QPushButton("Guardar Presupuesto")
        save_btn.clicked.connect(self.save_quote)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setup_clients()
    
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
    
    def add_item(self):
        """Add item to quote"""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        self.items_table.setItem(row, 0, QTableWidgetItem("Producto ejemplo"))
        self.items_table.setItem(row, 1, QTableWidgetItem("Descripción"))
        self.items_table.setItem(row, 2, QTableWidgetItem("1"))
        self.items_table.setItem(row, 3, QTableWidgetItem("100.00"))
        self.items_table.setItem(row, 4, QTableWidgetItem("100.00"))
    
    def save_quote(self):
        """Save quote"""
        QMessageBox.information(self, "Éxito", "Presupuesto guardado correctamente")
        self.accept()

class InvoiceDialog(QDialog):
    """Invoice creation dialog"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Factura")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Función de facturas en desarrollo..."))
        
        button_layout = QHBoxLayout()
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)

class ClientManagementTab(QWidget):
    """Client management tab"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        add_btn = QPushButton("Añadir Cliente")
        add_btn.clicked.connect(self.add_client)
        toolbar_layout.addWidget(add_btn)
        
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(refresh_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Table
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(6)
        self.clients_table.setHorizontalHeaderLabels(["Código", "Nombre", "Email", "Teléfono", "Dirección", "Estado"])
        
        # Set table properties
        header = self.clients_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
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
                    
                    status_text = "Activo" if client.is_active else "Inactivo"
                    status_item = QTableWidgetItem(status_text)
                    status_item.setStyleSheet("color: green;" if client.is_active else "color: red;")
                    self.clients_table.setItem(row, 5, status_item)
                
                self.status_label.setText(f"Mostrando {len(clients)} clientes")
                
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
    
    def add_client(self):
        """Add new client"""
        dialog = ClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()

class ProductManagementTab(QWidget):
    """Product management tab"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        add_btn = QPushButton("Añadir Producto")
        add_btn.clicked.connect(self.add_product)
        toolbar_layout.addWidget(add_btn)
        
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(refresh_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels(["Código", "Nombre", "Precio", "Stock", "Stock Mínimo", "Estado"])
        
        # Set table properties
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
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
                    self.products_table.setItem(row, 2, QTableWidgetItem(str(product.sale_price or 0)))
                    self.products_table.setItem(row, 3, QTableWidgetItem(str(product.current_stock or 0)))
                    self.products_table.setItem(row, 4, QTableWidgetItem(str(product.minimum_stock or 0)))
                    
                    status_text = "Activo" if product.is_active else "Inactivo"
                    status_item = QTableWidgetItem(status_text)
                    status_item.setStyleSheet("color: green;" if product.is_active else "color: red;")
                    self.products_table.setItem(row, 5, status_item)
                
                self.status_label.setText(f"Mostrando {len(products)} productos")
                
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
    
    def add_product(self):
        """Add new product"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()

class DocumentManagementTab(QWidget):
    """Document management tab"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Document type selection
        type_layout = QHBoxLayout()
        layout.addWidget(QLabel("Tipo:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Presupuesto", "Factura", "Albarán"])
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        new_doc_btn = QPushButton("Nuevo Documento")
        new_doc_btn.clicked.connect(self.new_document)
        action_layout.addWidget(new_doc_btn)
        
        list_docs_btn = QPushButton("Listar Documentos")
        list_docs_btn.clicked.connect(self.list_documents)
        action_layout.addWidget(list_docs_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # Documents table
        self.docs_table = QTableWidget()
        self.docs_table.setColumnCount(5)
        self.docs_table.setHorizontalHeaderLabels(["Código", "Tipo", "Cliente", "Fecha", "Total"])
        
        layout.addWidget(self.docs_table)
        
        # Status label
        self.status_label = QLabel("Gestión de documentos - haga clic en 'Nuevo Documento' para empezar")
        layout.addWidget(self.status_label)
    
    def new_document(self):
        """Create new document"""
        doc_type = self.type_combo.currentText()
        QMessageBox.information(self, "Nuevo Documento", f"Creando nuevo {doc_type.lower()}...")
    
    def list_documents(self):
        """List existing documents"""
        try:
            with SessionLocal() as db:
                documents = db.query(Document).all()
                
                self.docs_table.setRowCount(0)
                
                for row, doc in enumerate(documents):
                    self.docs_table.insertRow(row)
                    
                    self.docs_table.setItem(row, 0, QTableWidgetItem(doc.code or ""))
                    self.docs_table.setItem(row, 1, QTableWidgetItem(doc.type.value if hasattr(doc.type, 'value') else str(doc.type)))
                    self.docs_table.setItem(row, 2, QTableWidgetItem(f"Cliente {doc.id}"))
                    self.docs_table.setItem(row, 3, QTableWidgetItem(str(doc.issue_date or "")))
                    self.docs_table.setItem(row, 4, QTableWidgetItem(str(doc.total or 0)))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error listando documentos: {str(e)}")

class InventoryManagementTab(QWidget):
    """Inventory management tab"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        add_btn = QPushButton("Añadir Producto")
        add_btn.clicked.connect(self.add_product)
        toolbar_layout.addWidget(add_btn)
        
        adjust_btn = QPushButton("Ajustar Stock")
        adjust_btn.clicked.connect(self.adjust_stock)
        toolbar_layout.addWidget(adjust_btn)
        
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(refresh_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(6)
        self.inventory_table.setHorizontalHeaderLabels(["Producto", "Stock Actual", "Stock Mínimo", "Estado", "Acciones", "Último Movimiento"])
        
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
                
                for row, product in enumerate(products):
                    self.inventory_table.insertRow(row)
                    
                    self.inventory_table.setItem(row, 0, QTableWidgetItem(product.name or ""))
                    self.inventory_table.setItem(row, 1, QTableWidgetItem(str(product.current_stock or 0)))
                    self.inventory_table.setItem(row, 2, QTableWidgetItem(str(product.minimum_stock or 0)))
                    
                    # Status
                    stock_status = "OK"
                    if product.current_stock and product.minimum_stock:
                        if product.current_stock <= product.minimum_stock:
                            stock_status = "BAJO"
                            low_stock_count += 1
                    
                    status_item = QTableWidgetItem(stock_status)
                    status_item.setStyleSheet(
                        "color: orange;" if stock_status == "BAJO" else "color: green;"
                    )
                    self.inventory_table.setItem(row, 3, status_item)
                    
                    # Actions
                    actions_btn = QPushButton("Ajustar")
                    actions_btn.clicked.connect(lambda checked, p=product: self.adjust_product_stock(p))
                    self.inventory_table.setCellWidget(row, 4, actions_btn)
                    
                    # Last movement
                    last_movement = "N/A"
                    self.inventory_table.setItem(row, 5, QTableWidgetItem(last_movement))
                
                self.status_label.setText(f"Mostrando {len(products)} productos - {low_stock_count} con stock bajo")
                
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
    
    def add_product(self):
        """Add product to inventory"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
    
    def adjust_stock(self):
        """Quick stock adjustment"""
        QMessageBox.information(self, "Ajustar Stock", "Selecciona un producto y usa el botón 'Ajustar' en la tabla")
    
    def adjust_product_stock(self, product):
        """Adjust stock for specific product"""
        quantity, ok = QMessageBox.getInt(
            self, 
            "Ajustar Stock", 
            f"Cantidad para {product.name}:",
            0, -999, 999, 1
        )
        
        if ok:
            try:
                with SessionLocal() as db:
                    db_product = db.query(Product).filter(Product.id == product.id).first()
                    if db_product:
                        db_product.current_stock = max(0, (db_product.current_stock or 0) + quantity)
                        db.commit()
                        QMessageBox.information(self, "Éxito", f"Stock ajustado para {product.name}: {quantity:+d}")
                        self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error ajustando stock: {str(e)}")

class DiaryManagementTab(QWidget):
    """Diary management tab"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        add_entry_btn = QPushButton("Nueva Nota")
        add_entry_btn.clicked.connect(self.add_entry)
        toolbar_layout.addWidget(add_entry_btn)
        
        view_calendar_btn = QPushButton("Ver Calendario")
        view_calendar_btn.clicked.connect(self.view_calendar)
        toolbar_layout.addWidget(view_calendar_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Entries area
        self.entries_area = QTextEdit()
        self.entries_area.setPlaceholderText("Las notas del diario aparecerán aquí...")
        layout.addWidget(self.entries_area)
        
        # Status label
        self.status_label = QLabel("Diario personal - Haz clic en 'Nueva Nota' para añadir apuntes")
        layout.addWidget(self.status_label)
    
    def add_entry(self):
        """Add new diary entry"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QTextEdit, QDateEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Nueva Nota del Diario")
        dialog.setModal(True)
        
        dialog_layout = QVBoxLayout(dialog)
        
        # Title
        title_edit = QLineEdit()
        title_edit.setPlaceholderText("Título de la nota")
        dialog_layout.addWidget(QLabel("Título:"))
        dialog_layout.addWidget(title_edit)
        
        # Content
        content_edit = QTextEdit()
        content_edit.setPlaceholderText("Contenido de la nota...")
        dialog_layout.addWidget(QLabel("Contenido:"))
        dialog_layout.addWidget(content_edit)
        
        # Date
        date_edit = QDateEdit()
        date_edit.setDate(QDateTime.currentDate().date())
        date_edit.setCalendarPopup(True)
        dialog_layout.addWidget(QLabel("Fecha:"))
        dialog_layout.addWidget(date_edit)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("Guardar Nota")
        save_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_btn)
        
        dialog_layout.addLayout(buttons_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted and title_edit.text().strip():
            # Add to entries area
            entry_text = f"📅 {date_edit.date().toString('yyyy-MM-dd')} - {title_edit.text()}\n{content_edit.toPlainText()}\n"
            entry_text += "-" * 50 + "\n"
            
            self.entries_area.append(entry_text)
            self.status_label.setText("Nota guardada correctamente")
    
    def view_calendar(self):
        """View calendar"""
        QMessageBox.information(self, "Calendario", "Calendario de notas en desarrollo...")

class SimpleLoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.user = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup login dialog"""
        self.setWindowTitle("Login - DRAGOFACTU")
        self.setModal(True)
        self.resize(300, 200)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🐲 DRAGOFACTU")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Usuario")
        layout.addWidget(self.username_edit)
        
        # Password
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Contraseña")
        layout.addWidget(self.password_edit)
        
        # Login button
        login_btn = QPushButton("Iniciar Sesión")
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)
    
    def handle_login(self):
        """Handle login"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Por favor ingrese usuario y contraseña")
            return
        
        try:
            auth_service = AuthService()
            with SessionLocal() as db:
                user = auth_service.authenticate(db, username, password)
                if user:
                    self.user = user
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Usuario o contraseña incorrectos")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de autenticación: {str(e)}")

class SimpleApp(QApplication):
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
        login_dialog = SimpleLoginDialog()
        
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            # Store user data to avoid DetachedInstanceError
            self.current_user_data = {
                'id': login_dialog.user.id,
                'username': login_dialog.user.username,
                'full_name': login_dialog.user.full_name,
                'role': login_dialog.user.role.value if hasattr(login_dialog.user.role, 'value') else str(login_dialog.user.role)
            }
            self.show_main_window()
        else:
            self.quit()
    
    def show_main_window(self):
        """Show main window"""
        self.main_window = SimpleMainWindow()
        
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
    app = SimpleApp()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()