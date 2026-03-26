from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

from dragofactu.models.database import SessionLocal
from dragofactu.models.entities import Worker


class WorkersParityView(QWidget):
    """Workers data view for modular parity shell."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Workers Management")
        layout.addWidget(title_label)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search workers...")
        self.search_edit.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search_edit)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setProperty("secondary", "true")
        self.refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(self.refresh_button)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Code", "Full Name", "Department", "Position", "Phone", "Email"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setProperty("secondary", "true")
        layout.addWidget(self.status_label)

        self.refresh()

    def refresh(self):
        query_text = self.search_edit.text().strip().lower() if hasattr(self, "search_edit") else ""
        with SessionLocal() as db:
            workers = db.query(Worker).filter(Worker.is_active == True).order_by(Worker.full_name.asc()).all()

        if query_text:
            workers = [
                w for w in workers
                if query_text in (w.full_name or "").lower()
                or query_text in (w.code or "").lower()
                or query_text in (w.department or "").lower()
            ]

        self.table.setRowCount(len(workers))
        for row, worker in enumerate(workers):
            self.table.setItem(row, 0, QTableWidgetItem(worker.code or ""))
            self.table.setItem(row, 1, QTableWidgetItem(worker.full_name or ""))
            self.table.setItem(row, 2, QTableWidgetItem(worker.department or ""))
            self.table.setItem(row, 3, QTableWidgetItem(worker.position or ""))
            self.table.setItem(row, 4, QTableWidgetItem(worker.phone or ""))
            self.table.setItem(row, 5, QTableWidgetItem(worker.email or ""))
            for col in range(6):
                item = self.table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.status_label.setText(f"{len(workers)} workers loaded")
