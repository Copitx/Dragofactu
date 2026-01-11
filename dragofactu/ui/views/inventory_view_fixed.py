"""
Fixed Inventory View with Add Product functionality
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QLineEdit, QComboBox, QMessageBox, QSpinBox, QDialog,
    QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from dragofactu.models.database import SessionLocal
from dragofactu.models.entities import User, Product, StockMovement
from dragofactu.services.business.entity_services import ProductService
from dragofactu.services.inventory.inventory_service import InventoryService
from dragofactu.config.translation import t
import uuid
from datetime import datetime

class AddProductDialog(QDialog):
    """Dialog for adding new products"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("buttons.add_product"))
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QFormLayout(self)
        
        # Product fields
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("AUTO")
        layout.addRow(t("products.code"), self.code_edit)
        
        self.name_edit = QLineEdit()
        layout.addRow(t("products.name"), self.name_edit)
        
        self.description_edit = QLineEdit()
        layout.addRow("Descripción", self.description_edit)
        
        self.category_edit = QLineEdit()
        layout.addRow("Categoría", self.category_edit)
        
        self.purchase_price_edit = QLineEdit()
        layout.addRow("Precio Compra", self.purchase_price_edit)
        
        self.sale_price_edit = QLineEdit()
        layout.addRow("Precio Venta", self.sale_price_edit)
        
        self.current_stock_spin = QSpinBox()
        self.current_stock_spin.setMinimum(0)
        self.current_stock_spin.setMaximum(99999)
        self.current_stock_spin.setValue(0)
        layout.addRow(t("inventory.current_stock"), self.current_stock_spin)
        
        self.minimum_stock_spin = QSpinBox()
        self.minimum_stock_spin.setMinimum(0)
        self.minimum_stock_spin.setMaximum(99999)
        self.minimum_stock_spin.setValue(5)
        layout.addRow(t("inventory.minimum_stock"), self.minimum_stock_spin)
        
        self.unit_edit = QLineEdit()
        self.unit_edit.setText("Unidades")
        layout.addRow("Unidad", self.unit_edit)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def get_product_data(self):
        """Get product data from form"""
        return {
            'code': self.code_edit.text() or f"PROD-{uuid.uuid4().hex[:8].upper()}",
            'name': self.name_edit.text(),
            'description': self.description_edit.text(),
            'category': self.category_edit.text(),
            'purchase_price': float(self.purchase_price_edit.text() or 0),
            'sale_price': float(self.sale_price_edit.text() or 0),
            'current_stock': self.current_stock_spin.value(),
            'minimum_stock': self.minimum_stock_spin.value(),
            'stock_unit': self.unit_edit.text(),
            'is_active': True
        }

