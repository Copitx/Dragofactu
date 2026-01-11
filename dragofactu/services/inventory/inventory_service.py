from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from dragofactu.models.audit import StockMovement
from dragofactu.models.database import SessionLocal
from dragofactu.services.business.entity_services import ProductService
from dragofactu.services.auth.auth_service import require_permission


class InventoryService:
    """Service for managing inventory and stock movements"""
    
    def __init__(self, db: Session):
        self.db = db
        self.product_service = ProductService(db)
    
    @require_permission('inventory.read')
    def get_stock_levels(self, category: str = None, low_stock_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get current stock levels for products
        
        Args:
            category: Filter by product category
            low_stock_only: Only show products below minimum stock
            
        Returns:
            List of stock level information
        """
        products = self.product_service.search_products(
            category=category, 
            low_stock_only=low_stock_only,
            active_only=True
        )
        
        stock_levels = []
        for product in products:
            stock_levels.append({
                'id': str(product.id),
                'code': product.code,
                'name': product.name,
                'category': product.category,
                'current_stock': product.current_stock,
                'minimum_stock': product.minimum_stock,
                'stock_unit': product.stock_unit,
                'is_low_stock': product.current_stock <= product.minimum_stock and product.minimum_stock > 0,
                'purchase_price': float(product.purchase_price) if product.purchase_price else 0,
                'sale_price': float(product.sale_price) if product.sale_price else 0,
                'supplier_id': str(product.supplier_id) if product.supplier_id else None,
                'supplier_name': product.supplier.name if product.supplier else None
            })
        
        return stock_levels
    
    @require_permission('inventory.read')
    def get_stock_movements(self, product_id: str = None, 
                           movement_type: str = None,
                           date_from: datetime = None,
                           date_to: datetime = None,
                           limit: int = 100) -> List[StockMovement]:
        """
        Get stock movements with optional filters
        
        Args:
            product_id: Filter by product ID
            movement_type: Filter by movement type ('in', 'out', 'adjustment')
            date_from: Start date filter
            date_to: End date filter
            limit: Maximum number of records
            
        Returns:
            List of StockMovement objects
        """
        query = self.db.query(StockMovement)
        
        if product_id:
            query = query.filter(StockMovement.product_id == product_id)
        
        if movement_type:
            query = query.filter(StockMovement.movement_type == movement_type)
        
        if date_from:
            query = query.filter(StockMovement.timestamp >= date_from)
        
        if date_to:
            query = query.filter(StockMovement.timestamp <= date_to)
        
        # Join with products to get product info
        query = query.join(StockMovement.product)
        
        return query.order_by(StockMovement.timestamp.desc()).limit(limit).all()
    
    @require_permission('inventory.adjust')
    def adjust_stock(self, product_id: str, new_quantity: int, 
                     reason: str = None, reference_type: str = None,
                     reference_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Adjust stock for a product
        
        Args:
            product_id: Product ID
            new_quantity: New stock quantity
            reason: Reason for adjustment
            reference_type: Type of reference (document, supplier_invoice, manual_adjustment)
            reference_id: Reference ID
            user_id: User performing the adjustment
            
        Returns:
            Result dictionary with success status
        """
        try:
            # Update product stock
            product = self.product_service.update_stock(
                product_id, new_quantity, reason, reference_type, reference_id, user_id
            )
            
            if not product:
                return {
                    'success': False,
                    'message': 'Product not found'
                }
            
            return {
                'success': True,
                'message': f'Stock updated to {new_quantity} units',
                'product': {
                    'id': str(product.id),
                    'name': product.name,
                    'current_stock': product.current_stock
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Stock adjustment failed: {str(e)}'
            }
    
    @require_permission('inventory.adjust')
    def add_stock(self, product_id: str, quantity: int, 
                  reason: str = None, reference_type: str = None,
                  reference_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Add stock to a product
        
        Args:
            product_id: Product ID
            quantity: Quantity to add
            reason: Reason for addition
            reference_type: Type of reference
            reference_id: Reference ID
            user_id: User performing the addition
            
        Returns:
            Result dictionary
        """
        product = self.db.query(StockMovement.product).filter(
            StockMovement.product_id == product_id
        ).first().product if self.db.query(StockMovement).filter(
            StockMovement.product_id == product_id
        ).first() else self.product_service.get_product_by_id(product_id)
        
        if not product:
            return {
                'success': False,
                'message': 'Product not found'
            }
        
        new_stock = product.current_stock + quantity
        
        return self.adjust_stock(
            product_id, new_stock, reason or f"Added {quantity} units",
            reference_type, reference_id, user_id
        )
    
    @require_permission('inventory.adjust')
    def remove_stock(self, product_id: str, quantity: int,
                    reason: str = None, reference_type: str = None,
                    reference_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Remove stock from a product
        
        Args:
            product_id: Product ID
            quantity: Quantity to remove
            reason: Reason for removal
            reference_type: Type of reference
            reference_id: Reference ID
            user_id: User performing the removal
            
        Returns:
            Result dictionary
        """
        product = self.db.query(StockMovement.product).filter(
            StockMovement.product_id == product_id
        ).first().product if self.db.query(StockMovement).filter(
            StockMovement.product_id == product_id
        ).first() else self.product_service.get_product_by_id(product_id)
        
        if not product:
            return {
                'success': False,
                'message': 'Product not found'
            }
        
        new_stock = product.current_stock - quantity
        
        if new_stock < 0:
            return {
                'success': False,
                'message': f'Cannot remove {quantity} units. Only {product.current_stock} units available.'
            }
        
        return self.adjust_stock(
            product_id, new_stock, reason or f"Removed {quantity} units",
            reference_type, reference_id, user_id
        )
    
    @require_permission('inventory.read')
    def get_low_stock_alerts(self) -> List[Dict[str, Any]]:
        """Get products that are below minimum stock levels"""
        return self.get_stock_levels(low_stock_only=True)
    
    @require_permission('inventory.read')
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get overall inventory summary statistics"""
        products = self.product_service.search_products(active_only=True)
        
        total_products = len(products)
        low_stock_count = 0
        total_stock_value = Decimal('0')
        
        for product in products:
            if product.current_stock <= product.minimum_stock and product.minimum_stock > 0:
                low_stock_count += 1
            
            if product.purchase_price:
                stock_value = product.current_stock * product.purchase_price
                total_stock_value += stock_value
        
        # Get recent stock movements
        recent_movements = self.get_stock_movements(limit=10)
        
        return {
            'total_products': total_products,
            'low_stock_products': low_stock_count,
            'total_stock_value': float(total_stock_value),
            'recent_movements': [
                {
                    'id': str(movement.id),
                    'product_name': movement.product.name if movement.product else 'Unknown',
                    'movement_type': movement.movement_type,
                    'quantity': movement.quantity,
                    'stock_before': movement.stock_before,
                    'stock_after': movement.stock_after,
                    'reason': movement.reason,
                    'timestamp': movement.timestamp.isoformat() if movement.timestamp else None,
                    'user_id': str(movement.user_id) if movement.user_id else None
                }
                for movement in recent_movements
            ]
        }
    
    @require_permission('inventory.read')
    def get_all_products(self, current_user) -> List[Product]:
        """Get all products for inventory view"""
        return self.product_service.search_products(current_user, active_only=True)
    
    @require_permission('inventory.create')
    def create_stock_movement(self, current_user, product_id: str, 
                           movement_type: str, quantity: int, reason: str):
        """Create a stock movement entry"""
        try:
            # Get current product
            product = self.product_service.get_product_by_id(product_id)
            if not product:
                raise ValueError("Product not found")
            
            # Create stock movement
            movement = StockMovement(
                id=uuid.uuid4(),
                product_id=product_id,
                movement_type=movement_type,
                quantity=quantity,
                reason=reason,
                stock_before=product.current_stock or 0,
                stock_after=(product.current_stock or 0) + (quantity if movement_type == 'in' else -quantity),
                user_id=current_user.id if current_user else None,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(movement)
            
            # Update product stock
            stock_change = quantity if movement_type == 'in' else -quantity
            new_stock = (product.current_stock or 0) + stock_change
            product.current_stock = new_stock
            
            self.db.commit()
            
            return {
                'success': True,
                'movement_id': str(movement.id),
                'new_stock': new_stock
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @require_permission('inventory.read')
    def search_products_by_stock(self, query: str, min_stock: int = None,
                                max_stock: int = None) -> List[Dict[str, Any]]:
        """
        Search products by stock levels
        
        Args:
            query: Search query for product name/code
            min_stock: Minimum stock filter
            max_stock: Maximum stock filter
            
        Returns:
            List of products matching criteria
        """
        products = self.product_service.search_products(query=query, active_only=True)
        
        filtered_products = []
        for product in products:
            if min_stock is not None and product.current_stock < min_stock:
                continue
            if max_stock is not None and product.current_stock > max_stock:
                continue
            
            filtered_products.append({
                'id': str(product.id),
                'code': product.code,
                'name': product.name,
                'category': product.category,
                'current_stock': product.current_stock,
                'minimum_stock': product.minimum_stock,
                'is_low_stock': product.current_stock <= product.minimum_stock and product.minimum_stock > 0
            })
        
        return filtered_products
    
    @require_permission('inventory.read')
    def get_product_stock_history(self, product_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get stock history for a specific product
        
        Args:
            product_id: Product ID
            days: Number of days of history to retrieve
            
        Returns:
            List of stock changes over time
        """
        date_from = datetime.utcnow() - timedelta(days=days)
        
        movements = self.get_stock_movements(
            product_id=product_id,
            date_from=date_from,
            limit=100
        )
        
        history = []
        for movement in movements:
            history.append({
                'date': movement.timestamp.isoformat() if movement.timestamp else None,
                'type': movement.movement_type,
                'quantity': movement.quantity,
                'stock_before': movement.stock_before,
                'stock_after': movement.stock_after,
                'reason': movement.reason
            })
        
        return history
    
    @require_permission('inventory.create')
    def create_stock_adjustment_batch(self, adjustments: List[Dict[str, Any]], 
                                     user_id: str) -> Dict[str, Any]:
        """
        Create multiple stock adjustments in a batch
        
        Args:
            adjustments: List of adjustment dictionaries
            user_id: User performing adjustments
            
        Returns:
            Result dictionary with success/failure summary
        """
        success_count = 0
        failed_adjustments = []
        
        for adjustment in adjustments:
            result = self.adjust_stock(
                product_id=adjustment.get('product_id'),
                new_quantity=adjustment.get('quantity'),
                reason=adjustment.get('reason'),
                reference_type='batch_adjustment',
                user_id=user_id
            )
            
            if result['success']:
                success_count += 1
            else:
                failed_adjustments.append({
                    'product_id': adjustment.get('product_id'),
                    'error': result['message']
                })
        
        return {
            'success': len(failed_adjustments) == 0,
            'success_count': success_count,
            'failed_count': len(failed_adjustments),
            'failed_adjustments': failed_adjustments
        }