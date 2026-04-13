#!/usr/bin/env python3
"""
Migration runner for Dragofactu (wave-based).

This tool implements the first executable part of the migration plan:
- Validate CSV files and business constraints.
- Run wave "masters" (suppliers, clients, products, workers).
- Run wave "operations" (documents + document_lines).
- Run wave "diary" (current operational diary entries).
- Support dry-run mode for safe rehearsals.

Expected CSV files inside --data-dir:
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
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


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

ALLOWED_DOC_TYPES = {"quote", "delivery_note", "invoice"}
ALLOWED_DOC_STATUS = {
    "draft",
    "not_sent",
    "sent",
    "accepted",
    "rejected",
    "paid",
    "partially_paid",
    "cancelled",
}

STATUS_PATHS = {
    "draft": [],
    "not_sent": ["not_sent"],
    "sent": ["not_sent", "sent"],
    "accepted": ["not_sent", "sent", "accepted"],
    "rejected": ["not_sent", "sent", "rejected"],
    "partially_paid": ["not_sent", "sent", "accepted", "partially_paid"],
    "paid": ["not_sent", "sent", "accepted", "paid"],
    "cancelled": ["not_sent", "cancelled"],
}


class MigrationError(Exception):
    """Domain error for migration operations."""


class APIError(MigrationError):
    """HTTP/API error wrapper."""

    def __init__(self, status: int, detail: str):
        super().__init__(f"HTTP {status}: {detail}")
        self.status = status
        self.detail = detail


@dataclass
class Stats:
    created: int = 0
    skipped: int = 0
    errors: int = 0


class DragofactuAPI:
    def __init__(self, base_url: str, token: str, timeout: int = 30):
        self.base_url = self._normalize_base_url(base_url)
        self.token = token
        self.timeout = timeout

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        raw = (base_url or "").strip().rstrip("/")
        if not raw:
            raise MigrationError("--base-url es obligatorio")
        if raw.endswith("/api/v1"):
            return raw
        return f"{raw}/api/v1"

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, object]] = None,
        payload: Optional[Dict[str, object]] = None,
    ) -> object:
        query = ""
        if params:
            query = "?" + urllib.parse.urlencode(params)

        url = f"{self.base_url}{path}{query}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

        data: Optional[bytes] = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url=url, data=data, headers=headers, method=method.upper())

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                if not body:
                    return {}
                try:
                    return json.loads(body)
                except json.JSONDecodeError:
                    return {"raw": body}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            detail = raw
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    detail = str(parsed.get("detail") or parsed)
            except json.JSONDecodeError:
                pass
            raise APIError(exc.code, detail) from exc
        except urllib.error.URLError as exc:
            raise APIError(0, f"Error de red: {exc.reason}") from exc

    def _list_all(self, path: str, extra_params: Optional[Dict[str, object]] = None) -> List[Dict[str, object]]:
        skip = 0
        limit = 500
        all_items: List[Dict[str, object]] = []
        params = dict(extra_params or {})

        while True:
            page_params = dict(params)
            page_params.update({"skip": skip, "limit": limit})
            response = self._request("GET", path, params=page_params)
            if not isinstance(response, dict):
                break

            items = response.get("items", [])
            if not isinstance(items, list):
                break

            all_items.extend(items)
            if len(items) < limit:
                break
            skip += limit

        return all_items

    def map_clients_by_code(self) -> Dict[str, str]:
        items = self._list_all("/clients", extra_params={"active_only": False})
        return {
            str(item.get("code", "")).strip(): str(item.get("id"))
            for item in items
            if item.get("code") and item.get("id")
        }

    def map_products_by_code(self) -> Dict[str, str]:
        items = self._list_all("/products", extra_params={"active_only": False, "low_stock": False})
        return {
            str(item.get("code", "")).strip(): str(item.get("id"))
            for item in items
            if item.get("code") and item.get("id")
        }

    def map_suppliers_by_code(self) -> Dict[str, str]:
        items = self._list_all("/suppliers", extra_params={"active_only": False})
        return {
            str(item.get("code", "")).strip(): str(item.get("id"))
            for item in items
            if item.get("code") and item.get("id")
        }

    def map_workers_by_code(self) -> Dict[str, str]:
        items = self._list_all("/workers", extra_params={"active_only": False})
        return {
            str(item.get("code", "")).strip(): str(item.get("id"))
            for item in items
            if item.get("code") and item.get("id")
        }

    def create_client(self, payload: Dict[str, object]) -> Dict[str, object]:
        response = self._request("POST", "/clients", payload=payload)
        if not isinstance(response, dict):
            raise APIError(0, "Respuesta inesperada en create_client")
        return response

    def create_supplier(self, payload: Dict[str, object]) -> Dict[str, object]:
        response = self._request("POST", "/suppliers", payload=payload)
        if not isinstance(response, dict):
            raise APIError(0, "Respuesta inesperada en create_supplier")
        return response

    def create_product(self, payload: Dict[str, object]) -> Dict[str, object]:
        response = self._request("POST", "/products", payload=payload)
        if not isinstance(response, dict):
            raise APIError(0, "Respuesta inesperada en create_product")
        return response

    def create_worker(self, payload: Dict[str, object]) -> Dict[str, object]:
        response = self._request("POST", "/workers", payload=payload)
        if not isinstance(response, dict):
            raise APIError(0, "Respuesta inesperada en create_worker")
        return response

    def create_document(self, payload: Dict[str, object]) -> Dict[str, object]:
        response = self._request("POST", "/documents", payload=payload)
        if not isinstance(response, dict):
            raise APIError(0, "Respuesta inesperada en create_document")
        return response

    def create_diary_entry(self, payload: Dict[str, object]) -> Dict[str, object]:
        response = self._request("POST", "/diary", payload=payload)
        if not isinstance(response, dict):
            raise APIError(0, "Respuesta inesperada en create_diary_entry")
        return response

    def change_document_status(self, document_id: str, new_status: str) -> Dict[str, object]:
        response = self._request(
            "POST",
            f"/documents/{document_id}/change-status",
            payload={"new_status": new_status},
        )
        if not isinstance(response, dict):
            raise APIError(0, "Respuesta inesperada en change_document_status")
        return response


def _to_float(value: str, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip().replace(",", ".")
    if not text:
        return default
    return float(text)


def _to_int(value: str, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    return int(float(text))


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if not text:
        return default
    return text in {"1", "true", "yes", "si", "sí", "y"}


def _to_iso_datetime(value: str) -> Optional[str]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None

    candidates = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]

    try:
        return dt.datetime.fromisoformat(raw).isoformat()
    except ValueError:
        pass

    for fmt in candidates:
        try:
            parsed = dt.datetime.strptime(raw, fmt)
            return parsed.isoformat()
        except ValueError:
            continue

    raise MigrationError(f"Fecha invalida: {raw}")


def load_csv_rows(file_path: str) -> List[Dict[str, str]]:
    if not os.path.exists(file_path):
        raise MigrationError(f"No existe el archivo: {file_path}")

    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]

    return rows


def _header_errors(file_path: str, required_headers: List[str]) -> List[str]:
    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        actual = reader.fieldnames or []

    missing = [h for h in required_headers if h not in actual]
    if not missing:
        return []
    return [f"{os.path.basename(file_path)}: faltan columnas {missing}"]


def validate_data_dir(data_dir: str, wave: str) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    def path(name: str) -> str:
        return os.path.join(data_dir, name)

    def exists(name: str) -> bool:
        return os.path.exists(path(name))

    if wave in ("masters", "all"):
        errors.extend(_header_errors(path("clients.csv"), CLIENT_HEADERS))
        errors.extend(_header_errors(path("products.csv"), PRODUCT_HEADERS))
        errors.extend(_header_errors(path("suppliers.csv"), SUPPLIER_HEADERS))

        if exists("workers.csv"):
            worker_header_errors = _header_errors(path("workers.csv"), WORKER_HEADERS)
            errors.extend(worker_header_errors)
            if not worker_header_errors:
                worker_rows = load_csv_rows(path("workers.csv"))
                for idx, row in enumerate(worker_rows, start=2):
                    if not (row.get("code") or "").strip():
                        errors.append(f"workers.csv fila {idx}: code obligatorio")
                    if not (row.get("first_name") or "").strip():
                        errors.append(f"workers.csv fila {idx}: first_name obligatorio")
                    if not (row.get("last_name") or "").strip():
                        errors.append(f"workers.csv fila {idx}: last_name obligatorio")

                    hire_date = (row.get("hire_date") or "").strip()
                    if hire_date:
                        try:
                            _to_iso_datetime(hire_date)
                        except MigrationError as exc:
                            errors.append(f"workers.csv fila {idx}: {exc}")

                    salary = (row.get("salary") or "").strip()
                    if salary:
                        try:
                            _to_float(salary, 0.0)
                        except ValueError:
                            errors.append(f"workers.csv fila {idx}: salary invalido")
        else:
            warnings.append("workers.csv no encontrado; se omitira migracion de trabajadores")

    if wave in ("operations", "all"):
        operation_header_errors = []
        operation_header_errors.extend(_header_errors(path("documents.csv"), DOCUMENT_HEADERS))
        operation_header_errors.extend(_header_errors(path("document_lines.csv"), DOCUMENT_LINE_HEADERS))
        errors.extend(operation_header_errors)

        if not operation_header_errors:
            doc_rows = load_csv_rows(path("documents.csv"))
            line_rows = load_csv_rows(path("document_lines.csv"))

            refs = set()
            for idx, row in enumerate(doc_rows, start=2):
                ref = (row.get("document_ref") or "").strip()
                if not ref:
                    errors.append(f"documents.csv fila {idx}: document_ref obligatorio")
                    continue
                if ref in refs:
                    errors.append(f"documents.csv fila {idx}: document_ref duplicado '{ref}'")
                refs.add(ref)

                doc_type = (row.get("type") or "").strip()
                if doc_type not in ALLOWED_DOC_TYPES:
                    errors.append(f"documents.csv fila {idx}: type invalido '{doc_type}'")

                status = (row.get("status") or "draft").strip()
                if status and status not in ALLOWED_DOC_STATUS:
                    errors.append(f"documents.csv fila {idx}: status invalido '{status}'")

                if not (row.get("client_code") or "").strip():
                    errors.append(f"documents.csv fila {idx}: client_code obligatorio")

                try:
                    _to_iso_datetime(row.get("issue_date", ""))
                except MigrationError as exc:
                    errors.append(f"documents.csv fila {idx}: {exc}")

                due = (row.get("due_date") or "").strip()
                if due:
                    try:
                        _to_iso_datetime(due)
                    except MigrationError as exc:
                        errors.append(f"documents.csv fila {idx}: {exc}")

            for idx, row in enumerate(line_rows, start=2):
                ref = (row.get("document_ref") or "").strip()
                if not ref:
                    errors.append(f"document_lines.csv fila {idx}: document_ref obligatorio")
                    continue
                if ref not in refs:
                    errors.append(f"document_lines.csv fila {idx}: referencia '{ref}' no existe en documents.csv")

                if not (row.get("description") or "").strip():
                    errors.append(f"document_lines.csv fila {idx}: description obligatorio")

                line_type = (row.get("line_type") or "product").strip()
                if line_type not in ("product", "text"):
                    errors.append(f"document_lines.csv fila {idx}: line_type invalido '{line_type}'")

                try:
                    qty = _to_float(row.get("quantity", "1"), 1.0)
                    if qty <= 0:
                        errors.append(f"document_lines.csv fila {idx}: quantity debe ser > 0")
                except ValueError:
                    errors.append(f"document_lines.csv fila {idx}: quantity invalido")

                try:
                    unit_price = _to_float(row.get("unit_price", "0"), 0.0)
                    if unit_price < 0:
                        errors.append(f"document_lines.csv fila {idx}: unit_price debe ser >= 0")
                except ValueError:
                    errors.append(f"document_lines.csv fila {idx}: unit_price invalido")

                try:
                    discount = _to_float(row.get("discount_percent", "0"), 0.0)
                    if discount < 0 or discount > 100:
                        errors.append(f"document_lines.csv fila {idx}: discount_percent fuera de rango")
                except ValueError:
                    errors.append(f"document_lines.csv fila {idx}: discount_percent invalido")

            if not line_rows:
                warnings.append("document_lines.csv no tiene filas; se crearan documentos sin lineas")

    if wave in ("diary", "all"):
        if not exists("diary_entries.csv"):
            if wave == "diary":
                errors.append("No existe el archivo requerido: diary_entries.csv")
            else:
                warnings.append("diary_entries.csv no encontrado; se omitira oleada de diario")
        else:
            diary_header_errors = _header_errors(path("diary_entries.csv"), DIARY_HEADERS)
            errors.extend(diary_header_errors)
            if not diary_header_errors:
                diary_rows = load_csv_rows(path("diary_entries.csv"))
                for idx, row in enumerate(diary_rows, start=2):
                    if not (row.get("title") or "").strip():
                        errors.append(f"diary_entries.csv fila {idx}: title obligatorio")
                    if not (row.get("content") or "").strip():
                        errors.append(f"diary_entries.csv fila {idx}: content obligatorio")

                    entry_date = (row.get("entry_date") or "").strip()
                    if not entry_date:
                        errors.append(f"diary_entries.csv fila {idx}: entry_date obligatorio")
                    else:
                        try:
                            _to_iso_datetime(entry_date)
                        except MigrationError as exc:
                            errors.append(f"diary_entries.csv fila {idx}: {exc}")

    return errors, warnings


def build_client_payload(row: Dict[str, str]) -> Dict[str, object]:
    return {
        "code": (row.get("code") or "").strip(),
        "name": (row.get("name") or "").strip(),
        "tax_id": (row.get("tax_id") or "").strip() or None,
        "address": (row.get("address") or "").strip() or None,
        "city": (row.get("city") or "").strip() or None,
        "postal_code": (row.get("postal_code") or "").strip() or None,
        "province": (row.get("province") or "").strip() or None,
        "country": (row.get("country") or "").strip() or "Espana",
        "phone": (row.get("phone") or "").strip() or None,
        "email": (row.get("email") or "").strip() or None,
        "website": (row.get("website") or "").strip() or None,
        "notes": (row.get("notes") or "").strip() or None,
        "is_active": True,
    }


def build_supplier_payload(row: Dict[str, str]) -> Dict[str, object]:
    return {
        "code": (row.get("code") or "").strip(),
        "name": (row.get("name") or "").strip(),
        "tax_id": (row.get("tax_id") or "").strip() or None,
        "address": (row.get("address") or "").strip() or None,
        "city": (row.get("city") or "").strip() or None,
        "postal_code": (row.get("postal_code") or "").strip() or None,
        "province": (row.get("province") or "").strip() or None,
        "country": (row.get("country") or "").strip() or "Espana",
        "phone": (row.get("phone") or "").strip() or None,
        "email": (row.get("email") or "").strip() or None,
        "website": (row.get("website") or "").strip() or None,
        "notes": (row.get("notes") or "").strip() or None,
    }


def build_product_payload(row: Dict[str, str], supplier_code_to_id: Dict[str, str]) -> Dict[str, object]:
    supplier_code = (row.get("supplier_code") or "").strip()
    supplier_id = supplier_code_to_id.get(supplier_code) if supplier_code else None

    return {
        "code": (row.get("code") or "").strip(),
        "name": (row.get("name") or "").strip(),
        "description": (row.get("description") or "").strip() or None,
        "category": (row.get("category") or "").strip() or None,
        "purchase_price": _to_float(row.get("purchase_price", "0"), 0.0),
        "sale_price": _to_float(row.get("sale_price", "0"), 0.0),
        "current_stock": _to_int(row.get("current_stock", "0"), 0),
        "minimum_stock": _to_int(row.get("minimum_stock", "0"), 0),
        "stock_unit": (row.get("stock_unit") or "").strip() or "unidades",
        "supplier_id": supplier_id,
    }


def build_worker_payload(row: Dict[str, str]) -> Dict[str, object]:
    hire_date = _to_iso_datetime(row.get("hire_date", ""))
    salary_raw = (row.get("salary") or "").strip()

    payload: Dict[str, object] = {
        "code": (row.get("code") or "").strip(),
        "first_name": (row.get("first_name") or "").strip(),
        "last_name": (row.get("last_name") or "").strip(),
        "phone": (row.get("phone") or "").strip() or None,
        "email": (row.get("email") or "").strip() or None,
        "address": (row.get("address") or "").strip() or None,
        "position": (row.get("position") or "").strip() or None,
        "department": (row.get("department") or "").strip() or None,
    }

    if hire_date:
        payload["hire_date"] = hire_date
    if salary_raw:
        payload["salary"] = _to_float(salary_raw, 0.0)

    return payload


def build_diary_payload(row: Dict[str, str]) -> Dict[str, object]:
    entry_date = _to_iso_datetime(row.get("entry_date", ""))
    if not entry_date:
        raise MigrationError("entry_date obligatorio")

    return {
        "title": (row.get("title") or "").strip(),
        "content": (row.get("content") or "").strip(),
        "entry_date": entry_date,
        "tags": (row.get("tags") or "").strip() or None,
        "is_pinned": _to_bool(row.get("is_pinned", ""), default=False),
    }


def _group_lines_by_ref(line_rows: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for row in line_rows:
        ref = (row.get("document_ref") or "").strip()
        grouped.setdefault(ref, []).append(row)
    return grouped


def _build_document_payload(
    doc_row: Dict[str, str],
    line_rows: List[Dict[str, str]],
    client_map: Dict[str, str],
    product_map: Dict[str, str],
) -> Dict[str, object]:
    client_code = (doc_row.get("client_code") or "").strip()
    client_id = client_map.get(client_code)
    if not client_id:
        raise MigrationError(f"Cliente no encontrado para code='{client_code}'")

    lines_payload: List[Dict[str, object]] = []
    for line in line_rows:
        product_code = (line.get("product_code") or "").strip()
        product_id = product_map.get(product_code) if product_code else None
        line_type = (line.get("line_type") or "product").strip() or "product"
        if line_type == "product" and product_code and not product_id:
            raise MigrationError(f"Producto no encontrado para code='{product_code}'")

        lines_payload.append(
            {
                "line_type": line_type,
                "product_id": product_id,
                "description": (line.get("description") or "").strip(),
                "quantity": _to_float(line.get("quantity", "1"), 1.0),
                "unit_price": _to_float(line.get("unit_price", "0"), 0.0),
                "discount_percent": _to_float(line.get("discount_percent", "0"), 0.0),
            }
        )

    payload: Dict[str, object] = {
        "type": (doc_row.get("type") or "").strip(),
        "client_id": client_id,
        "issue_date": _to_iso_datetime(doc_row.get("issue_date", "")),
        "lines": lines_payload,
    }

    due_date = _to_iso_datetime(doc_row.get("due_date", ""))
    if due_date:
        payload["due_date"] = due_date

    for text_key in ("notes", "internal_notes", "terms"):
        value = (doc_row.get(text_key) or "").strip()
        if value:
            payload[text_key] = value

    return payload


def _apply_document_status(api: DragofactuAPI, document_id: str, target_status: str, dry_run: bool):
    status = (target_status or "draft").strip() or "draft"
    path = STATUS_PATHS.get(status)
    if path is None:
        raise MigrationError(f"Estado no soportado: {status}")

    if dry_run:
        return

    for step in path:
        api.change_document_status(document_id, step)


def run_wave_masters(
    data_dir: str,
    api: Optional[DragofactuAPI],
    dry_run: bool,
    verbose: bool,
) -> Tuple[Stats, Stats, Stats, Stats]:
    suppliers_stats = Stats()
    clients_stats = Stats()
    products_stats = Stats()
    workers_stats = Stats()

    suppliers = load_csv_rows(os.path.join(data_dir, "suppliers.csv"))
    clients = load_csv_rows(os.path.join(data_dir, "clients.csv"))
    products = load_csv_rows(os.path.join(data_dir, "products.csv"))
    workers_path = os.path.join(data_dir, "workers.csv")
    workers = load_csv_rows(workers_path) if os.path.exists(workers_path) else []

    supplier_code_to_id: Dict[str, str] = {}
    client_code_to_id: Dict[str, str] = {}
    product_code_to_id: Dict[str, str] = {}
    worker_code_to_id: Dict[str, str] = {}

    if api is not None:
        supplier_code_to_id = api.map_suppliers_by_code()
        client_code_to_id = api.map_clients_by_code()
        product_code_to_id = api.map_products_by_code()
        worker_code_to_id = api.map_workers_by_code()

    for row in suppliers:
        code = (row.get("code") or "").strip()
        name = (row.get("name") or "").strip()
        if not code or not name:
            suppliers_stats.errors += 1
            continue
        if code in supplier_code_to_id:
            suppliers_stats.skipped += 1
            continue

        payload = build_supplier_payload(row)
        if dry_run or api is None:
            suppliers_stats.created += 1
            continue

        try:
            created = api.create_supplier(payload)
            supplier_id = str(created.get("id", ""))
            if supplier_id:
                supplier_code_to_id[code] = supplier_id
            suppliers_stats.created += 1
        except APIError as exc:
            suppliers_stats.errors += 1
            if verbose:
                print(f"[ERROR][suppliers:{code}] {exc}")

    for row in clients:
        code = (row.get("code") or "").strip()
        name = (row.get("name") or "").strip()
        if not code or not name:
            clients_stats.errors += 1
            continue
        if code in client_code_to_id:
            clients_stats.skipped += 1
            continue

        payload = build_client_payload(row)
        if dry_run or api is None:
            clients_stats.created += 1
            continue

        try:
            created = api.create_client(payload)
            client_id = str(created.get("id", ""))
            if client_id:
                client_code_to_id[code] = client_id
            clients_stats.created += 1
        except APIError as exc:
            clients_stats.errors += 1
            if verbose:
                print(f"[ERROR][clients:{code}] {exc}")

    for row in products:
        code = (row.get("code") or "").strip()
        name = (row.get("name") or "").strip()
        if not code or not name:
            products_stats.errors += 1
            continue
        if code in product_code_to_id:
            products_stats.skipped += 1
            continue

        try:
            payload = build_product_payload(row, supplier_code_to_id)
        except (ValueError, MigrationError) as exc:
            products_stats.errors += 1
            if verbose:
                print(f"[ERROR][products:{code}] {exc}")
            continue

        if dry_run or api is None:
            products_stats.created += 1
            continue

        try:
            created = api.create_product(payload)
            product_id = str(created.get("id", ""))
            if product_id:
                product_code_to_id[code] = product_id
            products_stats.created += 1
        except APIError as exc:
            products_stats.errors += 1
            if verbose:
                print(f"[ERROR][products:{code}] {exc}")

    for row in workers:
        code = (row.get("code") or "").strip()
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()
        if not code or not first_name or not last_name:
            workers_stats.errors += 1
            continue
        if code in worker_code_to_id:
            workers_stats.skipped += 1
            continue

        try:
            payload = build_worker_payload(row)
        except (ValueError, MigrationError) as exc:
            workers_stats.errors += 1
            if verbose:
                print(f"[ERROR][workers:{code}] {exc}")
            continue

        if dry_run or api is None:
            workers_stats.created += 1
            continue

        try:
            created = api.create_worker(payload)
            worker_id = str(created.get("id", ""))
            if worker_id:
                worker_code_to_id[code] = worker_id
            workers_stats.created += 1
        except APIError as exc:
            workers_stats.errors += 1
            if verbose:
                print(f"[ERROR][workers:{code}] {exc}")

    return suppliers_stats, clients_stats, products_stats, workers_stats


def run_wave_operations(
    data_dir: str,
    api: Optional[DragofactuAPI],
    dry_run: bool,
    verbose: bool,
) -> Stats:
    stats = Stats()

    docs = load_csv_rows(os.path.join(data_dir, "documents.csv"))
    lines = load_csv_rows(os.path.join(data_dir, "document_lines.csv"))
    lines_by_ref = _group_lines_by_ref(lines)

    client_map: Dict[str, str] = {}
    product_map: Dict[str, str] = {}

    if api is not None:
        client_map = api.map_clients_by_code()
        product_map = api.map_products_by_code()

    # Offline dry-run: validate operations payload shape without resolving remote IDs.
    if api is None:
        for row in docs:
            ref = (row.get("document_ref") or "").strip() or "<sin-ref>"
            try:
                doc_type = (row.get("type") or "").strip()
                if doc_type not in ALLOWED_DOC_TYPES:
                    raise MigrationError(f"Tipo de documento invalido: {doc_type}")

                client_code = (row.get("client_code") or "").strip()
                if not client_code:
                    raise MigrationError("client_code obligatorio")

                _to_iso_datetime(row.get("issue_date", ""))
                due_value = (row.get("due_date") or "").strip()
                if due_value:
                    _to_iso_datetime(due_value)

                if (row.get("status") or "draft").strip() not in ALLOWED_DOC_STATUS:
                    raise MigrationError("status no soportado")

                for line in lines_by_ref.get(ref, []):
                    if not (line.get("description") or "").strip():
                        raise MigrationError("linea sin description")
                    qty = _to_float(line.get("quantity", "1"), 1.0)
                    if qty <= 0:
                        raise MigrationError("quantity debe ser > 0")
                    unit_price = _to_float(line.get("unit_price", "0"), 0.0)
                    if unit_price < 0:
                        raise MigrationError("unit_price debe ser >= 0")
                    discount = _to_float(line.get("discount_percent", "0"), 0.0)
                    if discount < 0 or discount > 100:
                        raise MigrationError("discount_percent fuera de rango")

                stats.created += 1
            except (MigrationError, ValueError) as exc:
                stats.errors += 1
                if verbose:
                    print(f"[ERROR][documents:{ref}] {exc}")

        return stats

    for row in docs:
        ref = (row.get("document_ref") or "").strip() or "<sin-ref>"
        try:
            payload = _build_document_payload(
                row,
                lines_by_ref.get(ref, []),
                client_map,
                product_map,
            )
        except (MigrationError, ValueError) as exc:
            stats.errors += 1
            if verbose:
                print(f"[ERROR][documents:{ref}] {exc}")
            continue

        target_status = (row.get("status") or "draft").strip() or "draft"

        if dry_run:
            stats.created += 1
            continue

        try:
            created = api.create_document(payload)
            document_id = str(created.get("id", ""))
            if not document_id:
                raise MigrationError("No se pudo obtener id del documento creado")
            _apply_document_status(api, document_id, target_status, dry_run=False)
            stats.created += 1
        except (APIError, MigrationError) as exc:
            stats.errors += 1
            if verbose:
                print(f"[ERROR][documents:{ref}] {exc}")

    return stats


def run_wave_diary(
    data_dir: str,
    api: Optional[DragofactuAPI],
    dry_run: bool,
    verbose: bool,
) -> Stats:
    stats = Stats()

    diary_path = os.path.join(data_dir, "diary_entries.csv")
    if not os.path.exists(diary_path):
        return stats

    rows = load_csv_rows(diary_path)

    for row in rows:
        title = (row.get("title") or "").strip() or "<sin-title>"
        try:
            payload = build_diary_payload(row)
        except (MigrationError, ValueError) as exc:
            stats.errors += 1
            if verbose:
                print(f"[ERROR][diary:{title}] {exc}")
            continue

        if dry_run or api is None:
            stats.created += 1
            continue

        try:
            api.create_diary_entry(payload)
            stats.created += 1
        except APIError as exc:
            stats.errors += 1
            if verbose:
                print(f"[ERROR][diary:{title}] {exc}")

    return stats


def print_stats(title: str, stats: Stats):
    print(
        f"{title}: created={stats.created}, skipped={stats.skipped}, errors={stats.errors}"
    )


def command_validate(args: argparse.Namespace) -> int:
    errors, warnings = validate_data_dir(args.data_dir, args.wave)

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"- {w}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("Validacion OK")
    return 0


def command_run(args: argparse.Namespace) -> int:
    errors, warnings = validate_data_dir(args.data_dir, args.wave)

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"- {w}")

    if errors and not args.ignore_validation_errors:
        print("\nErrores de validacion (bloqueante):")
        for e in errors:
            print(f"- {e}")
        return 1

    if errors and args.ignore_validation_errors:
        print("\nErrores de validacion (continuando por --ignore-validation-errors):")
        for e in errors:
            print(f"- {e}")

    api: Optional[DragofactuAPI] = None
    if args.token:
        api = DragofactuAPI(args.base_url, args.token, timeout=args.timeout)
    elif not args.dry_run:
        print("ERROR: --token es obligatorio cuando no hay --dry-run")
        return 1

    if args.dry_run and api is None:
        print("Dry-run offline: no se consultaran duplicados remotos")

    if args.wave in ("masters", "all"):
        s_stats, c_stats, p_stats, w_stats = run_wave_masters(
            args.data_dir,
            api=api,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
        print_stats("Suppliers", s_stats)
        print_stats("Clients", c_stats)
        print_stats("Products", p_stats)
        print_stats("Workers", w_stats)

    if args.wave in ("operations", "all"):
        op_stats = run_wave_operations(
            args.data_dir,
            api=api,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
        print_stats("Documents", op_stats)

    if args.wave in ("diary", "all"):
        diary_stats = run_wave_diary(
            args.data_dir,
            api=api,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
        print_stats("Diary", diary_stats)

    print("\nRun finalizado")
    return 0


def command_templates(args: argparse.Namespace) -> int:
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    templates = {
        "clients.csv": [
            CLIENT_HEADERS,
            [
                "C-0001",
                "Cliente Ejemplo",
                "B12345678",
                "Calle Ejemplo 1",
                "Palma",
                "07001",
                "Baleares",
                "Espana",
                "600000000",
                "cliente@example.com",
                "",
                "",
            ],
        ],
        "products.csv": [
            PRODUCT_HEADERS,
            [
                "P-0001",
                "Producto Ejemplo",
                "Descripcion ejemplo",
                "General",
                "10.0",
                "15.0",
                "100",
                "10",
                "unidades",
                "",
            ],
        ],
        "suppliers.csv": [
            SUPPLIER_HEADERS,
            [
                "S-0001",
                "Proveedor Ejemplo",
                "B87654321",
                "Calle Proveedor 1",
                "Palma",
                "07001",
                "Baleares",
                "Espana",
                "600000001",
                "proveedor@example.com",
                "",
                "",
            ],
        ],
        "workers.csv": [
            WORKER_HEADERS,
            [
                "W-0001",
                "Ana",
                "Garcia",
                "600000123",
                "ana.worker@example.com",
                "Calle Trabajo 10",
                "Operaria",
                "Produccion",
                "2026-01-10",
                "22000",
            ],
        ],
        "documents.csv": [
            DOCUMENT_HEADERS,
            [
                "DOC-REF-0001",
                "quote",
                "C-0001",
                "2026-04-10",
                "2026-04-30",
                "Notas documento",
                "",
                "",
                "draft",
            ],
        ],
        "document_lines.csv": [
            DOCUMENT_LINE_HEADERS,
            [
                "DOC-REF-0001",
                "product",
                "P-0001",
                "Linea de ejemplo",
                "2",
                "15.0",
                "0",
            ],
        ],
        "diary_entries.csv": [
            DIARY_HEADERS,
            [
                "Parte diario ejemplo",
                "Inicio de jornada y tareas ejecutadas",
                "2026-04-10T09:00:00",
                "obra-a,seguimiento",
                "false",
            ],
        ],
    }

    for filename, rows in templates.items():
        file_path = os.path.join(out_dir, filename)
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    print(f"Plantillas generadas en: {out_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dragofactu migration runner (wave-based)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Validate CSV files for selected wave")
    p_validate.add_argument("--data-dir", required=True, help="Directory with CSV files")
    p_validate.add_argument(
        "--wave",
        default="all",
        choices=["masters", "operations", "diary", "all"],
        help="Validation scope",
    )
    p_validate.set_defaults(func=command_validate)

    p_run = sub.add_parser("run", help="Execute migration wave(s)")
    p_run.add_argument("--data-dir", required=True, help="Directory with CSV files")
    p_run.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    p_run.add_argument("--token", default="", help="JWT access token")
    p_run.add_argument(
        "--wave",
        default="all",
        choices=["masters", "operations", "diary", "all"],
        help="Execution scope",
    )
    p_run.add_argument("--dry-run", action="store_true", help="Validate and simulate without writes")
    p_run.add_argument(
        "--ignore-validation-errors",
        action="store_true",
        help="Continue even with validation errors",
    )
    p_run.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    p_run.add_argument("--verbose", action="store_true", help="Verbose error output")
    p_run.set_defaults(func=command_run)

    p_tpl = sub.add_parser("templates", help="Generate CSV templates")
    p_tpl.add_argument("--out-dir", required=True, help="Destination folder for templates")
    p_tpl.set_defaults(func=command_templates)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("Interrumpido por el usuario")
        return 130
    except MigrationError as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
