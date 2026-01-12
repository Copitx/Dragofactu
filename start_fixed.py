#!/usr/bin/env python3
"""
DRAGOFACTU - Fixed Application Launcher
"""

import os
import sys
import subprocess

def main():
    print("🐲 DRAGOFACTU - Sistema de Gestión Empresarial")
    print("==================================================")
    
    # Check if virtual environment exists
    if not os.path.exists("venv"):
        print("❌ Entorno virtual no encontrado")
        print("🔧 Creando entorno virtual...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
        
        print("📦 Instalando dependencias...")
        subprocess.run(["./venv/bin/pip", "install", "PySide6", "SQLAlchemy", "psycopg2-binary", 
                         "alembic", "reportlab", "pillow", "bcrypt", 
                         "python-dotenv", "python-dateutil", "jinja2", "PyJWT"])
    
    # Check if admin user exists
    try:
        result = subprocess.run([
            "./venv/bin/python", "-c", 
            "import sqlite3; "
            "conn = sqlite3.connect('dragofactu.db'); "
            "cursor = conn.cursor(); "
            "cursor.execute('SELECT COUNT(*) FROM users WHERE username = \"admin\"'); "
            "admin_exists = cursor.fetchone()[0] > 0; "
            "conn.close(); "
            "print('✅' if admin_exists else '❌', end=''); "
            "exit(0 if admin_exists else 1)"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(" Usuario admin no encontrado")
            print("🔧 Creando usuario administrador...")
            subprocess.run(["./venv/bin/python", "scripts/init_db.py"])
    except Exception as e:
        print(f"⚠️ Error checking admin user: {e}")
        print("🔧 Creando usuario administrador...")
        subprocess.run(["./venv/bin/python", "scripts/init_db.py"])
    
    print("")
    print("🚀 INICIANDO APLICACIÓN...")
    print("🔐 Credenciales:")
    print("   Usuario: admin")
    print("   Contraseña: admin123")
    print("")
    
    # Launch application
    subprocess.run(["./venv/bin/python", "simple_dragofactu_app_fixed.py"])

if __name__ == "__main__":
    main()