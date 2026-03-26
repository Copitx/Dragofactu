from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

from dragofactu.models.database import SessionLocal
from dragofactu.models.entities import Reminder


class RemindersView(QWidget):
    """Reminders list view for modular parity shell."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Reminders")
        layout.addWidget(title_label)

        toolbar = QHBoxLayout()
        self.priority_filter = QComboBox()
        self.priority_filter.addItem("All priorities", "")
        self.priority_filter.addItems(["low", "normal", "high"])
        self.priority_filter.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.priority_filter)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setProperty("secondary", "true")
        self.refresh_button.clicked.connect(self.refresh)
        toolbar.addWidget(self.refresh_button)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Title", "Priority", "Due Date", "Completed"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setProperty("secondary", "true")
        layout.addWidget(self.status_label)

        self.refresh()

    def refresh(self):
        selected_priority = self.priority_filter.currentText().strip() if hasattr(self, "priority_filter") else ""
        with SessionLocal() as db:
            reminders = db.query(Reminder).order_by(Reminder.created_at.desc()).all()

        if selected_priority and selected_priority != "All priorities":
            reminders = [r for r in reminders if (r.priority or "normal") == selected_priority]

        self.table.setRowCount(len(reminders))
        for row, reminder in enumerate(reminders):
            self.table.setItem(row, 0, QTableWidgetItem(reminder.title or ""))
            self.table.setItem(row, 1, QTableWidgetItem(reminder.priority or "normal"))
            self.table.setItem(row, 2, QTableWidgetItem(str(reminder.due_date.date()) if reminder.due_date else ""))
            self.table.setItem(row, 3, QTableWidgetItem("Yes" if reminder.is_completed else "No"))
            for col in range(4):
                item = self.table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.status_label.setText(f"{len(reminders)} reminders loaded")
