"""
Export/Import CSV/XLSX endpoints.
Export clients, products, suppliers to CSV.
Import clients, products, suppliers, workers and diary from CSV or XLSX.
"""
import csv
import io
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Form, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.models import Client, Product, Supplier, Worker, DiaryEntry, User
from app.schemas.base import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export/Import"])

ALLOWED_CSV_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
}
ALLOWED_XLSX_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
}
MAX_IMPORT_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB for xlsx support
MAX_IMPORT_ROWS = 10000
PREVIEW_SAMPLE_ROWS = 5


class ImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    skipped_rows: int
    error_rows: int
    errors: List[str]
    sample: List[Dict[str, Any]]
    headers: List[str]


def _parse_datetime(value: str) -> Optional[datetime]:
    """Parse common datetime/date formats used in CSV imports."""
    text = (value or "").strip()
    if not text:
        return None

    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    raise ValueError(f"fecha invalida: {text}")


def _parse_bool(value: str) -> bool:
    """Parse truthy strings from CSV imports."""
    text = (value or "").strip().lower()
    return text in {"1", "true", "yes", "si", "sí", "y"}


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


def _validate_xlsx_upload(file: UploadFile, content: bytes):
    """Validate basic XLSX upload constraints before parsing."""
    filename = (file.filename or "").lower()
    if not (filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser CSV o XLSX"
        )
    if len(content) > MAX_IMPORT_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Archivo demasiado grande (máx. 5 MB)"
        )


def _parse_xlsx_to_rows(content: bytes) -> tuple[list, list]:
    """Parse xlsx content into (headers, list_of_dicts)."""
    try:
        import openpyxl
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="openpyxl no instalado en el servidor"
        )
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)

    try:
        header_row = next(rows_iter)
    except StopIteration:
        return [], []

    headers = [str(h).strip() if h is not None else "" for h in header_row]

    data_rows = []
    for row in rows_iter:
        row_dict = {}
        for i, val in enumerate(row):
            key = headers[i] if i < len(headers) else f"col_{i}"
            row_dict[key] = str(val).strip() if val is not None else ""
        data_rows.append(row_dict)

    wb.close()
    return headers, data_rows


def _is_xlsx(file: UploadFile) -> bool:
    filename = (file.filename or "").lower()
    return filename.endswith(".xlsx") or filename.endswith(".xls")


def _parse_file_to_rows(file: UploadFile, content: bytes) -> tuple[list, list]:
    """Parse CSV or XLSX file into (headers, list_of_dicts)."""
    if _is_xlsx(file):
        _validate_xlsx_upload(file, content)
        return _parse_xlsx_to_rows(content)
    else:
        _validate_csv_upload(file, content)
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo CSV debe estar codificado en UTF-8"
            )
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        headers = list(reader.fieldnames or [])
        return headers, rows


# ENTITY_TYPE → required fields for validation
ENTITY_REQUIRED_FIELDS: dict[str, list[str]] = {
    "clients": ["code", "name"],
    "products": ["code", "name"],
    "suppliers": ["code", "name"],
    "workers": ["code", "first_name", "last_name"],
    "diary": ["title", "content", "entry_date"],
}


