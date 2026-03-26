from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

from dragofactu.models.database import SessionLocal
from dragofactu.models.entities import Product


class ProductsView(QWidget):
    """Products management view (modular parity track)."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Products Management")
        layout.addWidget(title_label)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search products...")
        self.search_edit.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search_edit)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setProperty("secondary", "true")
        self.refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(self.refresh_button)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Code", "Name", "Category", "Stock", "Min Stock", "Price"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setProperty("secondary", "true")
        layout.addWidget(self.status_label)

        self.refresh()

    def refresh(self):
        """Refresh products view."""
        query_text = self.search_edit.text().strip().lower() if hasattr(self, "search_edit") else ""
        with SessionLocal() as db:
            products = db.query(Product).filter(Product.is_active == True).order_by(Product.name.asc()).all()

        if query_text:
            products = [
                p for p in products
                if query_text in (p.name or "").lower()
                or query_text in (p.code or "").lower()
                or query_text in (p.category or "").lower()
            ]

        self.table.setRowCount(len(products))
        for row, product in enumerate(products):
            self.table.setItem(row, 0, QTableWidgetItem(product.code or ""))
            self.table.setItem(row, 1, QTableWidgetItem(product.name or ""))
            self.table.setItem(row, 2, QTableWidgetItem(product.category or ""))
            self.table.setItem(row, 3, QTableWidgetItem(str(product.current_stock or 0)))
            self.table.setItem(row, 4, QTableWidgetItem(str(product.minimum_stock or 0)))
            self.table.setItem(row, 5, QTableWidgetItem(str(product.sale_price or 0)))
            for col in range(6):
                item = self.table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.status_label.setText(f"{len(products)} products loaded")
