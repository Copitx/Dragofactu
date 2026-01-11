# Dragofactu - Professional Business Management System

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from models.database import engine, Base
from config.config import AppConfig, setup_logging
from services.auth.auth_service import AuthService
from ui.views.login_dialog import LoginDialog
from ui.views.main_window import MainWindow


class DragofactuApp(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        
        # Setup configuration and logging
        AppConfig.ensure_directories()
        setup_logging()
        
        # Application setup
        self.setApplicationName(AppConfig.APP_NAME)
        self.setApplicationVersion(AppConfig.APP_VERSION)
        self.setOrganizationName("Dragofactu")
        
        # Database setup
        self.setup_database()
        
        # Initialize services
        self.auth_service = AuthService()
        self.current_user = None
        
        # Setup UI
        self.setup_ui()
        
        # Show login dialog
        self.show_login()
    
    def setup_database(self):
        """Create database tables"""
        Base.metadata.create_all(bind=engine)
    
    def setup_ui(self):
        """Setup main UI components"""
        # Set application style
        self.setStyle("Fusion")
        
        # Set application font
        font = QFont("Segoe UI", 9)
        self.setFont(font)
        
        # Create main window (hidden initially)
        self.main_window = MainWindow()
        self.main_window.hide()
    
    def show_login(self):
        """Show login dialog"""
        login_dialog = LoginDialog(self.auth_service)
        
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_user = login_dialog.user
            self.main_window.set_current_user(self.current_user)
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
        else:
            self.quit()
    
    def logout(self):
        """Logout current user and show login dialog"""
        self.current_user = None
        self.main_window.hide()
        self.show_login()


def main():
    """Main application entry point"""
    app = DragofactuApp()
    
    # Set up periodic tasks if needed
    # timer = QTimer()
    # timer.timeout.connect(check_notifications)
    # timer.start(60000)  # Check every minute
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()