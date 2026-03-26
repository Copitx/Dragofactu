from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

from dragofactu.models.database import SessionLocal
from dragofactu.models.entities import Supplier


class SuppliersView(QWidget):
    """Suppliers management view (modular parity track)."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Suppliers Management")
        layout.addWidget(title_label)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search suppliers...")
        self.search_edit.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search_edit)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setProperty("secondary", "true")
        self.refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(self.refresh_button)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Code", "Name", "Tax ID", "Phone", "Email"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setProperty("secondary", "true")
        layout.addWidget(self.status_label)

        self.refresh()

    def refresh(self):
        """Refresh suppliers view."""
        query_text = self.search_edit.text().strip().lower() if hasattr(self, "search_edit") else ""
        with SessionLocal() as db:
            suppliers = db.query(Supplier).filter(Supplier.is_active == True).order_by(Supplier.name.asc()).all()

        if query_text:
            suppliers = [
                s for s in suppliers
                if query_text in (s.name or "").lower()
                or query_text in (s.code or "").lower()
                or query_text in (s.email or "").lower()
            ]

        self.table.setRowCount(len(suppliers))
        for row, supplier in enumerate(suppliers):
            self.table.setItem(row, 0, QTableWidgetItem(supplier.code or ""))
            self.table.setItem(row, 1, QTableWidgetItem(supplier.name or ""))
            self.table.setItem(row, 2, QTableWidgetItem(supplier.tax_id or ""))
            self.table.setItem(row, 3, QTableWidgetItem(supplier.phone or ""))
            self.table.setItem(row, 4, QTableWidgetItem(supplier.email or ""))
            for col in range(5):
                item = self.table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.status_label.setText(f"{len(suppliers)} suppliers loaded")
