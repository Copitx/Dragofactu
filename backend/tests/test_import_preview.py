"""
Tests for import preview endpoint and xlsx support.
"""
import io
import csv
import pytest
from fastapi.testclient import TestClient


def _csv_bytes(rows: list[dict], fieldnames: list[str]) -> bytes:
    """Build an in-memory CSV bytes object."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _xlsx_bytes(rows: list[dict], fieldnames: list[str]) -> bytes:
    """Build an in-memory XLSX bytes object using openpyxl."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(fieldnames)
    for row in rows:
        ws.append([row.get(f, "") for f in fieldnames])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


CLIENT_FIELDS = ["code", "name", "tax_id", "email"]


class TestImportPreview:
    def test_preview_csv_clients(self, client: TestClient, auth_headers: dict):
        rows = [
            {"code": "CLI001", "name": "Cliente A", "tax_id": "A1234567B", "email": "a@a.com"},
            {"code": "CLI002", "name": "Cliente B", "tax_id": "", "email": ""},
        ]
        csv_data = _csv_bytes(rows, CLIENT_FIELDS)
        response = client.post(
            "/api/v1/export/import/preview",
            data={"entity_type": "clients"},
            files={"file": ("clients.csv", csv_data, "text/csv")},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 2
        assert data["valid_rows"] == 2
        assert data["error_rows"] == 0
        assert len(data["sample"]) == 2
        assert len(data["sample"][0]) <= 20  # headers capped

    def test_preview_csv_missing_required_field(self, client: TestClient, auth_headers: dict):
        rows = [
            {"code": "CLI001", "name": "", "tax_id": "", "email": ""},  # name missing
        ]
        csv_data = _csv_bytes(rows, CLIENT_FIELDS)
        response = client.post(
            "/api/v1/export/import/preview",
            data={"entity_type": "clients"},
            files={"file": ("clients.csv", csv_data, "text/csv")},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 1
        assert data["error_rows"] == 1
        assert data["valid_rows"] == 0
        assert len(data["errors"]) >= 1

    def test_preview_xlsx_clients(self, client: TestClient, auth_headers: dict):
        rows = [
            {"code": "CLI001", "name": "Cliente XLSX", "tax_id": "B9876543A", "email": "x@x.com"},
        ]
        xlsx_data = _xlsx_bytes(rows, CLIENT_FIELDS)
        response = client.post(
            "/api/v1/export/import/preview",
            data={"entity_type": "clients"},
            files={"file": ("clients.xlsx", xlsx_data,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 1
        assert data["valid_rows"] == 1
        assert len(data["sample"]) == 1
        assert data["sample"][0]["name"] == "Cliente XLSX"

    def test_preview_invalid_entity_type(self, client: TestClient, auth_headers: dict):
        csv_data = b"code,name\n1,Test"
        response = client.post(
            "/api/v1/export/import/preview",
            data={"entity_type": "invalid_entity"},
            files={"file": ("test.csv", csv_data, "text/csv")},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_preview_sample_capped_at_5(self, client: TestClient, auth_headers: dict):
        rows = [{"code": f"CLI{i:03d}", "name": f"Cliente {i}"} for i in range(10)]
        csv_data = _csv_bytes(rows, ["code", "name"])
        response = client.post(
            "/api/v1/export/import/preview",
            data={"entity_type": "clients"},
            files={"file": ("clients.csv", csv_data, "text/csv")},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 10
        assert len(data["sample"]) == 5  # capped at PREVIEW_SAMPLE_ROWS

    def test_preview_products(self, client: TestClient, auth_headers: dict):
        rows = [{"code": "PROD001", "name": "Producto Test"}]
        csv_data = _csv_bytes(rows, ["code", "name"])
        response = client.post(
            "/api/v1/export/import/preview",
            data={"entity_type": "products"},
            files={"file": ("products.csv", csv_data, "text/csv")},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["valid_rows"] == 1

    def test_preview_requires_auth(self, client: TestClient):
        csv_data = b"code,name\nC1,Test"
        response = client.post(
            "/api/v1/export/import/preview",
            data={"entity_type": "clients"},
            files={"file": ("clients.csv", csv_data, "text/csv")},
        )
        assert response.status_code == 401


class TestXlsxImport:
    def test_import_clients_xlsx(self, client: TestClient, auth_headers: dict):
        rows = [
            {"code": "XLSCLI001", "name": "Cliente Excel", "tax_id": "A1111111B",
             "address": "", "city": "", "postal_code": "", "province": "",
             "country": "ES", "phone": "", "email": "excel@test.com", "website": "", "notes": ""},
        ]
        xlsx_data = _xlsx_bytes(
            rows,
            ["code", "name", "tax_id", "address", "city", "postal_code",
             "province", "country", "phone", "email", "website", "notes"]
        )
        response = client.post(
            "/api/v1/export/import/clients",
            files={"file": ("clients.xlsx", xlsx_data,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "Importados: 1" in response.json()["message"]
