"""
Suppliers CRUD endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user, require_permission
from app.models import Supplier, User
from app.schemas import (
    SupplierCreate, SupplierUpdate, SupplierResponse, SupplierList, MessageResponse
)

router = APIRouter(prefix="/suppliers", tags=["Proveedores"])


@router.get("", response_model=SupplierList)
async def list_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers.read"))
):
    """Listar proveedores."""
    query = db.query(Supplier).filter(Supplier.company_id == current_user.company_id)

    if active_only:
        query = query.filter(Supplier.is_active == True)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Supplier.name.ilike(search_term)) |
            (Supplier.code.ilike(search_term))
        )

    total = query.count()
    suppliers = query.order_by(Supplier.name).offset(skip).limit(limit).all()

    return SupplierList(
        items=[SupplierResponse.model_validate(s) for s in suppliers],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers.create"))
):
    """Crear proveedor."""
    existing = db.query(Supplier).filter(
        Supplier.company_id == current_user.company_id,
        Supplier.code == data.code
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un proveedor con el codigo {data.code}"
        )

    supplier = Supplier(
        company_id=current_user.company_id,
        **data.model_dump()
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    return SupplierResponse.model_validate(supplier)


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers.read"))
):
    """Obtener proveedor."""
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.company_id == current_user.company_id
    ).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    return SupplierResponse.model_validate(supplier)


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: UUID,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers.update"))
):
    """Actualizar proveedor."""
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.company_id == current_user.company_id
    ).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    if data.code and data.code != supplier.code:
        existing = db.query(Supplier).filter(
            Supplier.company_id == current_user.company_id,
            Supplier.code == data.code,
            Supplier.id != supplier_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un proveedor con el codigo {data.code}"
            )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    db.commit()
    db.refresh(supplier)

    return SupplierResponse.model_validate(supplier)


@router.delete("/{supplier_id}", response_model=MessageResponse)
async def delete_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers.delete"))
):
    """Eliminar proveedor (soft delete)."""
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.company_id == current_user.company_id
    ).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    supplier.is_active = False
    db.commit()

    return MessageResponse(message=f"Proveedor {supplier.code} eliminado")
