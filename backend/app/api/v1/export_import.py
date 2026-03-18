"""
Export/Import CSV endpoints.
Export clients, products, suppliers to CSV.
Import clients and products from CSV.
"""
import csv
import io
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.models import Client, Product, Supplier, User
from app.schemas.base import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export/Import"])

ALLOWED_CSV_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
}
MAX_IMPORT_FILE_SIZE_BYTES = 2 * 1024 * 1024
MAX_IMPORT_ROWS = 10000


def _sanitize_csv_cell(value: Optional[object]) -> str:
    """Prevent CSV formula injection by prefixing risky cell values."""
    if value is None:
        return ""
    text = str(value)
    if text.startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text


def _validate_csv_upload(file: UploadFile, content: bytes):
    """Validate basic CSV upload constraints before parsing."""
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser CSV"
        )

    if file.content_type and file.content_type not in ALLOWED_CSV_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo no permitido"
        )

    if len(content) > MAX_IMPORT_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Archivo demasiado grande"
        )


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
    current_user: User = Depends(require_permission("export.read"))
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
            _sanitize_csv_cell(c.code), _sanitize_csv_cell(c.name), _sanitize_csv_cell(c.tax_id or ""), _sanitize_csv_cell(c.address or ""),
            _sanitize_csv_cell(c.city or ""), _sanitize_csv_cell(c.postal_code or ""), _sanitize_csv_cell(c.province or ""),
            _sanitize_csv_cell(c.country or ""), _sanitize_csv_cell(c.phone or ""), _sanitize_csv_cell(c.email or ""),
            _sanitize_csv_cell(c.website or ""), _sanitize_csv_cell(c.notes or "")
        ])

    logger.info(f"Exported {len(rows)} clients for company {current_user.company_id}")
    return _stream_csv(rows, headers, "clients.csv")


@router.get("/products")
async def export_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("export.read"))
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
            _sanitize_csv_cell(p.code), _sanitize_csv_cell(p.name), _sanitize_csv_cell(p.description or ""), _sanitize_csv_cell(p.category or ""),
            _sanitize_csv_cell(p.purchase_price), _sanitize_csv_cell(p.sale_price), _sanitize_csv_cell(p.current_stock),
            _sanitize_csv_cell(p.minimum_stock), _sanitize_csv_cell(p.stock_unit or "")
        ])

    logger.info(f"Exported {len(rows)} products for company {current_user.company_id}")
    return _stream_csv(rows, headers, "products.csv")


@router.get("/suppliers")
async def export_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("export.read"))
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
            _sanitize_csv_cell(s.code), _sanitize_csv_cell(s.name), _sanitize_csv_cell(s.tax_id or ""), _sanitize_csv_cell(s.address or ""),
            _sanitize_csv_cell(s.city or ""), _sanitize_csv_cell(s.postal_code or ""), _sanitize_csv_cell(s.province or ""),
            _sanitize_csv_cell(s.country or ""), _sanitize_csv_cell(s.phone or ""), _sanitize_csv_cell(s.email or ""),
            _sanitize_csv_cell(s.website or ""), _sanitize_csv_cell(s.notes or "")
        ])

    logger.info(f"Exported {len(rows)} suppliers for company {current_user.company_id}")
    return _stream_csv(rows, headers, "suppliers.csv")


@router.post("/import/clients", response_model=MessageResponse)
async def import_clients(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("export.write"))
):
    """
    Import clients from CSV file.
    Expected columns: code, name, tax_id, address, city, postal_code,
    province, country, phone, email, website, notes
    Skips rows with duplicate codes.
    """
    content = await file.read()
    _validate_csv_upload(file, content)
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo CSV debe estar codificado en UTF-8"
        )

    reader = csv.DictReader(io.StringIO(text))

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        if i - 1 > MAX_IMPORT_ROWS:
            errors.append(f"Se alcanzó el límite de filas ({MAX_IMPORT_ROWS})")
            break

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
    current_user: User = Depends(require_permission("export.write"))
):
    """
    Import products from CSV file.
    Expected columns: code, name, description, category, purchase_price,
    sale_price, current_stock, minimum_stock, stock_unit
    Skips rows with duplicate codes.
    """
    content = await file.read()
    _validate_csv_upload(file, content)
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo CSV debe estar codificado en UTF-8"
        )

    reader = csv.DictReader(io.StringIO(text))

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        if i - 1 > MAX_IMPORT_ROWS:
            errors.append(f"Se alcanzó el límite de filas ({MAX_IMPORT_ROWS})")
            break

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