class InventoryView(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.inventory_service = None
        self.setup_ui()
        self.refresh_data()
    
    def set_current_user(self, user):
        """Set current user"""
        self.current_user = user
    
    def setup_ui(self):
        """Setup inventory management UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(t("inventory.title"))
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Search and filters
        filter_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar productos...")
        self.search_edit.textChanged.connect(self.filter_products)
        filter_layout.addWidget(self.search_edit)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("Todas las categorías")
        filter_layout.addWidget(self.category_combo)
        
        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.clicked.connect(self.refresh_data)
        filter_layout.addWidget(self.refresh_button)
        
        layout.addLayout(filter_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton(t("buttons.add_product"))
        self.add_button.clicked.connect(self.add_product)
        button_layout.addWidget(self.add_button)
        
        self.adjust_button = QPushButton(t("buttons.adjust_stock"))
        self.adjust_button.clicked.connect(self.adjust_stock)
        button_layout.addWidget(self.adjust_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Products table
        self.products_table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.products_table)
        
        # Status bar
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
    
    def setup_table(self):
        """Setup products table"""
        headers = [
            t("products.code"),
            t("products.name"), 
            "Categoría",
            t("inventory.current_stock"),
            t("inventory.minimum_stock"),
            "Precio Compra",
            "Precio Venta",
            "Estado"
        ]
        
        self.products_table.setColumnCount(len(headers))
        self.products_table.setHorizontalHeaderLabels(headers)
        
        # Configure table
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name column
        
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    
    def refresh_data(self):
        """Refresh inventory data"""
        if not self.current_user:
            self.status_label.setText("Usuario no configurado")
            return
        
        try:
            with SessionLocal() as db:
                self.inventory_service = InventoryService(db)
                products = self.inventory_service.get_all_products(self.current_user)
                self.populate_table(products)
                self.update_categories(products)
                self.status_label.setText(f"Mostrando {len(products)} productos")
                
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            print(f"Error refreshing inventory: {e}")
    
    def populate_table(self, products):
        """Populate products table"""
        self.products_table.setRowCount(0)
        
        for row, product in enumerate(products):
            self.products_table.insertRow(row)
            
            # Product data
            self.products_table.setItem(row, 0, QTableWidgetItem(product.code or ""))
            self.products_table.setItem(row, 1, QTableWidgetItem(product.name or ""))
            self.products_table.setItem(row, 2, QTableWidgetItem(product.category or ""))
            self.products_table.setItem(row, 3, QTableWidgetItem(str(product.current_stock or 0)))
            self.products_table.setItem(row, 4, QTableWidgetItem(str(product.minimum_stock or 0)))
            self.products_table.setItem(row, 5, QTableWidgetItem(str(product.purchase_price or 0)))
            self.products_table.setItem(row, 6, QTableWidgetItem(str(product.sale_price or 0)))
            
            # Status
            status_text = "Activo" if product.is_active else "Inactivo"
            status_item = QTableWidgetItem(status_text)
            status_item.setStyleSheet(
                "color: green;" if product.is_active else "color: red;"
            )
            self.products_table.setItem(row, 7, status_item)
            
            # Color low stock items
            if product.current_stock and product.minimum_stock:
                if product.current_stock <= product.minimum_stock:
                    for col in range(4):  # Color first 4 columns
                        item = self.products_table.item(row, col)
                        if item:
                            item.setBackground(Qt.GlobalColor.yellow)
    
    def update_categories(self, products):
        """Update categories dropdown"""
        categories = set()
        for product in products:
            if product.category:
                categories.add(product.category)
        
        self.category_combo.clear()
        self.category_combo.addItem("Todas las categorías")
        for category in sorted(categories):
            self.category_combo.addItem(category)
    
    def filter_products(self):
        """Filter products based on search"""
        search_text = self.search_edit.text().lower()
        
        for row in range(self.products_table.rowCount()):
            match = False
            for col in range(3):  # Check first 3 columns
                item = self.products_table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            
            self.products_table.setRowHidden(row, not match)
    
    def add_product(self):
        """Add new product"""
        if not self.current_user:
            QMessageBox.warning(self, "Error", "Usuario no configurado")
            return
        
        dialog = AddProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            product_data = dialog.get_product_data()
            
            if not product_data['name']:
                QMessageBox.warning(self, "Error", "El nombre del producto es obligatorio")
                return
            
            try:
                with SessionLocal() as db:
                    service = ProductService(db)
                    
                    # Create product
                    product = Product(
                        id=uuid.uuid4(),
                        code=product_data['code'],
                        name=product_data['name'],
                        description=product_data['description'],
                        category=product_data['category'],
                        purchase_price=product_data['purchase_price'],
                        sale_price=product_data['sale_price'],
                        current_stock=product_data['current_stock'],
                        minimum_stock=product_data['minimum_stock'],
                        stock_unit=product_data['stock_unit'],
                        is_active=product_data['is_active']
                    )
                    
                    service.create_product(self.current_user, product)
                    
                    # Create stock movement if initial stock > 0
                    if product_data['current_stock'] > 0:
                        inventory_service = InventoryService(db)
                        inventory_service.create_stock_movement(
                            self.current_user,
                            product.id,
                            "initial",
                            product_data['current_stock'],
                            "Stock inicial"
                        )
                    
                    db.commit()
                    QMessageBox.information(self, "Éxito", "Producto añadido correctamente")
                    self.refresh_data()
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al añadir producto: {str(e)}")
    
    def adjust_stock(self):
        """Adjust product stock"""
        selection = self.products_table.selectedItems()
        if not selection:
            QMessageBox.information(self, "Info", "Seleccione un producto primero")
            return
        
        row = selection[0].row()
        product_code = self.products_table.item(row, 0).text()
        
        if not self.current_user:
            QMessageBox.warning(self, "Error", "Usuario no configurado")
            return
        
        # Simple stock adjustment dialog
        quantity, ok = QMessageBox.getInt(
            self, 
            "Ajustar Stock", 
            "Cantidad (+ para añadir, - para quitar):",
            0, -99999, 99999, 1
        )
        
        if ok and quantity != 0:
            try:
                with SessionLocal() as db:
                    service = ProductService(db)
                    product = service.get_product_by_code(product_code)
                    
                    if product:
                        inventory_service = InventoryService(db)
                        movement_type = "in" if quantity > 0 else "out"
                        reason = "Ajuste manual"
                        
                        inventory_service.create_stock_movement(
                            self.current_user,
                            product.id,
                            movement_type,
                            abs(quantity),
                            reason
                        )
                        
                        db.commit()
                        QMessageBox.information(self, "Éxito", f"Stock ajustado: {quantity:+d} unidades")
                        self.refresh_data()
                    else:
                        QMessageBox.warning(self, "Error", "Producto no encontrado")
                        
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al ajustar stock: {str(e)}")