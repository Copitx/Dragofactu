from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIntValidator

from dragofactu.models.database import SessionLocal
from dragofactu.services.auth.auth_service import AuthService
from dragofactu.models.entities import User
from dragofactu.ui.styles import get_card_style, get_primary_button_style, get_secondary_button_style


class LoginDialog(QDialog):
    """Login dialog for user authentication"""
    
    login_successful = Signal(User)
    
    def __init__(self, auth_service: AuthService, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.user = None
        
        self.setWindowTitle("Login - Dragofactu")
        self.setFixedSize(420, 480)  # Increased size for proper spacing
        self.setModal(True)
        
        # Center on screen
        self.move_to_center()
        
        self.setup_ui()
    
    def move_to_center(self):
        """Center dialog on screen"""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def setup_ui(self):
        """Setup dialog UI with Apple-style card layout"""
        # Main layout with 32px margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)
        
        # Card container
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(get_card_style())
        
        # Card layout
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(24)
        card_layout.setContentsMargins(32, 32, 32, 32)
        
        # Title section
        title_section = QVBoxLayout()
        title_section.setSpacing(8)
        title_section.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Main title
        title_label = QLabel("Dragofactu")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"""
            font-family: system-ui, -apple-system, "SF Pro Display", "Segoe UI", sans-serif;
            font-size: 28px;
            font-weight: 600;
            color: #1D1D1F;
            margin-bottom: 4px;
        """)
        
        # Subtitle
        subtitle_label = QLabel("Business Management System")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"""
            font-family: system-ui, -apple-system, "SF Pro Display", "Segoe UI", sans-serif;
            font-size: 15px;
            color: #6E6E73;
            margin-bottom: 8px;
        """)
        
        title_section.addWidget(title_label)
        title_section.addWidget(subtitle_label)
        card_layout.addLayout(title_section)
        
        # Form section - using vertical layout for labels ABOVE inputs
        form_section = QVBoxLayout()
        form_section.setSpacing(16)
        form_section.setContentsMargins(0, 8, 0, 8)

        # Shared input style
        input_style = """
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #D2D2D7;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: #1D1D1F;
                font-family: system-ui, -apple-system, "SF Pro Display", "Segoe UI", sans-serif;
            }
            QLineEdit:focus {
                border-color: #007AFF;
            }
        """

        # Shared label style
        label_style = """
            font-family: system-ui, -apple-system, "SF Pro Display", "Segoe UI", sans-serif;
            font-size: 13px;
            font-weight: 500;
            color: #1D1D1F;
            padding: 0px;
            margin: 0px;
        """

        # Username field group (label above input)
        username_group = QVBoxLayout()
        username_group.setSpacing(6)

        username_label = QLabel("Username")
        username_label.setStyleSheet(label_style)
        username_group.addWidget(username_label)

        self.username_edit = QLineEdit()
        self.username_edit.setMinimumHeight(40)
        self.username_edit.setStyleSheet(input_style)
        username_group.addWidget(self.username_edit)

        form_section.addLayout(username_group)

        # Password field group (label above input)
        password_group = QVBoxLayout()
        password_group.setSpacing(6)

        password_label = QLabel("Password")
        password_label.setStyleSheet(label_style)
        password_group.addWidget(password_label)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setMinimumHeight(40)
        self.password_edit.setStyleSheet(input_style)
        password_group.addWidget(self.password_edit)

        form_section.addLayout(password_group)

        card_layout.addLayout(form_section)
        
        # Buttons section
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(get_secondary_button_style())
        self.cancel_button.clicked.connect(self.reject)
        
        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet(get_primary_button_style())
        self.login_button.clicked.connect(self.handle_login)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.login_button)
        
        card_layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            font-family: system-ui, -apple-system, "SF Pro Display", "Segoe UI", sans-serif;
            font-size: 12px;
            color: #FF3B30;
            padding: 8px 0px;
        """)
        card_layout.addWidget(self.status_label)
        
        # Add card to main layout
        main_layout.addWidget(card)
        
        # Set default focus and Enter key
        self.username_edit.setFocus()
        self.login_button.setDefault(True)
        
        # Connect Enter key for password field
        self.password_edit.returnPressed.connect(self.handle_login)
    
    def handle_login(self):
        """Handle login attempt"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            self.status_label.setText("Please enter username and password")
            return
        
        try:
            with SessionLocal() as db:
                user = self.auth_service.authenticate(db, username, password)
                
                if user:
                    self.user = user
                    self.status_label.setText("")
                    self.accept()
                else:
                    self.status_label.setText("Invalid username or password")
                    self.password_edit.clear()
                    self.password_edit.setFocus()
        
        except Exception as e:
            self.status_label.setText(f"Login error: {str(e)}")
    
    def get_user(self):
        """Get authenticated user"""
        return self.user