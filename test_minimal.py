#!/usr/bin/env python3
"""
Minimal test to isolate the blocking component
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QDialog
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from dragofactu.models.database import engine, Base, SessionLocal
from dragofactu.config.config import AppConfig, setup_logging
from dragofactu.services.auth.auth_service import AuthService
from dragofactu.ui.views.login_dialog import LoginDialog


def debug_print(message):
    print(f"[DEBUG] {message}")
    sys.stdout.flush()


class TestMainWindow(QMainWindow):
    """Minimal main window without tabs"""
    
    def __init__(self):
        debug_print("TestMainWindow.__init__() starting")
        super().__init__()
        self.current_user = None
        
        debug_print("Setting window properties")
        self.setWindowTitle("TEST Dragofactu - Minimal")
        self.setGeometry(100, 100, 400, 300)
        
        debug_print("Creating central widget")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        debug_print("Creating layout")
        layout = QVBoxLayout(self.central_widget)
        
        from PySide6.QtWidgets import QLabel
        label = QLabel("MINIMAL TEST WINDOW - SUCCESS!")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: green; padding: 50px;")
        layout.addWidget(label)
        
        debug_print("TestMainWindow setup complete")
    
    def set_current_user(self, user):
        debug_print(f"set_current_user called with: {user}")
        self.current_user = user


class TestApp(QApplication):
    def __init__(self):
        debug_print("TestApp.__init__() starting")
        super().__init__(sys.argv)
        
        debug_print("Setting up configuration and logging")
        try:
            AppConfig.ensure_directories()
            setup_logging()
            debug_print("✅ Configuration setup complete")
        except Exception as e:
            debug_print(f"❌ Configuration setup failed: {e}")
        
        debug_print("Setting application properties")
        self.setApplicationName(AppConfig.APP_NAME)
        self.setApplicationVersion(AppConfig.APP_VERSION)
        self.setOrganizationName("Dragofactu")
        
        debug_print("Setting up database")
        try:
            self.setup_database()
            debug_print("✅ Database setup complete")
        except Exception as e:
            debug_print(f"❌ Database setup failed: {e}")
        
        debug_print("Initializing services")
        try:
            self.auth_service = AuthService()
            self.current_user = None
            debug_print("✅ Services initialized")
        except Exception as e:
            debug_print(f"❌ Service initialization failed: {e}")
        
        debug_print("Setting up UI")
        try:
            self.setup_ui()
            debug_print("✅ UI setup complete")
        except Exception as e:
            debug_print(f"❌ UI setup failed: {e}")
        
        debug_print("Showing login dialog")
        try:
            self.show_login()
            debug_print("✅ Login dialog initiated")
        except Exception as e:
            debug_print(f"❌ Login dialog failed: {e}")
    
    def setup_database(self):
        """Create database tables"""
        debug_print("Creating database tables")
        Base.metadata.create_all(bind=engine)
        debug_print("Database tables created")
    
    def setup_ui(self):
        """Setup main UI components"""
        debug_print("Setting application style")
        self.setStyle("Fusion")
        
        debug_print("Setting application font")
        font = QFont("Segoe UI", 9)
        self.setFont(font)
        
        debug_print("Creating main window (hidden initially)")
        self.main_window = TestMainWindow()
        self.main_window.hide()
        debug_print(f"Main window created: {self.main_window}")
        debug_print(f"Main window visible: {self.main_window.isVisible()}")
    
    def show_login(self):
        """Show login dialog"""
        debug_print("Creating login dialog")
        try:
            login_dialog = LoginDialog(self.auth_service)
            debug_print(f"Login dialog created: {login_dialog}")
            
            debug_print("Executing login dialog")
            result = login_dialog.exec()
            debug_print(f"Login dialog result: {result}")
            
            if result == QDialog.DialogCode.Accepted:
                debug_print("Login accepted - setting up main window")
                # Refresh user with new session to avoid DetachedInstanceError
                with SessionLocal() as db:
                    self.current_user = db.merge(login_dialog.user)
                    debug_print(f"Current user set: {self.current_user}")
                    
                    self.main_window.set_current_user(self.current_user)
                    
                    debug_print("About to show main window")
                    debug_print(f"Before show - visible: {self.main_window.isVisible()}")
                    
                    self.main_window.show()
                    self.main_window.raise_()
                    self.main_window.activateWindow()
                    
                    debug_print(f"After show - visible: {self.main_window.isVisible()}")
                    debug_print("Main window should now be visible")
            else:
                debug_print("Login cancelled - quitting")
                self.quit()
                
        except Exception as e:
            debug_print(f"❌ Login dialog error: {e}")
            import traceback
            debug_print(f"Traceback: {traceback.format_exc()}")


def main():
    """Main application entry point with debug logging"""
    debug_print("=== MINIMAL TEST STARTUP ===")
    
    try:
        debug_print("Creating QApplication")
        app = TestApp()
        debug_print("QApplication created successfully")
        
        debug_print("Starting event loop")
        result = app.exec()
        debug_print(f"Event loop ended with result: {result}")
        
    except KeyboardInterrupt:
        debug_print("Application stopped by user")
    except Exception as e:
        debug_print(f"Fatal error: {e}")
        import traceback
        debug_print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()