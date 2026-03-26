from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton

from dragofactu.models.database import SessionLocal
from dragofactu.models.entities import Document, Product


class ReportsView(QWidget):
    """Reports KPI view for modular parity shell."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Reports")
        layout.addWidget(title_label)

        self.grid = QGridLayout()
        self.total_documents = QLabel()
        self.total_revenue = QLabel()
        self.total_products = QLabel()
        self.low_stock = QLabel()

        self.grid.addWidget(self.total_documents, 0, 0)
        self.grid.addWidget(self.total_revenue, 0, 1)
        self.grid.addWidget(self.total_products, 1, 0)
        self.grid.addWidget(self.low_stock, 1, 1)
        layout.addLayout(self.grid)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setProperty("secondary", "true")
        self.refresh_button.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_button)

        self.refresh()

    def refresh(self):
        with SessionLocal() as db:
            docs = db.query(Document).all()
            products = db.query(Product).filter(Product.is_active == True).all()

        total_documents = len(docs)
        total_revenue = float(sum(float(d.total or 0) for d in docs))
        total_products = len(products)
        low_stock = len([p for p in products if (p.current_stock or 0) <= (p.minimum_stock or 0)])

        self.total_documents.setText(f"Total documents: {total_documents}")
        self.total_revenue.setText(f"Total revenue: {total_revenue:.2f}")
        self.total_products.setText(f"Active products: {total_products}")
        self.low_stock.setText(f"Low stock products: {low_stock}")
