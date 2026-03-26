from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

from dragofactu.models.database import SessionLocal
from dragofactu.models.audit import DocumentHistory


class AuditView(QWidget):
    """Audit history view for modular parity shell."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Audit")
        layout.addWidget(title_label)

        toolbar = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setProperty("secondary", "true")
        self.refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(self.refresh_button)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Action", "Document ID", "User ID", "Description"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setProperty("secondary", "true")
        layout.addWidget(self.status_label)

        self.refresh()

    def refresh(self):
        with SessionLocal() as db:
            entries = db.query(DocumentHistory).order_by(DocumentHistory.timestamp.desc()).limit(300).all()

        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(str(entry.timestamp or "")))
            self.table.setItem(row, 1, QTableWidgetItem(entry.action or ""))
            self.table.setItem(row, 2, QTableWidgetItem(str(entry.document_id or "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(entry.user_id or "")))
            self.table.setItem(row, 4, QTableWidgetItem(entry.description or ""))
            for col in range(5):
                item = self.table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.status_label.setText(f"{len(entries)} audit entries loaded")
