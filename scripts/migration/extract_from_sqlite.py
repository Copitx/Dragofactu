#!/usr/bin/env python3
"""
Extract migration CSV datasets from a local SQLite database.

This helper produces files compatible with migrate_to_dragofactu.py:
- clients.csv
- products.csv
- suppliers.csv
- workers.csv
- documents.csv
- document_lines.csv
- diary_entries.csv
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path
from typing import Iterable, Sequence

CLIENT_HEADERS = [
    "code",
    "name",
    "tax_id",
    "address",
    "city",
    "postal_code",
    "province",
    "country",
    "phone",
    "email",
    "website",
    "notes",
]

PRODUCT_HEADERS = [
    "code",
    "name",
    "description",
    "category",
    "purchase_price",
    "sale_price",
    "current_stock",
    "minimum_stock",
    "stock_unit",
    "supplier_code",
]

SUPPLIER_HEADERS = [
    "code",
    "name",
    "tax_id",
    "address",
    "city",
    "postal_code",
    "province",
    "country",
    "phone",
    "email",
    "website",
    "notes",
]

WORKER_HEADERS = [
    "code",
    "first_name",
    "last_name",
    "phone",
    "email",
    "address",
    "position",
    "department",
    "hire_date",
    "salary",
]

DOCUMENT_HEADERS = [
    "document_ref",
    "type",
    "client_code",
    "issue_date",
    "due_date",
    "notes",
    "internal_notes",
    "terms",
    "status",
]

DOCUMENT_LINE_HEADERS = [
    "document_ref",
    "line_type",
    "product_code",
    "description",
    "quantity",
    "unit_price",
    "discount_percent",
]

DIARY_HEADERS = [
    "title",
    "content",
    "entry_date",
    "tags",
    "is_pinned",
]


def _normalize_type(value: object) -> str:
    text = str(value or "").strip().lower()
    mapping = {
        "quote": "quote",
        "delivery_note": "delivery_note",
        "delivery note": "delivery_note",
        "invoice": "invoice",
        "documenttype.quote": "quote",
        "documenttype.delivery_note": "delivery_note",
        "documenttype.invoice": "invoice",
        "quote": "quote",
        "deliverynote": "delivery_note",
    }

    if text in mapping:
        return mapping[text]

    upper = str(value or "").strip().upper()
    enum_mapping = {
        "QUOTE": "quote",
        "DELIVERY_NOTE": "delivery_note",
        "INVOICE": "invoice",
    }
    return enum_mapping.get(upper, text)


def _normalize_status(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "draft"

    lower = text.lower()
    mapping = {
        "draft": "draft",
        "not_sent": "not_sent",
        "sent": "sent",
        "accepted": "accepted",
        "rejected": "rejected",
        "paid": "paid",
        "partially_paid": "partially_paid",
        "cancelled": "cancelled",
    }
    if lower in mapping:
        return mapping[lower]

    upper = text.upper()
    enum_mapping = {
        "DRAFT": "draft",
        "NOT_SENT": "not_sent",
        "SENT": "sent",
        "ACCEPTED": "accepted",
        "REJECTED": "rejected",
        "PAID": "paid",
        "PARTIALLY_PAID": "partially_paid",
        "CANCELLED": "cancelled",
    }
    return enum_mapping.get(upper, lower)


def _as_str(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _write_csv(path: Path, headers: Sequence[str], rows: Iterable[Sequence[object]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([_as_str(col) for col in row])
            count += 1
    return count


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cursor = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def extract(db_path: Path, out_dir: Path, include_inactive: bool) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    active_filter = "" if include_inactive else "WHERE COALESCE(is_active, 1) = 1"

    suppliers_rows = conn.execute(
        f"""
        SELECT code, name, tax_id, address, city, postal_code, province,
               country, phone, email, website, notes
        FROM suppliers
        {active_filter}
        ORDER BY code
        """
    ).fetchall()

    clients_rows = conn.execute(
        f"""
        SELECT code, name, tax_id, address, city, postal_code, province,
               country, phone, email, website, notes
        FROM clients
        {active_filter}
        ORDER BY code
        """
    ).fetchall()

    products_rows = conn.execute(
        f"""
        SELECT p.code, p.name, p.description, p.category,
               p.purchase_price, p.sale_price, p.current_stock, p.minimum_stock,
               p.stock_unit, COALESCE(s.code, '') AS supplier_code
        FROM products p
        LEFT JOIN suppliers s ON s.id = p.supplier_id
        {active_filter.replace('is_active', 'p.is_active')}
        ORDER BY p.code
        """
    ).fetchall()

    workers_rows = []
    if _table_exists(conn, "workers"):
        workers_rows = conn.execute(
            f"""
            SELECT code, first_name, last_name, phone, email, address,
                   position, department, hire_date, salary
            FROM workers
            {active_filter}
            ORDER BY code
            """
        ).fetchall()

    documents_rows = []
    if _table_exists(conn, "documents"):
        documents_rows = conn.execute(
            """
            SELECT d.code AS document_ref,
                   d.type,
                   COALESCE(c.code, '') AS client_code,
                   d.issue_date,
                   d.due_date,
                   d.notes,
                   d.internal_notes,
                   d.terms,
                   d.status
            FROM documents d
            LEFT JOIN clients c ON c.id = d.client_id
            ORDER BY d.issue_date, d.code
            """
        ).fetchall()

    document_lines_rows = []
    if _table_exists(conn, "document_lines"):
        document_lines_rows = conn.execute(
            """
            SELECT d.code AS document_ref,
                   COALESCE(dl.line_type, 'product') AS line_type,
                   COALESCE(p.code, '') AS product_code,
                   dl.description,
                   dl.quantity,
                   dl.unit_price,
                   dl.discount_percent
            FROM document_lines dl
            JOIN documents d ON d.id = dl.document_id
            LEFT JOIN products p ON p.id = dl.product_id
            ORDER BY d.code, COALESCE(dl.order_index, 0)
            """
        ).fetchall()

    diary_rows = []
    if _table_exists(conn, "diary_entries"):
        diary_rows = conn.execute(
            """
            SELECT title, content, entry_date, tags, is_pinned
            FROM diary_entries
            ORDER BY entry_date
            """
        ).fetchall()

    counts = {}
    counts["suppliers.csv"] = _write_csv(
        out_dir / "suppliers.csv",
        SUPPLIER_HEADERS,
        (
            (
                r["code"], r["name"], r["tax_id"], r["address"], r["city"], r["postal_code"],
                r["province"], r["country"], r["phone"], r["email"], r["website"], r["notes"],
            )
            for r in suppliers_rows
        ),
    )

    counts["clients.csv"] = _write_csv(
        out_dir / "clients.csv",
        CLIENT_HEADERS,
        (
            (
                r["code"], r["name"], r["tax_id"], r["address"], r["city"], r["postal_code"],
                r["province"], r["country"], r["phone"], r["email"], r["website"], r["notes"],
            )
            for r in clients_rows
        ),
    )

    counts["products.csv"] = _write_csv(
        out_dir / "products.csv",
        PRODUCT_HEADERS,
        (
            (
                r["code"], r["name"], r["description"], r["category"], r["purchase_price"],
                r["sale_price"], r["current_stock"], r["minimum_stock"], r["stock_unit"],
                r["supplier_code"],
            )
            for r in products_rows
        ),
    )

    counts["workers.csv"] = _write_csv(
        out_dir / "workers.csv",
        WORKER_HEADERS,
        (
            (
                r["code"], r["first_name"], r["last_name"], r["phone"], r["email"],
                r["address"], r["position"], r["department"], r["hire_date"], r["salary"],
            )
            for r in workers_rows
        ),
    )

    counts["documents.csv"] = _write_csv(
        out_dir / "documents.csv",
        DOCUMENT_HEADERS,
        (
            (
                r["document_ref"],
                _normalize_type(r["type"]),
                r["client_code"],
                r["issue_date"],
                r["due_date"],
                r["notes"],
                r["internal_notes"],
                r["terms"],
                _normalize_status(r["status"]),
            )
            for r in documents_rows
        ),
    )

    counts["document_lines.csv"] = _write_csv(
        out_dir / "document_lines.csv",
        DOCUMENT_LINE_HEADERS,
        (
            (
                r["document_ref"], r["line_type"], r["product_code"], r["description"],
                r["quantity"], r["unit_price"], r["discount_percent"],
            )
            for r in document_lines_rows
        ),
    )

    counts["diary_entries.csv"] = _write_csv(
        out_dir / "diary_entries.csv",
        DIARY_HEADERS,
        (
            (
                r["title"], r["content"], r["entry_date"], r["tags"],
                "true" if str(r["is_pinned"] or "").strip() in {"1", "true", "True"} else "false",
            )
            for r in diary_rows
        ),
    )

    print(f"Extraccion completada desde {db_path}")
    for filename, row_count in counts.items():
        print(f"- {filename}: {row_count} filas")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract migration CSV files from SQLite source")
    parser.add_argument("--db-path", required=True, help="Path to source SQLite database")
    parser.add_argument("--out-dir", required=True, help="Destination directory for migration CSV files")
    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include inactive rows for entities with is_active column",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    db_path = Path(args.db_path).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()

    if not db_path.exists():
        print(f"ERROR: no existe base de datos {db_path}")
        return 1

    extract(db_path=db_path, out_dir=out_dir, include_inactive=bool(args.include_inactive))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
