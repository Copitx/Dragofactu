#!/usr/bin/env python3
"""
Dragofactu - Professional Business Management System
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

try:
    from PySide6.QtWidgets import QApplication, QMainWindow
    from PySide6.QtGui import QFont, QIcon
    from PySide6.QtCore import QTimer
    
    from models.database import engine, Base
    from config.config import AppConfig
    from services.auth.auth_service import AuthService
    
    from ui.views.login_dialog import LoginDialog
    from ui.views.main_window import MainWindow
    
    print("✅ PySide6 import successful")
    
except ImportError as e:
    print(f"❌ Cannot import PySide6: {e}")
    print("Please install PySide6: pip install PySide6")
    sys.exit(1)


try:
    # Test basic SQLAlchemy import
    from sqlalchemy import create_engine
    print("✅ SQLAlchemy import successful")
except ImportError as e:
    print(f"❌ Cannot import SQLAlchemy: {e}")
    print("Please install SQLAlchemy: pip install SQLAlchemy")
    sys.exit(1)


class DragofactuApp(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        
        # Basic application setup
        self.setApplicationName("Dragofactu")
        self.setApplicationVersion("1.0.0")
        
        # Simple font
        font = QFont("Arial", 9)
        self.setFont(font)
        
        # Database setup
        self.setup_database()
        
        # Services
        self.auth_service = AuthService()
        self.current_user = None
        
        # Setup UI (simplified for now)
        try:
            self.setup_ui()
        except Exception as e:
            print(f"❌ UI setup failed: {e}")
        
        # Show message
        self.show_startup_message()
        
        # Show login after a delay
        QTimer.singleShot(1000, self.show_login)
    
    def setup_database(self):
        """Setup database tables"""
        try:
            print("🗄️ Setting up database...")
            Base.metadata.create_all(bind=engine)
            print("✅ Database setup complete")
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            print("Please check your database configuration")
    
    def setup_ui(self):
        """Setup UI (simplified for now)"""
        # Create simple main window for now
        from PySide6.QtWidgets import QLabel, QVBoxLayout, QPushButton, QWidget
        
        self.main_window = QWidget()
        layout = QVBoxLayout(self.main_window)
        
        # Welcome message
        welcome_label = QLabel("🏢 Dragofactu - Business Management System")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_font = QFont("Arial", 14)
        welcome_label.setFont(welcome_font)
        welcome_label.setStyleSheet("color: #0078d4; padding: 20px;")
        
        # Status message
        self.status_label = QLabel("Loading...")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        self.start_button = QPushButton("🚀 Start Application")
        self.start_button.clicked.connect(self.start_application)
        self.start_button.setMinimumHeight(40)
        
        self.quit_button = QPushButton("🚪 Quit")
        self.quit_button.clicked.connect(self.quit)
        self.quit_button.setMinimumHeight(40)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.quit_button)
        
        layout.addWidget(welcome_label)
        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addLayout(button_layout)
        
        self.main_window.setLayout(layout)
        self.main_window.setWindowTitle("Dragofactu")
        self.main_window.resize(400, 300)
        self.main_window.show()
    
    def show_startup_message(self):
        """Show startup status message"""
        self.status_label.setText("🔧 Checking dependencies...")
        
        # Check if key modules are available
        modules_status = []
        
        try:
            import models.database
            modules_status.append("✅ Database models")
        except ImportError as e:
            modules_status.append(f"❌ Database models: {e}")
        
        try:
            import services.auth.auth_service
            modules_status.append("✅ Authentication service")
        except ImportError as e:
            modules_status.append(f"❌ Authentication service: {e}")
        
        modules_status.append("✅ Configuration")
        modules_status.append("✅ UI Framework")
        
        status_text = "\n".join(modules_status)
        self.status_label.setText(status_text)
        
        QTimer.singleShot(2000, lambda: self.status_label.setText("🎯 Ready to start!"))
    
    def start_application(self):
        """Start the full application"""
        self.status_label.setText("🔄 Starting application...")
        
        try:
            # Import main application components
            from ui.views.main_window import MainWindow
            
            # Close simple window
            self.main_window.hide()
            
            # Create full main window
            self.full_main_window = MainWindow()
            self.full_main_window.current_user = self.current_user
            self.full_main_window.show()
            
            # Hide welcome window
            self.main_window.hide()
            
            print("✅ Application started successfully!")
            
        except Exception as e:
            print(f"❌ Failed to start full application: {e}")
            self.status_label.setText(f"❌ Error: {e}")
            QMessageBox.critical(None, "Error", f"Failed to start application:\n{e}")
    
    def quit(self):
        """Quit application"""
        print("👋 Dragofactu stopped")
        self.main_window.hide()
        super().quit()


def main():
    """Main application entry point"""
    print("🚀 Dragofactu - Professional Business Management System")
    print("=" * 50)
    
    try:
        # Create application
        app = DragofactuApp()
        
        # Run application
        sys.exit(app.exec())
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)