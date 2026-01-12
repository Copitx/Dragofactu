#!/usr/bin/env python3
"""
🐲 DRAGOFACTU - Unified Application Launcher
Official single entry point for the Dragofactu Business Management System
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print("✅ Python version compatible")

def setup_virtual_environment():
    """Create virtual environment if not exists"""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("🔧 Creating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("✅ Virtual environment created")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
    
    # Install/upgrade dependencies
    print("📦 Installing/updating dependencies...")
    requirements = [
        "PySide6>=6.5.0",
        "SQLAlchemy>=2.0.0", 
        "psycopg2-binary>=2.8.0",
        "alembic>=1.12.0",
        "reportlab>=4.0.0",
        "pillow>=9.0.0",
        "bcrypt>=3.2.0",
        "python-dotenv>=1.0.0",
        "python-dateutil>=2.8.0",
        "jinja2>=3.0.0",
        "PyJWT>=2.0.0"
    ]
    
    try:
        subprocess.run(["./venv/bin/pip", "install", "--upgrade"] + requirements, check=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def initialize_database():
    """Initialize database if needed"""
    db_path = Path("dragofactu.db")
    
    # Check if database exists and has admin user
    if db_path.exists():
        try:
            conn = sqlite3.connect('dragofactu.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', 
                          (os.getenv('DEFAULT_ADMIN_USERNAME', 'admin'),))
            admin_exists = cursor.fetchone()[0] > 0
            conn.close()
            
            if admin_exists:
                print("✅ Database initialized with admin user")
                return True
        except (sqlite3.Error, Exception):
            pass
    
    print("🔧 Initializing database...")
    try:
        subprocess.run(["./venv/bin/python", "scripts/init_db.py"], check=True)
        print("✅ Database initialized")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

def get_application_entry():
    """Determine the best application entry point"""
    entry_points = [
        "dragofactu_complete.py",  # Main complete application
        "dragofactu/main.py",      # Module-based entry
        "main.py",                 # Simple entry point
    ]
    
    for entry in entry_points:
        if Path(entry).exists():
            print(f"✅ Using entry point: {entry}")
            return entry
    
    print("❌ No application entry point found")
    return None

def launch_application():
    """Launch the Dragofactu application"""
    app_entry = get_application_entry()
    if not app_entry:
        return False
    
    print("\n🚀 Launching DRAGOFACTU...")
    print("=" * 50)
    
    try:
        subprocess.run(["./venv/bin/python", app_entry], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch application: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return True

def main():
    """Main launcher function"""
    print("🐲 DRAGOFACTU - Business Management System Launcher")
    print("=" * 60)
    
    # Environment setup
    check_python_version()
    
    if not setup_virtual_environment():
        sys.exit(1)
    
    if not initialize_database():
        sys.exit(1)
    
    # Security warnings
    if not os.getenv('SECRET_KEY') or os.getenv('SECRET_KEY') == 'your-secret-key-here':
        print("\n⚠️ SECURITY WARNING: Using default SECRET_KEY")
        print("   Set SECRET_KEY environment variable for production security")
    
    if not os.getenv('DEFAULT_ADMIN_PASSWORD'):
        print("\n⚠️ SECURITY WARNING: Using default admin password")
        print("   Set DEFAULT_ADMIN_PASSWORD environment variable for security")
    
    # Show credentials
    print(f"\n🔐 Login Credentials:")
    print(f"   Username: {os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')}")
    print(f"   Password: {'[Set via DEFAULT_ADMIN_PASSWORD]' if os.getenv('DEFAULT_ADMIN_PASSWORD') else 'change-this-password-2024'}")
    
    if not launch_application():
        sys.exit(1)

if __name__ == "__main__":
    main()