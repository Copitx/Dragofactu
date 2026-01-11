#!/usr/bin/env python3
"""
Script para inicializar datos básicos en la base de datos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragofactu.models.database import SessionLocal, engine, Base
from dragofactu.models.entities import User, UserRole
from dragofactu.services.auth.auth_service import AuthService
import uuid

def create_default_admin():
    """Crear usuario admin por defecto"""
    db = SessionLocal()
    
    try:
        # Verificar si ya existe el usuario admin
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("✅ El usuario admin ya existe")
            return admin_user
        
        # Crear usuario admin
        auth_service = AuthService()
        password_hash = auth_service.hash_password("admin123")
        
        admin_user = User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@dragofactu.com",
            password_hash=password_hash,
            full_name="Administrador del Sistema",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Usuario admin creado exitosamente")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   ID: {admin_user.id}")
        
        return admin_user
        
    except Exception as e:
        print(f"❌ Error creando usuario admin: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def main():
    """Función principal"""
    print("🔧 DRAGOFACTU - Inicialización de Base de Datos")
    print("=" * 50)
    
    # Crear tablas
    print("📊 Creando tablas de la base de datos...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas correctamente")
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return
    
    # Crear usuario admin
    print("\n👤 Creando usuario administrador...")
    admin_user = create_default_admin()
    
    if admin_user:
        print("\n🎉 ¡Inicialización completada con éxito!")
        print("\n🚀 Ahora puedes iniciar la aplicación:")
        print("   source venv/bin/activate")
        print("   python3 dragofactu/main.py")
        print("\n🔐 Login credentials:")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("\n❌ No se pudo completar la inicialización")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())