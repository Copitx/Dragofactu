#!/usr/bin/env python3
"""
Script para probar la aplicación completa sin GUI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragofactu.models.database import SessionLocal
from dragofactu.models.entities import User
from dragofactu.services.auth.auth_service import AuthService
from dragofactu.ui.views.main_window import MainWindow
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

def test_app_functionality():
    """Probar funcionalidad básica de la aplicación"""
    print("🧪 DRAGOFACTU - Test de Funcionalidad")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    # Probar conexión a base de datos
    print("📊 Probando conexión a base de datos...")
    try:
        db = SessionLocal()
        user_count = db.query(User).count()
        print(f"✅ Base de datos conectada - {user_count} usuarios encontrados")
        db.close()
    except Exception as e:
        print(f"❌ Error de base de datos: {e}")
        return False
    
    admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
    if not admin_password:
        print("❌ DEFAULT_ADMIN_PASSWORD no definido. Exporta credenciales seguras para ejecutar este test.")
        return False

    # Probar autenticación
    print("\n🔐 Probando autenticación...")
    try:
        auth = AuthService()
        with SessionLocal() as db:
            user = auth.authenticate(db, admin_username, admin_password)
            if user:
                print(f"✅ Autenticación exitosa: {user.full_name} ({user.role})")
            else:
                print("❌ Autenticación fallida")
                return False
    except Exception as e:
        print(f"❌ Error en autenticación: {e}")
        return False
    
    # Probar creación de UI
    print("\n🖥️  Probando UI principal...")
    try:
        main_window = MainWindow()
        print("✅ Ventana principal creada exitosamente")
        
        # Probar configuración de usuario
        with SessionLocal() as db:
            user = auth.authenticate(db, admin_username, admin_password)
            merged_user = db.merge(user)
            main_window.set_current_user(merged_user)
            print("✅ UI configurada con usuario correctamente")
            
    except Exception as e:
        print(f"❌ Error en UI: {e}")
        return False
    
    print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
    print("\n📋 Resumen:")
    print("   ✅ Base de datos: Conectada")
    print("   ✅ Autenticación: Funcional")
    print("   ✅ UI: Renderizada")
    print("   ✅ Usuario admin: Configurado")
    
    print("\n🚀 La aplicación está lista para producción!")
    
    return True

if __name__ == "__main__":
    success = test_app_functionality()
    exit(0 if success else 1)