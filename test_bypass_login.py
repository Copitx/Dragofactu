#!/usr/bin/env python3
"""
Test main application without login to verify window visibility
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from dragofactu.models.database import engine, Base, SessionLocal
from dragofactu.config.config import AppConfig, setup_logging
from dragofactu.ui.views.main_window import MainWindow


def debug_print(message):
    print(f"[DEBUG] {message}")
    sys.stdout.flush()


class TestBypassLoginApp(QApplication):
    def __init__(self):
        debug_print("TestBypassLoginApp.__init__() starting")
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
        
        debug_print("Auto-login as admin")
        try:
            self.auto_login()
            debug_print("✅ Auto-login complete")
        except Exception as e:
            debug_print(f"❌ Auto-login failed: {e}")
        
        debug_print("Setting up UI")
        try:
            self.setup_ui()
            debug_print("✅ UI setup complete")
        except Exception as e:
            debug_print(f"❌ UI setup failed: {e}")
        
        debug_print("Application setup complete - main window should be visible")
    
    def setup_database(self):
        """Create database tables"""
        debug_print("Creating database tables")
        Base.metadata.create_all(bind=engine)
        debug_print("Database tables created")
    
    def auto_login(self):
        """Auto-login as admin user"""
        with SessionLocal() as db:
            from dragofactu.models.entities import User
            admin_user = db.query(User).filter(User.username == 'admin').first()
            if admin_user:
                self.current_user = admin_user
                debug_print(f"Admin user found: {admin_user.full_name}")
            else:
                raise Exception("Admin user not found")
    
    def setup_ui(self):
        """Setup main UI components"""
        debug_print("Setting application style")
        self.setStyle("Fusion")
        
        debug_print("Setting application font")
        font = QFont("Segoe UI", 9)
        self.setFont(font)
        
        debug_print("Creating main window")
        try:
            self.main_window = MainWindow()
            debug_print(f"Main window created: {self.main_window}")
            debug_print(f"Main window visible: {self.main_window.isVisible()}")
        except Exception as e:
            debug_print(f"❌ Main window creation failed: {e}")
            import traceback
            debug_print(f"Traceback: {traceback.format_exc()}")
            return
        
        debug_print("Setting current user on main window")
        self.main_window.set_current_user(self.current_user)
        
        debug_print("About to show main window")
        debug_print(f"Before show - visible: {self.main_window.isVisible()}")
        
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        
        debug_print(f"After show - visible: {self.main_window.isVisible()}")
        debug_print("Main window should now be visible")


def main():
    """Main application entry point with debug logging"""
    debug_print("=== BYPASS LOGIN TEST STARTUP ===")
    
    try:
        debug_print("Creating QApplication")
        app = TestBypassLoginApp()
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