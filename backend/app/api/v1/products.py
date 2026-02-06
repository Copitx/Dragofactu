"""
Products CRUD endpoints with stock management.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user, require_permission
from app.models import Product, Supplier, User
from app.schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductList,
    StockAdjustment, MessageResponse
)

router = APIRouter(prefix="/products", tags=["Productos"])


@router.get("", response_model=ProductList)
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None, description="Buscar por nombre o codigo"),
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    low_stock: bool = Query(False, description="Solo productos con stock bajo"),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products.read"))
):
    """Listar productos de la empresa."""
    query = db.query(Product).filter(Product.company_id == current_user.company_id)

    if active_only:
        query = query.filter(Product.is_active == True)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_term)) |
            (Product.code.ilike(search_term))
        )

    if category:
        query = query.filter(Product.category == category)

    if low_stock:
        query = query.filter(Product.current_stock < Product.minimum_stock)

    total = query.count()
    products = query.order_by(Product.name).offset(skip).limit(limit).all()

    return ProductList(
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products.create"))
):
    """Crear nuevo producto."""
    # Check code uniqueness
    existing = db.query(Product).filter(
        Product.company_id == current_user.company_id,
        Product.code == data.code
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un producto con el codigo {data.code}"
        )

    # Validate supplier if provided
    if data.supplier_id:
        supplier = db.query(Supplier).filter(
            Supplier.id == data.supplier_id,
            Supplier.company_id == current_user.company_id
        ).first()
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Proveedor no encontrado"
            )

    product = Product(
        company_id=current_user.company_id,
        **data.model_dump()
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return ProductResponse.model_validate(product)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products.read"))
):
    """Obtener producto por ID."""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.company_id == current_user.company_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    return ProductResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products.update"))
):
    """Actualizar producto."""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.company_id == current_user.company_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    # Check code uniqueness if changing
    if data.code and data.code != product.code:
        existing = db.query(Product).filter(
            Product.company_id == current_user.company_id,
            Product.code == data.code,
            Product.id != product_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un producto con el codigo {data.code}"
            )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products.delete"))
):
    """Eliminar producto (soft delete)."""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.company_id == current_user.company_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    product.is_active = False
    db.commit()

    return MessageResponse(message=f"Producto {product.code} eliminado")


@router.post("/{product_id}/adjust-stock", response_model=ProductResponse)
async def adjust_stock(
    product_id: UUID,
    adjustment: StockAdjustment,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.update"))
):
    """Ajustar stock de un producto."""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.company_id == current_user.company_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    new_stock = product.current_stock + adjustment.quantity
    if new_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Stock actual: {product.current_stock}"
        )

    product.current_stock = new_stock
    db.commit()
    db.refresh(product)

    return ProductResponse.model_validate(product)


@router.get("/categories/list", response_model=list)
async def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products.read"))
):
    """Listar categorias de productos."""
    categories = db.query(Product.category).filter(
        Product.company_id == current_user.company_id,
        Product.category.isnot(None),
        Product.is_active == True
    ).distinct().all()

    return [c[0] for c in categories if c[0]]
