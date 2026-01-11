from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ...models.entities import Client, Supplier, Product
from ..auth.auth_service import require_permission
import json


class ClientService:
    def __init__(self, db: Session):
        self.db = db
    
    @require_permission('clients.create')
    def create_client(self, code: str, name: str, tax_id: str = None, 
                     address: str = None, city: str = None, postal_code: str = None,
                     province: str = None, country: str = None, phone: str = None,
                     email: str = None, website: str = None, notes: str = None) -> Client:
        
        # Check if code already exists
        existing = self.db.query(Client).filter(Client.code == code).first()
        if existing:
            raise ValueError(f"Client code {code} already exists")
        
        client = Client(
            code=code,
            name=name,
            tax_id=tax_id,
            address=address,
            city=city,
            postal_code=postal_code,
            province=province,
            country=country,
            phone=phone,
            email=email,
            website=website,
            notes=notes
        )
        
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        
        return client
    
    @require_permission('clients.read')
    def get_client_by_id(self, client_id: str) -> Optional[Client]:
        return self.db.query(Client).filter(Client.id == client_id).first()
    
    @require_permission('clients.read')
    def get_client_by_code(self, code: str) -> Optional[Client]:
        return self.db.query(Client).filter(Client.code == code).first()
    
    @require_permission('clients.read')
    def search_clients(self, query: str = None, active_only: bool = True) -> List[Client]:
        db_query = self.db.query(Client)
        
        if active_only:
            db_query = db_query.filter(Client.is_active == True)
        
        if query:
            db_query = db_query.filter(
                or_(
                    Client.code.ilike(f"%{query}%"),
                    Client.name.ilike(f"%{query}%"),
                    Client.tax_id.ilike(f"%{query}%"),
                    Client.email.ilike(f"%{query}%")
                )
            )
        
        return db_query.order_by(Client.name).all()
    
    @require_permission('clients.update')
    def update_client(self, client_id: str, **kwargs) -> Optional[Client]:
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return None
        
        # Update allowed fields
        allowed_fields = ['name', 'tax_id', 'address', 'city', 'postal_code', 
                         'province', 'country', 'phone', 'email', 'website', 
                         'notes', 'is_active']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(client, field, value)
        
        self.db.commit()
        self.db.refresh(client)
        
        return client
    
    @require_permission('clients.delete')
    def delete_client(self, client_id: str) -> bool:
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return False
        
        # Soft delete
        client.is_active = False
        self.db.commit()
        
        return True


class SupplierService:
    def __init__(self, db: Session):
        self.db = db
    
    @require_permission('suppliers.create')
    def create_supplier(self, code: str, name: str, tax_id: str = None,
                       address: str = None, city: str = None, postal_code: str = None,
                       province: str = None, country: str = None, phone: str = None,
                       email: str = None, website: str = None, notes: str = None) -> Supplier:
        
        # Check if code already exists
        existing = self.db.query(Supplier).filter(Supplier.code == code).first()
        if existing:
            raise ValueError(f"Supplier code {code} already exists")
        
        supplier = Supplier(
            code=code,
            name=name,
            tax_id=tax_id,
            address=address,
            city=city,
            postal_code=postal_code,
            province=province,
            country=country,
            phone=phone,
            email=email,
            website=website,
            notes=notes
        )
        
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        
        return supplier
    
    @require_permission('suppliers.read')
    def get_supplier_by_id(self, supplier_id: str) -> Optional[Supplier]:
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    @require_permission('suppliers.read')
    def get_supplier_by_code(self, code: str) -> Optional[Supplier]:
        return self.db.query(Supplier).filter(Supplier.code == code).first()
    
    @require_permission('suppliers.read')
    def search_suppliers(self, query: str = None, active_only: bool = True) -> List[Supplier]:
        db_query = self.db.query(Supplier)
        
        if active_only:
            db_query = db_query.filter(Supplier.is_active == True)
        
        if query:
            db_query = db_query.filter(
                or_(
                    Supplier.code.ilike(f"%{query}%"),
                    Supplier.name.ilike(f"%{query}%"),
                    Supplier.tax_id.ilike(f"%{query}%"),
                    Supplier.email.ilike(f"%{query}%")
                )
            )
        
        return db_query.order_by(Supplier.name).all()
    
    @require_permission('suppliers.update')
    def update_supplier(self, supplier_id: str, **kwargs) -> Optional[Supplier]:
        supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            return None
        
        # Update allowed fields
        allowed_fields = ['name', 'tax_id', 'address', 'city', 'postal_code',
                         'province', 'country', 'phone', 'email', 'website',
                         'notes', 'is_active']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(supplier, field, value)
        
        self.db.commit()
        self.db.refresh(supplier)
        
        return supplier
    
    @require_permission('suppliers.delete')
    def delete_supplier(self, supplier_id: str) -> bool:
        supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            return False
        
        # Soft delete
        supplier.is_active = False
        self.db.commit()
        
        return True


