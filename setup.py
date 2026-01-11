#!/usr/bin/env python3
"""
Simple setup script for Dragofactu
"""

import os
import sys
import subprocess

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    version_parts = version.split('.')
    major = int(version_parts[0])
    
    print(f"🐍 Python version: {version}")
    
    if major < 3:
        print("❌ Dragofactu requires Python 3.11+")
        print("Please install Python 3.11 or higher")
        return False
    
    return True

def create_env_file():
    """Create or update .env file"""
    env_content = '''# Database Configuration
DATABASE_URL=postgresql://localhost:5432/dragofactu
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dragofactu
DB_USER=dragofactu
DB_PASSWORD=your_password_here

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Application Configuration
APP_NAME=Dragofactu
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key-here
JWT_EXPIRATION_HOURS=24

# PDF Configuration
PDF_COMPANY_NAME=Your Company Name
PDF_COMPANY_ADDRESS=Your Address
PDF_COMPANY_PHONE=Your Phone
PDF_COMPANY_EMAIL=your-email@company.com
PDF_COMPANY_CIF=Your CIF
PDF_LOGO_PATH=assets/logo.png

# File Paths
DATA_DIR=./data
EXPORTS_DIR=./exports
ATTACHMENTS_DIR=./attachments
'''
    
    env_file = "/home/copi/Dragofactu/.env"
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✓ Created .env file at {env_file}")
    return env_file

def main():
    """Main setup function"""
    print("🚀 Dragofactu Setup Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Create .env file
    env_file = create_env_file()
    
    # Install dependencies
    print("📦 Installing dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "PySide6>=6.5.0",
            "sqlalchemy>=2.0.0",
            "psycopg2-binary>=2.9.0",
            "alembic>=1.12.0",
            "reportlab>=4.0.0",
            "pillow>=10.0.0",
            "bcrypt>=4.0.0",
            "python-dotenv>=1.0.0",
            "python-dateutil>=2.8.0",
            "jinja2>=3.1.0"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
        else:
            print("⚠️  Dependencies had issues:")
            print(result.stderr)
            print("Please run: pip install -e . --user")
    except Exception as e:
        print(f"❌ Installation failed: {e}")
    
    print(f"\n✅ Setup completed successfully!")
    print()
    print("🎯 Next steps:")
    print(f"1. Configure your database in {env_file}")
    print("2. Run: python3 main.py")
    print("3. Login with admin/admin123 (change after first login)")
    print()
    print("📖 For full documentation, see README.md")


if __name__ == "__main__":
    main()