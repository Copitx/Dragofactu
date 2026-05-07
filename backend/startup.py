#!/usr/bin/env python3
"""
Startup script: apply schema changes via raw SQL, then exec uvicorn.
No alembic dependency — works regardless of alembic_version state.
"""
import os
import sys


DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

PORT = os.environ.get("PORT", "8000")


def col_exists(cur, table, col):
    cur.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name=%s AND column_name=%s",
        (table, col)
    )
    return cur.fetchone() is not None


def table_exists(cur, table):
    cur.execute(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_name=%s AND table_schema='public'",
        (table,)
    )
    return cur.fetchone() is not None


def run(cur, sql, label):
    cur.execute(sql)
    print(f"  [OK] {label}")


def apply_schema(conn):
    cur = conn.cursor()

    # ── companies: smtp fields ──────────────────────────────────────────────
    for col, ddl in [
        ("smtp_host",               "VARCHAR(200)"),
        ("smtp_port",               "INTEGER DEFAULT 587"),
        ("smtp_user",               "VARCHAR(200)"),
        ("smtp_password_encrypted", "TEXT"),
        ("smtp_use_tls",            "BOOLEAN DEFAULT TRUE"),
        ("smtp_from_email",         "VARCHAR(200)"),
        ("smtp_from_name",          "VARCHAR(200)"),
        ("email_subject_template",  "VARCHAR(300)"),
        ("email_body_template",     "TEXT"),
        ("trade_name",              "VARCHAR(200)"),
        ("pdf_footer_text",         "TEXT"),
    ]:
        if not col_exists(cur, "companies", col):
            run(cur, f'ALTER TABLE companies ADD COLUMN "{col}" {ddl}', f"companies.{col}")

    # ── users: is_superadmin ────────────────────────────────────────────────
    if not col_exists(cur, "users", "is_superadmin"):
        run(cur, "ALTER TABLE users ADD COLUMN is_superadmin BOOLEAN NOT NULL DEFAULT FALSE",
            "users.is_superadmin")

    # ── clients: business fields ────────────────────────────────────────────
    for col, ddl in [
        ("payment_method",   "VARCHAR(50)"),
        ("payment_days",     "INTEGER DEFAULT 30"),
        ("contact_person",   "VARCHAR(100)"),
        ("bank_iban",        "TEXT"),
        ("default_discount", "FLOAT DEFAULT 0.0"),
        ("notes_internal",   "TEXT"),
    ]:
        if not col_exists(cur, "clients", col):
            run(cur, f'ALTER TABLE clients ADD COLUMN "{col}" {ddl}', f"clients.{col}")

    # ── documents: business fields ──────────────────────────────────────────
    for col, ddl in [
        ("client_reference",   "VARCHAR(100)"),
        ("payment_method",     "VARCHAR(50)"),
        ("execution_location", "VARCHAR(200)"),
        ("payment_date",       "DATE"),
    ]:
        if not col_exists(cur, "documents", col):
            run(cur, f'ALTER TABLE documents ADD COLUMN "{col}" {ddl}', f"documents.{col}")

    # ── document_lines: measurements ────────────────────────────────────────
    if not col_exists(cur, "document_lines", "measurements"):
        run(cur, "ALTER TABLE document_lines ADD COLUMN measurements VARCHAR(200)",
            "document_lines.measurements")

    # ── supplier_catalog table ──────────────────────────────────────────────
    if not table_exists(cur, "supplier_catalog"):
        run(cur, """
            CREATE TABLE supplier_catalog (
                id VARCHAR(36) PRIMARY KEY,
                company_id VARCHAR(36) NOT NULL REFERENCES companies(id),
                supplier_id VARCHAR(36) NOT NULL REFERENCES suppliers(id),
                product_id VARCHAR(36) NOT NULL REFERENCES products(id),
                supplier_ref VARCHAR(50),
                purchase_price FLOAT,
                lead_time_days INTEGER,
                min_order_qty FLOAT,
                notes TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE,
                CONSTRAINT uq_supplier_catalog_entry UNIQUE (company_id, supplier_id, product_id)
            )
        """, "table supplier_catalog")
        cur.execute("CREATE INDEX ix_supplier_catalog_company_id ON supplier_catalog(company_id)")
        cur.execute("CREATE INDEX ix_supplier_catalog_supplier_id ON supplier_catalog(supplier_id)")
        cur.execute("CREATE INDEX ix_supplier_catalog_product_id ON supplier_catalog(product_id)")

    # ── projects table ──────────────────────────────────────────────────────
    if not table_exists(cur, "projects"):
        run(cur, """
            CREATE TABLE projects (
                id VARCHAR(36) PRIMARY KEY,
                company_id VARCHAR(36) NOT NULL REFERENCES companies(id),
                code VARCHAR(20) NOT NULL,
                name VARCHAR(200) NOT NULL,
                client_id VARCHAR(36) REFERENCES clients(id),
                address VARCHAR(300),
                status VARCHAR(20),
                start_date DATE,
                end_date DATE,
                estimated_value FLOAT,
                notes TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_by VARCHAR(36) NOT NULL REFERENCES users(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE,
                CONSTRAINT uq_project_company_code UNIQUE (company_id, code)
            )
        """, "table projects")
        cur.execute("CREATE INDEX ix_projects_company_id ON projects(company_id)")
        cur.execute("CREATE INDEX ix_projects_client_id ON projects(client_id)")
        cur.execute("CREATE INDEX ix_projects_code ON projects(code)")

    # ── project_expenses table ──────────────────────────────────────────────
    if not table_exists(cur, "project_expenses"):
        run(cur, """
            CREATE TABLE project_expenses (
                id VARCHAR(36) PRIMARY KEY,
                project_id VARCHAR(36) NOT NULL REFERENCES projects(id),
                company_id VARCHAR(36) NOT NULL REFERENCES companies(id),
                date DATE NOT NULL,
                description VARCHAR(300) NOT NULL,
                supplier VARCHAR(150),
                document_ref VARCHAR(50),
                amount FLOAT NOT NULL,
                category VARCHAR(20),
                worker_id VARCHAR(36) REFERENCES workers(id),
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """, "table project_expenses")
        cur.execute("CREATE INDEX ix_project_expenses_project_id ON project_expenses(project_id)")

    # ── project_documents table ─────────────────────────────────────────────
    if not table_exists(cur, "project_documents"):
        run(cur, """
            CREATE TABLE project_documents (
                id VARCHAR(36) PRIMARY KEY,
                project_id VARCHAR(36) NOT NULL REFERENCES projects(id),
                document_id VARCHAR(36) NOT NULL REFERENCES documents(id),
                company_id VARCHAR(36) NOT NULL REFERENCES companies(id),
                linked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                CONSTRAINT uq_project_document UNIQUE (project_id, document_id)
            )
        """, "table project_documents")

    # ── password_reset_tokens table ─────────────────────────────────────────
    if not table_exists(cur, "password_reset_tokens"):
        run(cur, """
            CREATE TABLE password_reset_tokens (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL REFERENCES users(id),
                token_hash VARCHAR(64) NOT NULL UNIQUE,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                used_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """, "table password_reset_tokens")
        cur.execute(
            "CREATE INDEX ix_password_reset_tokens_user_id ON password_reset_tokens(user_id)"
        )
        cur.execute(
            "CREATE INDEX ix_password_reset_tokens_token_hash ON password_reset_tokens(token_hash)"
        )

    conn.commit()
    cur.close()


# ── Main ─────────────────────────────────────────────────────────────────────
if DATABASE_URL:
    print("[startup] PostgreSQL detected — applying schema migrations...")
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        apply_schema(conn)
        conn.close()
        print("[startup] Schema up to date.")
    except Exception as exc:
        print(f"[startup] ERROR during schema migration: {exc}", file=sys.stderr)
        # Still start uvicorn so healthcheck responds — but log the error
else:
    print("[startup] No DATABASE_URL — using SQLite (local dev), skipping migrations.")

print(f"[startup] Starting uvicorn on :{PORT}")
os.execvp("uvicorn", [
    "uvicorn", "app.main:app",
    "--host", "0.0.0.0",
    "--port", PORT,
])
