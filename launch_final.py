#!/usr/bin/env python3
"""
DRAGOFACTU - Super Simple Launcher
"""

import sys
import os

def main():
    print("🐲 DRAGOFACTU - Sistema de Gestión Empresarial")
    print("==================================================")
    
    # Check virtual environment
    if not os.path.exists("venv"):
        print("❌ No se encuentra el entorno virtual")
        print("Ejecute: python3 -m venv venv")
        return
    
    print("🚀 Iniciando aplicación...")
    
    # Create database and user if needed
    try:
        from dragofactu.models.database import engine, Base
        from dragofactu.services.auth.auth_service import AuthService
        from dragofactu.models.database import SessionLocal
        from dragofactu.models.entities import User
        
        Base.metadata.create_all(bind=engine)
        
        # Check and create admin user
        with SessionLocal() as db:
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                auth_service = AuthService()
                admin = User(
                    username="admin",
                    email="admin@dragofactu.com",
                    password_hash=auth_service.hash_password("admin123"),
                    full_name="Administrador del Sistema",
                    role="ADMIN",
                    is_active=True
                )
                db.add(admin)
                db.commit()
                print("✅ Usuario admin creado")
        
        print("✅ Base de datos lista")
        
        # Launch app
        try:
            exec(open("simple_dragofactu_app_fixed.py").read())
        except Exception as e:
            print(f"❌ Error al iniciar: {e}")
    
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    main()