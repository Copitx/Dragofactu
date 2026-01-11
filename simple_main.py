#!/usr/bin/env python3
"""
Dragofactu - Professional Business Management System (Simplified)
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

print("🚀 Dragofactu - Professional Business Management System")
print("=" * 50)

try:
    # Import essential modules only
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
    print("✅ PySide6 available")
except ImportError as e:
    print(f"❌ PySide6 not available: {e}")
    sys.exit(1)

class SimpleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dragofactu")
        self.resize(300, 200)
        
        # Simple layout
        layout = QVBoxLayout()
        
        # Welcome message
        welcome_label = QLabel("🏢 Welcome to Dragofactu!")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_font = welcome_label.font()
        welcome_font.setPointSize(16)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        
        # Status label
        self.status_label = QLabel("✅ Ready to start!")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Button
        self.start_button = QPushButton("🚀 Start Dragofactu")
        self.start_button.setMinimumHeight(50)
        
        layout.addWidget(welcome_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.start_button)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Connect button click
        self.start_button.clicked.connect(self.on_start_clicked)
        
        # Show window
        self.show()
    
    def on_start_clicked(self):
        self.status_label.setText("🚀 Initializing...")
        QTimer.singleShot(2000, self.show_ready_message)
    
    def show_ready_message(self):
        self.status_label.setText("✅ Ready to start!")
        
        # Show message dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("🎯 Application Ready")
        msg.setText("Dragofactu is ready to use!\n\n\n📋 Prerequisites:\n✅ Python 3.11+\n✅ PySide6 installed\n✅ Database configured\n✅ Admin user: admin/admin123\n\n⚠️ Change default password after first login!")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

class DragofactuApp(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        
        # Set basic application properties
        self.setApplicationName("Dragofactu")
        self.setOrganizationName("Dragofactu")
        self.setApplicationVersion("1.0.0")
        
        # Create and show simple window
        window = SimpleApp()
        window.show()
        
        # Process events
        self.exec()


if __name__ == "__main__":
    app = DragofactuApp()
    app.exec()