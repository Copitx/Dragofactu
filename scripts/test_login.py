#!/usr/bin/env python3
"""
Script para probar login
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from dragofactu.services.auth.auth_service import AuthService
from dragofactu.models.database import SessionLocal
from dragofactu.ui.views.login_dialog import LoginDialog

def test_login():
    """Probar el diálogo de login"""
    app = QApplication(sys.argv)
    
    # Crear servicios
    auth_service = AuthService()
    
    # Crear y mostrar diálogo de login
    login_dialog = LoginDialog(auth_service)
    
    print("🔐 Prueba de Login")
    print("Credenciales:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nAbriendo diálogo de login...")
    
    result = login_dialog.exec()
    
    if result == LoginDialog.DialogCode.Accepted:
        user = login_dialog.get_user()
        print(f"✅ Login exitoso: {user.username} ({user.role})")
    else:
        print("❌ Login cancelado")
    
    return 0

if __name__ == "__main__":
    exit(test_login())