from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox

from dragofactu.config.config import AppConfig


class SettingsView(QWidget):
    """Settings view for modular parity shell."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        default_language = getattr(AppConfig, "DEFAULT_LANGUAGE", "es")

        title_label = QLabel("Settings")
        layout.addWidget(title_label)

        info = QLabel(
            f"Application: {AppConfig.APP_NAME}\n"
            f"Version: {AppConfig.APP_VERSION}\n"
            f"Language: {default_language}\n"
            f"Debug mode: {'on' if AppConfig.DEBUG else 'off'}"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        button_row = QHBoxLayout()
        self.reload_button = QPushButton("Reload UI")
        self.reload_button.setProperty("secondary", "true")
        self.reload_button.clicked.connect(self.on_reload)
        button_row.addWidget(self.reload_button)

        self.about_button = QPushButton("About")
        self.about_button.setProperty("secondary", "true")
        self.about_button.clicked.connect(self.on_about)
        button_row.addWidget(self.about_button)
        button_row.addStretch(1)

        layout.addLayout(button_row)

    def refresh(self):
        return

    def on_reload(self):
        QMessageBox.information(self, "Settings", "UI settings reloaded.")

    def on_about(self):
        QMessageBox.information(self, "About", f"{AppConfig.APP_NAME} {AppConfig.APP_VERSION}")