class ProductService:
    def __init__(self, db: Session):
        self.db = db
    
    @require_permission('products.create')
    def create_product(self, code: str, name: str, description: str = None,
                      category: str = None, purchase_price: float = None,
                      sale_price: float = None, current_stock: int = 0,
                      minimum_stock: int = 0, stock_unit: str = "units",
                      supplier_id: str = None) -> Product:
        
        # Check if code already exists
        existing = self.db.query(Product).filter(Product.code == code).first()
        if existing:
            raise ValueError(f"Product code {code} already exists")
        
        product = Product(
            code=code,
            name=name,
            description=description,
            category=category,
            purchase_price=purchase_price,
            sale_price=sale_price,
            current_stock=current_stock,
            minimum_stock=minimum_stock,
            stock_unit=stock_unit,
            supplier_id=supplier_id
        )
        
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    @require_permission('products.read')
    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    @require_permission('products.read')
    def get_product_by_code(self, code: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.code == code).first()
    
    @require_permission('products.read')
    def search_products(self, query: str = None, category: str = None,
                       low_stock_only: bool = False, active_only: bool = True) -> List[Product]:
        db_query = self.db.query(Product)
        
        if active_only:
            db_query = db_query.filter(Product.is_active == True)
        
        if query:
            db_query = db_query.filter(
                or_(
                    Product.code.ilike(f"%{query}%"),
                    Product.name.ilike(f"%{query}%"),
                    Product.description.ilike(f"%{query}%"),
                    Product.category.ilike(f"%{query}%")
                )
            )
        
        if category:
            db_query = db_query.filter(Product.category == category)
        
        if low_stock_only:
            db_query = db_query.filter(
                and_(
                    Product.current_stock <= Product.minimum_stock,
                    Product.minimum_stock > 0
                )
            )
        
        return db_query.order_by(Product.name).all()
    
    @require_permission('products.read')
    def get_low_stock_products(self) -> List[Product]:
        return self.db.query(Product).filter(
            and_(
                Product.current_stock <= Product.minimum_stock,
                Product.minimum_stock > 0,
                Product.is_active == True
            )
        ).order_by(Product.name).all()
    
    @require_permission('products.update')
    def update_product(self, product_id: str, **kwargs) -> Optional[Product]:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None
        
        # Update allowed fields
        allowed_fields = ['name', 'description', 'category', 'purchase_price',
                         'sale_price', 'minimum_stock', 'stock_unit', 
                         'supplier_id', 'is_active']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(product, field, value)
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    @require_permission('products.update')
    def update_stock(self, product_id: str, new_stock: int, reason: str = None,
                    reference_type: str = None, reference_id: str = None,
                    user_id: str = None) -> Product:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError("Product not found")
        
        old_stock = product.current_stock
        
        # Create stock movement record
        from ...models.audit import StockMovement
        movement_type = "in" if new_stock > old_stock else "out"
        quantity = abs(new_stock - old_stock)
        
        stock_movement = StockMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
            reference_type=reference_type,
            reference_id=reference_id,
            stock_before=old_stock,
            stock_after=new_stock,
            user_id=user_id,
            notes=f"Stock adjusted from {old_stock} to {new_stock}"
        )
        
        # Update product stock
        product.current_stock = new_stock
        
        self.db.add(stock_movement)
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    @require_permission('products.delete')
    def delete_product(self, product_id: str) -> bool:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False
        
        # Soft delete
        product.is_active = False
        self.db.commit()
        
        return True