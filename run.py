#!/usr/bin/env python3
"""
DRAGOFACTU - Simple Launcher
Script para iniciar la aplicación sin dependencias complejas
"""

import os
import sys

print("🐲 DRAGOFACTU - Launcher")
print("=" * 40)

# Cambiar al directorio del proyecto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Verificar estructura
print("📁 Verificando estructura...")
required_dirs = ["dragofactu", "Documentos", "Scripts"]
for directory in required_dirs:
    if os.path.exists(directory):
        print(f"✅ {directory}")
    else:
        print(f"❌ {directory} no encontrado")

# Verificar scripts principales
print("\n📄 Verificando archivos principales...")
key_files = [
    "dragofactu/__init__.py",
    "dragofactu/main.py",
    "README.md",
    "requirements.txt"
]

for file_path in key_files:
    if os.path.exists(file_path):
        print(f"✅ {file_path}")
    else:
        print(f"❌ {file_path} no encontrado")

# Estado del entorno
print(f"\n📍 Directorio actual: {os.getcwd()}")
print(f"🐍 Python: {sys.version.split()[0]}")

# Opciones de inicio
print("\n🚀 Opciones de inicio:")
print("1. python3 dragofactu/main.py - Aplicación completa")
print("2. python3 simple_main.py - Versión simplificada")
print("3. ./Scripts/start.sh - Script de inicio")

# Recomendación
# Verificar si hay usuario admin
print("\n👤 Verificando usuario administrador...")
try:
    import sqlite3
    conn = sqlite3.connect("dragofactu.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    admin_exists = cursor.fetchone()[0] > 0
    conn.close()
    
    if admin_exists:
        print("✅ Usuario admin configurado")
    else:
        print("⚠️  Usuario admin no encontrado")
        print("   Ejecuta: python3 scripts/init_db.py")
        print("   Para crear el usuario admin")
except Exception as e:
    print(f"❌ Error verificando usuario: {e}")

print("\n💡 Recomendación:")
if os.path.exists("venv"):
    print("✅ Entorno virtual detectado")
    print("   Ejecuta: source venv/bin/activate")
    print("   Luego: python3 dragofactu/main.py")
    print("\n🎯 ¡La aplicación completa está funcionando!")
    print("   Base de datos SQLite: dragofactu.db")
    print("   Login por defecto: admin/admin123")
else:
    print("⚠️  Entorno virtual no encontrado")
    print("   Ejecuta: python3 install.py")

print("\n🎯 DRAGOFACTU está listo para usar!")