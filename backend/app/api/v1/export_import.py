"""
Export/Import CSV endpoints.
Export clients, products, suppliers to CSV.
Import clients and products from CSV.
"""
import csv
import io
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import Client, Product, Supplier, User
from app.schemas.base import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export/Import"])


def _stream_csv(rows: list, headers: list, filename: str) -> StreamingResponse:
    """Create a StreamingResponse with CSV content."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/clients")
async def export_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export all active clients to CSV."""
    clients = db.query(Client).filter(
        Client.company_id == current_user.company_id,
        Client.is_active == True
    ).order_by(Client.code).all()

    headers = ["code", "name", "tax_id", "address", "city", "postal_code",
               "province", "country", "phone", "email", "website", "notes"]

    rows = []
    for c in clients:
        rows.append([
            c.code, c.name, c.tax_id or "", c.address or "",
            c.city or "", c.postal_code or "", c.province or "",
            c.country or "", c.phone or "", c.email or "",
            c.website or "", c.notes or ""
        ])

    logger.info(f"Exported {len(rows)} clients for company {current_user.company_id}")
    return _stream_csv(rows, headers, "clients.csv")


@router.get("/products")
async def export_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export all active products to CSV."""
    products = db.query(Product).filter(
        Product.company_id == current_user.company_id,
        Product.is_active == True
    ).order_by(Product.code).all()

    headers = ["code", "name", "description", "category", "purchase_price",
               "sale_price", "current_stock", "minimum_stock", "stock_unit"]

    rows = []
    for p in products:
        rows.append([
            p.code, p.name, p.description or "", p.category or "",
            p.purchase_price, p.sale_price, p.current_stock,
            p.minimum_stock, p.stock_unit or ""
        ])

    logger.info(f"Exported {len(rows)} products for company {current_user.company_id}")
    return _stream_csv(rows, headers, "products.csv")


@router.get("/suppliers")
async def export_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export all active suppliers to CSV."""
    suppliers = db.query(Supplier).filter(
        Supplier.company_id == current_user.company_id,
        Supplier.is_active == True
    ).order_by(Supplier.code).all()

    headers = ["code", "name", "tax_id", "address", "city", "postal_code",
               "province", "country", "phone", "email", "website", "notes"]

    rows = []
    for s in suppliers:
        rows.append([
            s.code, s.name, s.tax_id or "", s.address or "",
            s.city or "", s.postal_code or "", s.province or "",
            s.country or "", s.phone or "", s.email or "",
            s.website or "", s.notes or ""
        ])

    logger.info(f"Exported {len(rows)} suppliers for company {current_user.company_id}")
    return _stream_csv(rows, headers, "suppliers.csv")


@router.post("/import/clients", response_model=MessageResponse)
async def import_clients(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import clients from CSV file.
    Expected columns: code, name, tax_id, address, city, postal_code,
    province, country, phone, email, website, notes
    Skips rows with duplicate codes.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser CSV"
        )

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        code = row.get("code", "").strip()
        name = row.get("name", "").strip()

        if not code or not name:
            errors.append(f"Fila {i}: code y name son obligatorios")
            continue

        existing = db.query(Client).filter(
            Client.company_id == current_user.company_id,
            Client.code == code
        ).first()

        if existing:
            skipped += 1
            continue

        client = Client(
            company_id=current_user.company_id,
            code=code,
            name=name,
            tax_id=row.get("tax_id", "").strip() or None,
            address=row.get("address", "").strip() or None,
            city=row.get("city", "").strip() or None,
            postal_code=row.get("postal_code", "").strip() or None,
            province=row.get("province", "").strip() or None,
            country=row.get("country", "").strip() or "Espana",
            phone=row.get("phone", "").strip() or None,
            email=row.get("email", "").strip() or None,
            website=row.get("website", "").strip() or None,
            notes=row.get("notes", "").strip() or None,
        )
        db.add(client)
        created += 1

    db.commit()
    logger.info(f"Imported {created} clients for company {current_user.company_id}")

    msg = f"Importados: {created}, Omitidos (duplicados): {skipped}"
    if errors:
        msg += f", Errores: {len(errors)}"
    return MessageResponse(message=msg)


@router.post("/import/products", response_model=MessageResponse)
async def import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import products from CSV file.
    Expected columns: code, name, description, category, purchase_price,
    sale_price, current_stock, minimum_stock, stock_unit
    Skips rows with duplicate codes.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser CSV"
        )

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        code = row.get("code", "").strip()
        name = row.get("name", "").strip()

        if not code or not name:
            errors.append(f"Fila {i}: code y name son obligatorios")
            continue

        existing = db.query(Product).filter(
            Product.company_id == current_user.company_id,
            Product.code == code
        ).first()

        if existing:
            skipped += 1
            continue

        try:
            product = Product(
                company_id=current_user.company_id,
                code=code,
                name=name,
                description=row.get("description", "").strip() or None,
                category=row.get("category", "").strip() or None,
                purchase_price=float(row.get("purchase_price", 0) or 0),
                sale_price=float(row.get("sale_price", 0) or 0),
                current_stock=int(row.get("current_stock", 0) or 0),
                minimum_stock=int(row.get("minimum_stock", 0) or 0),
                stock_unit=row.get("stock_unit", "").strip() or "unidades",
            )
            db.add(product)
            created += 1
        except (ValueError, TypeError) as e:
            errors.append(f"Fila {i}: {str(e)}")

    db.commit()
    logger.info(f"Imported {created} products for company {current_user.company_id}")

    msg = f"Importados: {created}, Omitidos (duplicados): {skipped}"
    if errors:
        msg += f", Errores: {len(errors)}"
    return MessageResponse(message=msg)
