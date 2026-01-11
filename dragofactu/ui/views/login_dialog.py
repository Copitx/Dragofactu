from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QLabel, QMessageBox, QFormLayout,
    QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIntValidator

from dragofactu.models.database import SessionLocal
from dragofactu.services.auth.auth_service import AuthService
from dragofactu.models.entities import User


class LoginDialog(QDialog):
    """Login dialog for user authentication"""
    
    login_successful = Signal(User)
    
    def __init__(self, auth_service: AuthService, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.user = None
        
        self.setWindowTitle("Login - Dragofactu")
        self.setFixedSize(400, 300)
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
        """Setup dialog UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Dragofactu")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Business Management System")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_font = QFont("Arial", 10)
        subtitle_label.setFont(subtitle_font)
        layout.addWidget(subtitle_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Login form
        form_layout = QFormLayout()
        
        # Username field
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username or Email")
        self.username_edit.setMinimumHeight(35)
        form_layout.addRow("Username:", self.username_edit)
        
        # Password field
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setMinimumHeight(35)
        form_layout.addRow("Password:", self.password_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Login")
        self.login_button.setMinimumHeight(40)
        self.login_button.clicked.connect(self.handle_login)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
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