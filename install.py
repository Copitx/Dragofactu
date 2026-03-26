#!/usr/bin/env python3
"""
Dragofactu - Professional Business Management System Installation Script
"""

import os
import sys
import secrets

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    print("🚀 Dragofactu Installation")
    print("=" * 50)
    
    try:
        # Step 1: Create directories
        print("📁 Creating directories...")
        directories = ["data", "exports", "attachments", "assets"]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Directory: {directory}")
        
        # Step 2: Install dependencies
        print("\n📦 Installing dependencies...")
        result = os.system("pip3 install -e . --user")
        
        if result == 0:
            print("✅ Dependencies installed successfully")
        else:
            print("⚠️  Dependencies installation had issues")
            print("You may need to run: pip3 install -e .")
        
        # Step 3: Setup database
        print("\n🗄️ Setting up database...")
        
        # Try to import and setup
        try:
            from config.config import AppConfig
            print(f"Database URL: {AppConfig.get_database_url()}")
            print("✅ Configuration loaded successfully")
            
            # Create tables
            from models.base import Base
            from models.database import engine
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created")
            
            # Create default user
            from models.database import SessionLocal
            from models.entities import UserRole
            from services.auth.auth_service import UserService
            
            with SessionLocal() as db:
                user_service = UserService(db)
                
                admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
                admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
                generated_password = False
                if not admin_password:
                    admin_password = secrets.token_urlsafe(12)
                    generated_password = True

                admin_user = user_service.get_user_by_username(admin_username)
                if not admin_user:
                    user_service.create_user(
                        username=admin_username,
                        email=f"{admin_username}@dragofactu.com",
                        password=admin_password,
                        full_name="System Administrator",
                        role=UserRole.ADMIN
                    )
                    print(f"✅ Created admin user: {admin_username}")
                    print(f"🔐 Temporary password: {admin_password}")
                    if generated_password:
                        print("⚠️  This password was generated automatically. Store it and rotate it after first login.")
                else:
                    print("✅ Admin user already exists")
            
        except ImportError as e:
            print(f"❌ Could not setup database: {e}")
            print("Please ensure .env file is properly configured")
        
        # Step 4: Create sample data
        print("\n📝 Creating sample data...")
        try:
            from models.database import SessionLocal
            from services.business.entity_services import ClientService, SupplierService, ProductService
            
            with SessionLocal() as db:
                client_service = ClientService(db)
                supplier_service = SupplierService(db)
                product_service = ProductService(db)
                
                # Sample client
                try:
                    client_service.create_client(
                        code="C001",
                        name="Sample Client",
                        tax_id="12345678A",
                        address="Sample Address 123",
                        city="Sample City",
                        postal_code="12345",
                        phone="+34 900 123 456",
                        email="client@sample.com"
                    )
                    print("✅ Sample client created")
                except:
                    print("⚠️  Sample client already exists")
                
                # Sample products
                sample_products = [
                    {
                        "code": "P001",
                        "name": "Sample Product 1",
                        "category": "Electronics",
                        "purchase_price": 50.00,
                        "sale_price": 75.00,
                        "current_stock": 100,
                        "minimum_stock": 10
                    },
                    {
                        "code": "P002",
                        "name": "Sample Product 2",
                        "category": "Office Supplies",
                        "purchase_price": 10.00,
                        "sale_price": 15.00,
                        "current_stock": 500,
                        "minimum_stock": 50
                    }
                ]
                
                for product_data in sample_products:
                    try:
                        product_service.create_product(**product_data)
                        print(f"✅ Sample product created: {product_data['name']}")
                    except:
                        print(f"⚠️  Sample product already exists: {product_data['name']}")
        
        except Exception as e:
            print(f"⚠️  Could not create sample data: {e}")
        
        print("\n✅ Installation completed successfully!")
        print("\n🎯 Next Steps:")
        print("1. Update .env file with your database and email configuration")
        print("2. Run: python3 main.py")
        print("3. Login with the admin credentials shown during installation")
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")


if __name__ == "__main__":
    main()