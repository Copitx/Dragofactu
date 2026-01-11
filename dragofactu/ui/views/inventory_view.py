from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QLineEdit, QComboBox, QMessageBox, QDialog, QFormLayout,
    QSpinBox, QHeaderView, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from models.database import SessionLocal
from services.inventory.inventory_service import InventoryService
from services.business.entity_services import ProductService
from services.auth.auth_service import PermissionService


class StockAdjustmentDialog(QDialog):
    """Dialog for stock adjustments"""
    
    def __init__(self, parent=None, product=None, user_id=None):
        super().__init__(parent)
        self.product = product
        self.user_id = user_id
        self.inventory_service = None
        
        self.setWindowTitle("Stock Adjustment")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        self.setup_ui()
        
        if product:
            self.load_product(product)
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Product info
        self.product_label = QLabel("Select a product")
        form_layout.addRow("Product:", self.product_label)
        
        # Current stock
        self.current_stock_label = QLabel("-")
        form_layout.addRow("Current Stock:", self.current_stock_label)
        
        # New stock
        self.new_stock_spin = QSpinBox()
        self.new_stock_spin.setRange(0, 99999)
        form_layout.addRow("New Stock:", self.new_stock_spin)
        
        # Reason
        self.reason_edit = QLineEdit()
        self.reason_edit.setPlaceholderText("Reason for adjustment...")
        form_layout.addRow("Reason:", self.reason_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.adjust_button = QPushButton("Adjust Stock")
        self.adjust_button.clicked.connect(self.perform_adjustment)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.adjust_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_product(self, product):
        """Load product data"""
        self.product = product
        self.product_label.setText(f"{product.code} - {product.name}")
        self.current_stock_label.setText(str(product.current_stock))
        self.new_stock_spin.setValue(product.current_stock)
    
    def perform_adjustment(self):
        """Perform the stock adjustment"""
        if not self.product:
            QMessageBox.warning(self, "Warning", "Please select a product")
            return
        
        new_stock = self.new_stock_spin.value()
        reason = self.reason_edit.text().strip()
        
        if new_stock == self.product.current_stock:
            QMessageBox.information(self, "Info", "No change in stock quantity")
            return
        
        try:
            with SessionLocal() as db:
                self.inventory_service = InventoryService(db)
                result = self.inventory_service.adjust_stock(
                    product_id=str(self.product.id),
                    new_quantity=new_stock,
                    reason=reason or "Manual adjustment",
                    reference_type="manual_adjustment",
                    user_id=self.user_id
                )
                
                if result['success']:
                    QMessageBox.information(self, "Success", result['message'])
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", result['message'])
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to adjust stock: {str(e)}")


class InventoryView(QWidget):
    """Inventory management view"""
    
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.permission_service = PermissionService()
        self.inventory_service = None
        self.product_service = None
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Setup inventory UI"""
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search products...")
        self.search_edit.textChanged.connect(self.on_search_changed)
        toolbar_layout.addWidget(QLabel("Search:"))
        toolbar_layout.addWidget(self.search_edit)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        toolbar_layout.addWidget(QLabel("Category:"))
        toolbar_layout.addWidget(self.category_combo)
        
        self.low_stock_only = QCheckBox("Low Stock Only")
        self.low_stock_only.stateChanged.connect(self.on_filter_changed)
        toolbar_layout.addWidget(self.low_stock_only)
        
        toolbar_layout.addStretch()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        toolbar_layout.addWidget(self.refresh_button)
        
        self.adjust_button = QPushButton("Adjust Stock")
        self.adjust_button.clicked.connect(self.adjust_selected_stock)
        toolbar_layout.addWidget(self.adjust_button)
        
        layout.addLayout(toolbar_layout)
        
        # Summary section
        summary_frame = QFrame()
        summary_layout = QHBoxLayout(summary_frame)
        
        self.total_products_label = QLabel("Total Products: 0")
        self.low_stock_label = QLabel("Low Stock: 0")
        self.total_value_label = QLabel("Total Value: €0.00")
        
        summary_layout.addWidget(self.total_products_label)
        summary_layout.addWidget(self.low_stock_label)
        summary_layout.addWidget(self.total_value_label)
        summary_layout.addStretch()
        
        layout.addWidget(summary_frame)
        
        # Table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(8)
        self.inventory_table.setHorizontalHeaderLabels([
            "Code", "Name", "Category", "Current Stock", 
            "Min Stock", "Unit", "Purchase Price", "Status"
        ])
        
        # Configure table
        header = self.inventory_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.inventory_table.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        layout.addWidget(self.inventory_table)
        
        self.setLayout(layout)
        
        # Update UI based on permissions
        self.update_permissions()
        
        # Apply styles
        self.apply_styles()
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f8f8f8;
                padding: 5px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #0078d4;
                background-color: #0078d4;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled {
                background-color: #ccc;
                border-color: #999;
            }
        """)
    
    def update_permissions(self):
        """Update UI based on user permissions"""
        if not self.current_user:
            return
        
        can_adjust = self.permission_service.has_permission(self.current_user, 'inventory.adjust')
        self.adjust_button.setEnabled(can_adjust)
    
    def refresh(self):
        """Refresh inventory data"""
        try:
            with SessionLocal() as db:
                self.inventory_service = InventoryService(db)
                self.product_service = ProductService(db)
                
                # Load inventory data
                self.load_inventory_data()
                
                # Load summary
                self.load_summary()
                
                # Load categories
                self.load_categories()
        
        except Exception as e:
            self.inventory_table.setRowCount(1)
            self.inventory_table.setColumnCount(1)
            self.inventory_table.setHorizontalHeaderLabels(["Error"])
            self.inventory_table.setItem(0, 0, QTableWidgetItem(f"Error loading data: {str(e)}"))
    
    def load_inventory_data(self):
        """Load inventory data into table"""
        category = self.category_combo.currentText()
        low_stock_only = self.low_stock_only.isChecked()
        
        if category == "All Categories":
            category = None
        
        stock_levels = self.inventory_service.get_stock_levels(
            category=category,
            low_stock_only=low_stock_only
        )
        
        self.inventory_table.setRowCount(len(stock_levels))
        
        for row, stock_info in enumerate(stock_levels):
            # Code
            self.inventory_table.setItem(row, 0, QTableWidgetItem(stock_info['code']))
            
            # Name
            self.inventory_table.setItem(row, 1, QTableWidgetItem(stock_info['name']))
            
            # Category
            self.inventory_table.setItem(row, 2, QTableWidgetItem(stock_info['category'] or ""))
            
            # Current Stock
            current_stock = QTableWidgetItem(str(stock_info['current_stock']))
            self.inventory_table.setItem(row, 3, current_stock)
            
            # Min Stock
            self.inventory_table.setItem(row, 4, QTableWidgetItem(str(stock_info['minimum_stock'])))
            
            # Unit
            self.inventory_table.setItem(row, 5, QTableWidgetItem(stock_info['stock_unit']))
            
            # Purchase Price
            price_text = f"€{stock_info['purchase_price']:.2f}" if stock_info['purchase_price'] else ""
            self.inventory_table.setItem(row, 6, QTableWidgetItem(price_text))
            
            # Status
            status_item = QTableWidgetItem("Low Stock" if stock_info['is_low_stock'] else "OK")
            if stock_info['is_low_stock']:
                status_item.setBackground(QColor('#ffebee'))
                status_item.setText("Low Stock")
            else:
                status_item.setBackground(QColor('#e8f5e8'))
                status_item.setText("OK")
            
            self.inventory_table.setItem(row, 7, status_item)
            
            # Store full product data
            self.inventory_table.item(row, 0).setData(Qt.UserRole, stock_info)
    
    def load_summary(self):
        """Load and display inventory summary"""
        summary = self.inventory_service.get_inventory_summary()
        
        self.total_products_label.setText(f"Total Products: {summary['total_products']}")
        self.low_stock_label.setText(f"Low Stock: {summary['low_stock_products']}")
        self.total_value_label.setText(f"Total Value: €{summary['total_stock_value']:.2f}")
    
    def load_categories(self):
        """Load product categories"""
        try:
            products = self.product_service.search_products(active_only=True)
            categories = set()
            
            for product in products:
                if product.category:
                    categories.add(product.category)
            
            # Update combo box
            self.category_combo.clear()
            self.category_combo.addItem("All Categories")
            
            for category in sorted(categories):
                self.category_combo.addItem(category)
        
        except Exception as e:
            print(f"Error loading categories: {e}")
    
    def on_search_changed(self, text):
        """Handle search text change"""
        if len(text) >= 3 or len(text) == 0:
            self.perform_search()
    
    def on_category_changed(self):
        """Handle category change"""
        self.load_inventory_data()
    
    def on_filter_changed(self):
        """Handle filter change"""
        self.load_inventory_data()
    
    def perform_search(self):
        """Perform product search"""
        query = self.search_edit.text().strip()
        
        try:
            if not self.inventory_service:
                return
            
            category = self.category_combo.currentText()
            if category == "All Categories":
                category = None
            
            if query:
                # Search by name/code
                products = self.inventory_service.search_products_by_stock(query)
                self.display_search_results(products)
            else:
                # Load all products with current filters
                self.load_inventory_data()
        
        except Exception as e:
            print(f"Search error: {e}")
    
    def display_search_results(self, products):
        """Display search results in table"""
        self.inventory_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            # Code
            self.inventory_table.setItem(row, 0, QTableWidgetItem(product['code']))
            
            # Name
            self.inventory_table.setItem(row, 1, QTableWidgetItem(product['name']))
            
            # Category
            self.inventory_table.setItem(row, 2, QTableWidgetItem(product['category'] or ""))
            
            # Current Stock
            self.inventory_table.setItem(row, 3, QTableWidgetItem(str(product['current_stock'])))
            
            # Min Stock
            self.inventory_table.setItem(row, 4, QTableWidgetItem(str(product['minimum_stock'])))
            
            # Unit
            self.inventory_table.setItem(row, 5, QTableWidgetItem(product.get('stock_unit', 'units')))
            
            # Purchase Price
            self.inventory_table.setItem(row, 6, QTableWidgetItem(""))
            
            # Status
            status_item = QTableWidgetItem("Low Stock" if product['is_low_stock'] else "OK")
            if product['is_low_stock']:
                status_item.setBackground(QColor('#ffebee'))
            else:
                status_item.setBackground(QColor('#e8f5e8'))
            
            self.inventory_table.setItem(row, 7, status_item)
    
    def on_item_double_clicked(self, item):
        """Handle table item double click"""
        row = item.row()
        code_item = self.inventory_table.item(row, 0)
        
        if code_item:
            stock_info = code_item.data(Qt.UserRole)
            if stock_info:
                # Get full product object
                product = self.product_service.get_product_by_id(stock_info['id'])
                if product:
                    self.show_stock_adjustment_dialog(product)
    
    def adjust_selected_stock(self):
        """Adjust stock for selected product"""
        current_row = self.inventory_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Info", "Please select a product to adjust stock")
            return
        
        code_item = self.inventory_table.item(current_row, 0)
        stock_info = code_item.data(Qt.UserRole)
        
        if stock_info:
            product = self.product_service.get_product_by_id(stock_info['id'])
            if product:
                self.show_stock_adjustment_dialog(product)
    
    def show_stock_adjustment_dialog(self, product):
        """Show stock adjustment dialog"""
        dialog = StockAdjustmentDialog(self, product, self.current_user.id)
        if dialog.exec() == QDialog.Accepted:
            self.refresh()
    
    def set_current_user(self, user):
        """Set the current user and refresh"""
        self.current_user = user
        self.update_permissions()
        self.refresh()