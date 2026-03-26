from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class RemindersView(QWidget):
    """Reminders view placeholder for modular parity shell."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Reminders")
        layout.addWidget(title_label)

        placeholder = QLabel("Phase 4 in progress: reminders modular parity UI is being aligned with web app.")
        placeholder.setWordWrap(True)
        layout.addWidget(placeholder)

    def refresh(self):
        return
