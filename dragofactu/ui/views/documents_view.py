from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

from dragofactu.models.database import SessionLocal
from dragofactu.models.entities import Document

class DocumentsView(QWidget):
    """Documents management view"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup documents UI"""
        layout = QVBoxLayout(self)

        title_label = QLabel("Documents")
        title_label.setText("Documents Management")
        layout.addWidget(title_label)

        toolbar = QHBoxLayout()
        self.status_filter = QComboBox()
        self.status_filter.addItem("All statuses", "")
        self.status_filter.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.status_filter)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setProperty("secondary", "true")
        self.refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(self.refresh_button)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Code", "Type", "Status", "Issue Date", "Client ID", "Total"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setProperty("secondary", "true")
        layout.addWidget(self.status_label)

        self.refresh()
    
    def refresh(self):
        """Refresh documents view"""
        with SessionLocal() as db:
            documents = db.query(Document).order_by(Document.created_at.desc()).all()

        statuses = sorted({(d.status.value if d.status else "") for d in documents if d.status})
        current_status = self.status_filter.currentData() if hasattr(self, "status_filter") else ""
        self.status_filter.blockSignals(True)
        self.status_filter.clear()
        self.status_filter.addItem("All statuses", "")
        for st in statuses:
            self.status_filter.addItem(st, st)
        idx = self.status_filter.findData(current_status)
        self.status_filter.setCurrentIndex(max(0, idx))
        self.status_filter.blockSignals(False)

        if current_status:
            documents = [d for d in documents if d.status and d.status.value == current_status]

        self.table.setRowCount(len(documents))
        for row, doc in enumerate(documents):
            self.table.setItem(row, 0, QTableWidgetItem(doc.code or ""))
            self.table.setItem(row, 1, QTableWidgetItem(doc.type.value if doc.type else ""))
            self.table.setItem(row, 2, QTableWidgetItem(doc.status.value if doc.status else ""))
            self.table.setItem(row, 3, QTableWidgetItem(str(doc.issue_date.date()) if doc.issue_date else ""))
            self.table.setItem(row, 4, QTableWidgetItem(str(doc.client_id or "")))
            self.table.setItem(row, 5, QTableWidgetItem(str(doc.total or 0)))
            for col in range(6):
                item = self.table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.status_label.setText(f"{len(documents)} documents loaded")