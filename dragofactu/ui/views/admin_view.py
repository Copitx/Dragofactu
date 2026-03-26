from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

from dragofactu.models.database import SessionLocal
from dragofactu.models.entities import User, Client, Supplier, Product, Document, Worker, Reminder


class AdminView(QWidget):
    """Admin summary view for modular parity shell."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Admin")
        layout.addWidget(title_label)

        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setProperty("secondary", "true")
        self.refresh_button.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_button)

        self.refresh()

    def refresh(self):
        with SessionLocal() as db:
            users = db.query(User).count()
            clients = db.query(Client).count()
            suppliers = db.query(Supplier).count()
            products = db.query(Product).count()
            documents = db.query(Document).count()
            workers = db.query(Worker).count()
            reminders = db.query(Reminder).count()

        self.summary_label.setText(
            "\n".join([
                f"Users: {users}",
                f"Clients: {clients}",
                f"Suppliers: {suppliers}",
                f"Products: {products}",
                f"Documents: {documents}",
                f"Workers: {workers}",
                f"Reminders: {reminders}",
            ])
        )
