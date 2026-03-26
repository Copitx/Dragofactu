# Dragofactu - Professional Business Management System

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from dragofactu.models.database import engine, Base, SessionLocal
from dragofactu.config.config import AppConfig, setup_logging
from dragofactu.services.auth.auth_service import AuthService
from dragofactu.ui.styles import apply_stylesheet
from dragofactu.ui.views.login_dialog import LoginDialog
from dragofactu.ui.views.main_window import MainWindow


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

        # Apply global desktop design tokens/styles.
        apply_stylesheet(self)
        
        # Set application font
        font = QFont("Segoe UI", 9)
        self.setFont(font)
        
        # Create main window (hidden initially)
        self.main_window = MainWindow()
        self.main_window.hide()
    
    def show_login(self):
        """Show login dialog.

        Headless auto-login is disabled by default for security reasons.
        It can be explicitly enabled for controlled CI/dev scenarios with:
        DRAGOFACTU_ALLOW_HEADLESS_AUTOLOGIN=true
        """
        is_linux = sys.platform.startswith('linux')
        headless_env = os.environ.get('QT_QPA_PLATFORM') == 'offscreen' or (is_linux and not os.environ.get('DISPLAY'))
        allow_headless_autologin = os.environ.get('DRAGOFACTU_ALLOW_HEADLESS_AUTOLOGIN', '').lower() == 'true'

        if headless_env and allow_headless_autologin:
            with SessionLocal() as db:
                from dragofactu.models.entities import User
                admin_user = db.query(User).filter(User.username == 'admin').first()
                if admin_user:
                    self.current_user = admin_user
                    self.main_window.set_current_user(self.current_user)
                    self.main_window.show()
                    self.main_window.raise_()
                    self.main_window.activateWindow()
                    return

        if headless_env:
            print("Headless environment detected. Interactive login is required; auto-login is disabled by default.")
            self.quit()
            return
        
        # Normal interactive login for GUI environments
        login_dialog = LoginDialog(self.auth_service)
        
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh user with new session to avoid DetachedInstanceError
            with SessionLocal() as db:
                self.current_user = db.merge(login_dialog.user)
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