"""
Supplier catalog endpoints.
Manages the catalog of products per supplier with purchase prices.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from uuid import UUID

from app.api.deps import get_db, get_current_user, require_permission
from app.models import User, Supplier, Product
from app.models.supplier_catalog import SupplierProduct
from app.schemas.supplier_catalog import (
    SupplierProductCreate, SupplierProductUpdate,
    SupplierProductResponse, CatalogSearchResult
)

router = APIRouter(tags=["Catálogo"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _to_response(entry: SupplierProduct) -> SupplierProductResponse:
    product = entry.product
    return SupplierProductResponse(
        id=entry.id,
        company_id=entry.company_id,
        supplier_id=entry.supplier_id,
        product_id=entry.product_id,
        supplier_ref=entry.supplier_ref,
        purchase_price=entry.purchase_price or 0.0,
        lead_time_days=entry.lead_time_days or 0,
        min_order_qty=entry.min_order_qty or 1.0,
        notes=entry.notes,
        is_active=entry.is_active,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        product_code=product.code if product else None,
        product_name=product.name if product else None,
        product_sale_price=product.sale_price if product else None,
        product_category=product.category if product else None,
    )


# ---------------------------------------------------------------------------
# Supplier-scoped endpoints
# ---------------------------------------------------------------------------

@router.get("/suppliers/{supplier_id}/catalog", response_model=List[SupplierProductResponse])
async def list_supplier_catalog(
    supplier_id: UUID,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers.read"))
):
    """List the product catalog for a specific supplier."""
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.company_id == current_user.company_id
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    query = db.query(SupplierProduct).options(
        joinedload(SupplierProduct.product)
    ).filter(
        SupplierProduct.supplier_id == supplier_id,
        SupplierProduct.company_id == current_user.company_id
    )
    if active_only:
        query = query.filter(SupplierProduct.is_active == True)

    return [_to_response(e) for e in query.all()]


@router.post("/suppliers/{supplier_id}/catalog", response_model=SupplierProductResponse, status_code=201)
async def add_to_supplier_catalog(
    supplier_id: UUID,
    data: SupplierProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers.write"))
):
    """Add a product to a supplier's catalog."""
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.company_id == current_user.company_id
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    product = db.query(Product).filter(
        Product.id == data.product_id,
        Product.company_id == current_user.company_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Check for duplicate
    existing = db.query(SupplierProduct).filter(
        SupplierProduct.supplier_id == supplier_id,
        SupplierProduct.product_id == data.product_id,
        SupplierProduct.company_id == current_user.company_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="El producto ya está en el catálogo de este proveedor")

    entry = SupplierProduct(
        company_id=current_user.company_id,
        supplier_id=supplier_id,
        **data.model_dump()
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    # Reload with product relationship
    entry = db.query(SupplierProduct).options(
        joinedload(SupplierProduct.product)
    ).filter(SupplierProduct.id == entry.id).first()
    return _to_response(entry)


@router.put("/suppliers/{supplier_id}/catalog/{entry_id}", response_model=SupplierProductResponse)
async def update_catalog_entry(
    supplier_id: UUID,
    entry_id: UUID,
    data: SupplierProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers.write"))
):
    """Update a catalog entry (price, reference, etc.)."""
    entry = db.query(SupplierProduct).options(
        joinedload(SupplierProduct.product)
    ).filter(
        SupplierProduct.id == entry_id,
        SupplierProduct.supplier_id == supplier_id,
        SupplierProduct.company_id == current_user.company_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada de catálogo no encontrada")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return _to_response(entry)


@router.delete("/suppliers/{supplier_id}/catalog/{entry_id}", status_code=204)
async def remove_from_catalog(
    supplier_id: UUID,
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers.write"))
):
    """Remove a product from a supplier's catalog."""
    entry = db.query(SupplierProduct).filter(
        SupplierProduct.id == entry_id,
        SupplierProduct.supplier_id == supplier_id,
        SupplierProduct.company_id == current_user.company_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada de catálogo no encontrada")

    db.delete(entry)
    db.commit()


# ---------------------------------------------------------------------------
# Global catalog search
# ---------------------------------------------------------------------------

@router.get("/catalog/search", response_model=List[CatalogSearchResult])
async def search_catalog(
    q: Optional[str] = Query(None, min_length=1),
    supplier_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers.read"))
):
    """Search across all supplier catalog entries. Returns products with purchase/sale prices and margin."""
    query = db.query(SupplierProduct).options(
        joinedload(SupplierProduct.product),
        joinedload(SupplierProduct.supplier)
    ).filter(
        SupplierProduct.company_id == current_user.company_id,
        SupplierProduct.is_active == True
    )

    if supplier_id:
        query = query.filter(SupplierProduct.supplier_id == supplier_id)

    if q:
        search_term = f"%{q}%"
        query = query.join(SupplierProduct.product).filter(
            (Product.name.ilike(search_term)) |
            (Product.code.ilike(search_term)) |
            (SupplierProduct.supplier_ref.ilike(search_term))
        )

    entries = query.limit(limit).all()

    results = []
    for entry in entries:
        p = entry.product
        s = entry.supplier
        if not p or not s:
            continue
        purchase = entry.purchase_price or 0.0
        sale = p.sale_price or 0.0
        margin = ((sale - purchase) / purchase * 100) if purchase > 0 else None
        results.append(CatalogSearchResult(
            id=entry.id,
            supplier_id=s.id,
            supplier_name=s.name,
            supplier_code=s.code,
            product_id=p.id,
            product_code=p.code,
            product_name=p.name,
            supplier_ref=entry.supplier_ref,
            purchase_price=purchase,
            sale_price=sale,
            margin_pct=round(margin, 1) if margin is not None else None,
            lead_time_days=entry.lead_time_days or 0,
        ))

    return results