@router.post("/import/preview", response_model=ImportPreviewResponse)
async def import_preview(
    entity_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("export.write"))
):
    """
    Preview import without inserting data.
    Returns stats and first 5 sample rows.
    """
    if entity_type not in ENTITY_REQUIRED_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo no soportado: {entity_type}. Valores válidos: {list(ENTITY_REQUIRED_FIELDS)}"
        )

    content = await file.read()
    headers, rows = _parse_file_to_rows(file, content)
    required = ENTITY_REQUIRED_FIELDS[entity_type]

    total_rows = len(rows)
    valid_rows = 0
    error_rows = 0
    errors: list[str] = []
    sample: list[dict] = []

    for i, row in enumerate(rows, start=2):
        if len(errors) >= 20:
            break  # cap error list

        missing = [f for f in required if not row.get(f, "").strip()]
        if missing:
            errors.append(f"Fila {i}: faltan campos obligatorios ({', '.join(missing)})")
            error_rows += 1
        else:
            valid_rows += 1
            if len(sample) < PREVIEW_SAMPLE_ROWS:
                # Limit cell values to 100 chars to avoid leaking large data
                sample.append({k: str(v)[:100] for k, v in row.items()})

    skipped_rows = 0  # duplicates only known at import time, not preview

    logger.info(
        f"Import preview: entity={entity_type} total={total_rows} valid={valid_rows} "
        f"errors={error_rows} user={current_user.id}"
    )

    return ImportPreviewResponse(
        total_rows=total_rows,
        valid_rows=valid_rows,
        skipped_rows=skipped_rows,
        error_rows=error_rows,
        errors=errors,
        sample=sample,
        headers=headers[:20],  # cap headers to prevent data leakage
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
    Import clients from CSV or XLSX file.
    Expected columns: code, name, tax_id, address, city, postal_code,
    province, country, phone, email, website, notes
    Skips rows with duplicate codes.
    """
    content = await file.read()
    _, rows = _parse_file_to_rows(file, content)

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(rows, start=2):
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
    Import products from CSV or XLSX file.
    Expected columns: code, name, description, category, purchase_price,
    sale_price, current_stock, minimum_stock, stock_unit
    Skips rows with duplicate codes.
    """
    content = await file.read()
    _, rows = _parse_file_to_rows(file, content)

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(rows, start=2):
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


@router.post("/import/suppliers", response_model=MessageResponse)
async def import_suppliers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("export.write"))
):
    """
    Import suppliers from CSV or XLSX file.
    Expected columns: code, name, tax_id, address, city, postal_code,
    province, country, phone, email, website, notes
    Skips rows with duplicate codes.
    """
    content = await file.read()
    _, rows = _parse_file_to_rows(file, content)

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(rows, start=2):
        if i - 1 > MAX_IMPORT_ROWS:
            errors.append(f"Se alcanzó el límite de filas ({MAX_IMPORT_ROWS})")
            break

        code = row.get("code", "").strip()
        name = row.get("name", "").strip()

        if not code or not name:
            errors.append(f"Fila {i}: code y name son obligatorios")
            continue

        existing = db.query(Supplier).filter(
            Supplier.company_id == current_user.company_id,
            Supplier.code == code
        ).first()

        if existing:
            skipped += 1
            continue

        supplier = Supplier(
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
        db.add(supplier)
        created += 1

    db.commit()
    logger.info(f"Imported {created} suppliers for company {current_user.company_id}")

    msg = f"Importados: {created}, Omitidos (duplicados): {skipped}"
    if errors:
        msg += f", Errores: {len(errors)}"
    return MessageResponse(message=msg)


@router.post("/import/workers", response_model=MessageResponse)
async def import_workers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("export.write"))
):
    """
    Import workers from CSV or XLSX file.
    Expected columns: code, first_name, last_name, phone, email, address,
    position, department, hire_date, salary
    Skips rows with duplicate codes.
    """
    content = await file.read()
    _, rows = _parse_file_to_rows(file, content)

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(rows, start=2):
        if i - 1 > MAX_IMPORT_ROWS:
            errors.append(f"Se alcanzó el límite de filas ({MAX_IMPORT_ROWS})")
            break

        code = row.get("code", "").strip()
        first_name = row.get("first_name", "").strip()
        last_name = row.get("last_name", "").strip()

        if not code or not first_name or not last_name:
            errors.append(f"Fila {i}: code, first_name y last_name son obligatorios")
            continue

        existing = db.query(Worker).filter(
            Worker.company_id == current_user.company_id,
            Worker.code == code
        ).first()

        if existing:
            skipped += 1
            continue

        hire_date_raw = row.get("hire_date", "")
        try:
            hire_date = _parse_datetime(hire_date_raw) if hire_date_raw.strip() else None
        except ValueError as e:
            errors.append(f"Fila {i}: {str(e)}")
            continue

        salary_raw = row.get("salary", "").strip()
        try:
            salary = float(salary_raw) if salary_raw else None
        except ValueError:
            errors.append(f"Fila {i}: salary invalido")
            continue

        worker = Worker(
            company_id=current_user.company_id,
            code=code,
            first_name=first_name,
            last_name=last_name,
            phone=row.get("phone", "").strip() or None,
            email=row.get("email", "").strip() or None,
            address=row.get("address", "").strip() or None,
            position=row.get("position", "").strip() or None,
            department=row.get("department", "").strip() or None,
            hire_date=hire_date,
            salary=salary,
        )
        db.add(worker)
        created += 1

    db.commit()
    logger.info(f"Imported {created} workers for company {current_user.company_id}")

    msg = f"Importados: {created}, Omitidos (duplicados): {skipped}"
    if errors:
        msg += f", Errores: {len(errors)}"
    return MessageResponse(message=msg)


@router.post("/import/diary", response_model=MessageResponse)
async def import_diary_entries(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("export.write"))
):
    """
    Import diary entries from CSV or XLSX file.
    Expected columns: title, content, entry_date, tags, is_pinned
    Skips rows with duplicate title+entry_date.
    """
    content = await file.read()
    _, rows = _parse_file_to_rows(file, content)

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(rows, start=2):
        if i - 1 > MAX_IMPORT_ROWS:
            errors.append(f"Se alcanzó el límite de filas ({MAX_IMPORT_ROWS})")
            break

        title = row.get("title", "").strip()
        content_text = row.get("content", "").strip()
        entry_date_raw = row.get("entry_date", "").strip()

        if not title or not content_text or not entry_date_raw:
            errors.append(f"Fila {i}: title, content y entry_date son obligatorios")
            continue

        try:
            entry_date = _parse_datetime(entry_date_raw)
        except ValueError as e:
            errors.append(f"Fila {i}: {str(e)}")
            continue

        existing = db.query(DiaryEntry).filter(
            DiaryEntry.company_id == current_user.company_id,
            DiaryEntry.title == title,
            DiaryEntry.entry_date == entry_date
        ).first()

        if existing:
            skipped += 1
            continue

        entry = DiaryEntry(
            company_id=current_user.company_id,
            user_id=current_user.id,
            title=title,
            content=content_text,
            entry_date=entry_date,
            tags=row.get("tags", "").strip() or None,
            is_pinned=_parse_bool(row.get("is_pinned", "")),
        )
        db.add(entry)
        created += 1

    db.commit()
    logger.info(f"Imported {created} diary entries for company {current_user.company_id}")

    msg = f"Importados: {created}, Omitidos (duplicados): {skipped}"
    if errors:
        msg += f", Errores: {len(errors)}"
    return MessageResponse(message=msg)
