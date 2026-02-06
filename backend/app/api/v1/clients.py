"""
Clients CRUD endpoints.
All operations are scoped to the current user's company.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user, require_permission
from app.models import Client, User
from app.schemas import (
    ClientCreate, ClientUpdate, ClientResponse, ClientList, MessageResponse
)

router = APIRouter(prefix="/clients", tags=["Clientes"])


@router.get("", response_model=ClientList)
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None, description="Buscar por nombre o codigo"),
    active_only: bool = Query(True, description="Solo clientes activos"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clients.read"))
):
    """Listar clientes de la empresa."""
    query = db.query(Client).filter(Client.company_id == current_user.company_id)

    if active_only:
        query = query.filter(Client.is_active == True)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Client.name.ilike(search_term)) |
            (Client.code.ilike(search_term))
        )

    total = query.count()
    clients = query.order_by(Client.name).offset(skip).limit(limit).all()

    return ClientList(
        items=[ClientResponse.model_validate(c) for c in clients],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clients.create"))
):
    """Crear nuevo cliente."""
    # Check code uniqueness within company
    existing = db.query(Client).filter(
        Client.company_id == current_user.company_id,
        Client.code == data.code
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un cliente con el codigo {data.code}"
        )

    client = Client(
        company_id=current_user.company_id,
        **data.model_dump()
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    return ClientResponse.model_validate(client)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clients.read"))
):
    """Obtener cliente por ID."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.company_id == current_user.company_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    return ClientResponse.model_validate(client)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clients.update"))
):
    """Actualizar cliente."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.company_id == current_user.company_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    # Check code uniqueness if changing
    if data.code and data.code != client.code:
        existing = db.query(Client).filter(
            Client.company_id == current_user.company_id,
            Client.code == data.code,
            Client.id != client_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un cliente con el codigo {data.code}"
            )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)

    return ClientResponse.model_validate(client)


@router.delete("/{client_id}", response_model=MessageResponse)
async def delete_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clients.delete"))
):
    """Eliminar cliente (soft delete)."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.company_id == current_user.company_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    # Soft delete
    client.is_active = False
    db.commit()

    return MessageResponse(message=f"Cliente {client.code} eliminado")
