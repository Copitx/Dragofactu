from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class ProductsView(QWidget):
    """Products management view (modular parity track)."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Products Management")
        layout.addWidget(title_label)

        placeholder = QLabel("Phase 3 in progress: full modular products UI is being aligned with web app.")
        placeholder.setWordWrap(True)
        layout.addWidget(placeholder)

    def refresh(self):
        """Refresh products view."""
        return
