#!/usr/bin/env python3
"""
Fixed DRAGOFACTU Application with basic functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QLineEdit, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox, QMenuBar, QStatusBar
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
    
    def add_product(self):
        """Add new product"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Éxito", "Producto añadido correctamente")
    
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
        self.code_edit.setText(f"CLI-{SessionLocal().query(Client).count() + 1:04d}")
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
        self.code_edit.setText(f"PROD-{SessionLocal().query(Product).count() + 1:04d}")
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
        self.statusBar().showMessage(f"Usuario: {user.full_name} ({user.role})")
    
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
        
        # Add other tabs (placeholders for now)
        self.clients_tab = QWidget()
        self.clients_layout = QVBoxLayout(self.clients_tab)
        self.clients_layout.addWidget(QLabel("Gestión de Clientes - En desarrollo"))
        self.tabs.addTab(self.clients_tab, "Clientes")
        
        self.products_tab = QWidget()
        self.products_layout = QVBoxLayout(self.products_tab)
        self.products_layout.addWidget(QLabel("Gestión de Productos - En desarrollo"))
        self.tabs.addTab(self.products_tab, "Productos")
        
        self.documents_tab = QWidget()
        self.documents_layout = QVBoxLayout(self.documents_tab)
        self.documents_layout.addWidget(QLabel("Gestión de Documentos - En desarrollo"))
        self.tabs.addTab(self.documents_tab, "Documentos")
        
        self.inventory_tab = QWidget()
        self.inventory_layout = QVBoxLayout(self.inventory_tab)
        self.inventory_layout.addWidget(QLabel("Inventario - En desarrollo"))
        self.tabs.addTab(self.inventory_tab, "Inventario")
        
        self.diary_tab = QWidget()
        self.diary_layout = QVBoxLayout(self.diary_tab)
        self.diary_layout.addWidget(QLabel("Diario Personal - En desarrollo"))
        self.tabs.addTab(self.diary_tab, "Diario")
        
        layout.addWidget(self.tabs)
        
        # Create status bar
        self.statusBar().showMessage("Listo")
    
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
        QMessageBox.information(self, "Info", "Función Nuevo Presupuesto en desarrollo")
    
    def new_invoice(self):
        """Create new invoice"""
        QMessageBox.information(self, "Info", "Función Nueva Factura en desarrollo")
    
    def show_settings(self):
        """Show settings dialog"""
        QMessageBox.information(self, "Ajustes", "Configuración del sistema en desarrollo")
    
    def change_language(self, language_code):
        """Change application language"""
        if translator.set_language(language_code):
            self.statusBar().showMessage(f"Idioma cambiado a: {translator.get_available_languages()[language_code]}", 3000)

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
            # Refresh user with new session to avoid DetachedInstanceError
            with SessionLocal() as db:
                self.current_user = db.merge(login_dialog.user)
            self.show_main_window()
        else:
            self.quit()
    
    def show_main_window(self):
        """Show main window"""
        self.main_window = SimpleMainWindow()
        self.main_window.set_current_user(self.current_user)
        self.main_window.show()

def main():
    """Main function"""
    app = SimpleApp()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()