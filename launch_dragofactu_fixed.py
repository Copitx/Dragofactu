#!/usr/bin/env python3
"""
🐲 DRAGOFACTU - Fixed Application Launcher with GUI Support
Solves display issues in remote/NX environments
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def setup_display_environment():
    """Setup display environment for remote/NX systems"""
    print("🖥️  Configurando entorno de visualización...")
    
    # Only apply X11/xcb settings if not on macOS
    if sys.platform != 'darwin':
        # Fix for NX/remote environments
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        os.environ['QT_SCALE_FACTOR'] = '1'
        os.environ['QT_X11_NO_MITSHM'] = '1'  # Fix for remote displays
        os.environ['QT_QPA_PLATFORM'] = 'xcb'  # Force X11 platform
        
        # Ensure DISPLAY is set
        if not os.environ.get('DISPLAY'):
            os.environ['DISPLAY'] = ':0'
        
        print(f"   DISPLAY: {os.environ.get('DISPLAY')}")
        print("   ✅ Entorno configurado para display remoto (X11)")
    else:
        print("   🍎 Detected macOS environment")
        print("   Using native display settings (Cocoa)")

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

def launch_application_with_display():
    """Launch the application with proper display setup"""
    app_entry = None
    entry_points = [
        "dragofactu_complete.py",
        "dragofactu/main.py", 
        "main.py",
    ]
    
    for entry in entry_points:
        if Path(entry).exists():
            app_entry = entry
            print(f"✅ Using entry point: {entry}")
            break
    
    if not app_entry:
        print("❌ No application entry point found")
        return False
    
    print("\n🚀 Launching DRAGOFACTU with Display Support...")
    print("=" * 60)
    
    try:
        # Launch with explicit display connection
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'  # Ensure immediate output
        
        process = subprocess.Popen(
            ["./venv/bin/python", app_entry],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("📱 Starting GUI application...")
        print("   If window doesn't appear, check:")
        print("   1. X11 forwarding is enabled")
        print("   2. DISPLAY=:0 is accessible")
        print("   3. No firewall blocking X11")
        print("")
        
        # Monitor output for a few seconds
        import time
        start_time = time.time()
        timeout = 10
        
        while time.time() - start_time < timeout:
            if process.poll() is not None:
                # Process finished
                try:
                    output, _ = process.communicate(timeout=1)
                    if output:
                        print(f"Application output: {output}")
                except:
                    pass
                return process.returncode == 0
            
            time.sleep(0.1)
        
        # If still running after timeout, assume GUI launched successfully
        if process.poll() is None:
            print("✅ GUI application launched successfully!")
            print("   Window should be visible on your display")
            print("   Process running in background")
            return True
        else:
            print("❌ Application failed to start")
            return False
            
    except Exception as e:
        print(f"❌ Failed to launch application: {e}")
        return False

def main():
    """Main launcher function"""
    print("🐲 DRAGOFACTU - Business Management System Launcher")
    print("=" * 60)
    
    # Setup display environment first
    setup_display_environment()
    
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
    
    if not launch_application_with_display():
        sys.exit(1)

if __name__ == "__main__":
    main()