#!/usr/bin/env python3
"""
Script no interactivo para crear superadmin en producción via railway run.

Uso:
    cd ~/Dragofactu
    railway run python3 scripts/create_superadmin_noninteractive.py

No requiere virtualenv activado. Usa DATABASE_URL que railway run inyecta.
"""
import os
import sys
import uuid
import hashlib

# --- Obtain DATABASE_URL ---
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL no está definida.")
    print("Asegúrate de correr: railway run python3 scripts/create_superadmin_noninteractive.py")
    sys.exit(1)

# railway uses postgres:// but psycopg2 needs postgresql://
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# --- Config ---
USERNAME = os.getenv("SA_USERNAME", "jaime")
EMAIL    = os.getenv("SA_EMAIL",    "jaime@dragofactu.local")
PASSWORD = os.getenv("SA_PASSWORD", "Drago2026!SA")
FULLNAME = os.getenv("SA_FULLNAME", "Jaime Superadmin")

try:
    import bcrypt
    pwd_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=12)).decode()
except ImportError:
    # fallback: sha256 (only for bootstrap, not production-grade)
    pwd_hash = "sha256:" + hashlib.sha256(PASSWORD.encode()).hexdigest()
    print("WARNING: bcrypt no disponible, usando sha256. Instala bcrypt: pip install bcrypt")

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 no disponible.")
    print("Instala con: pip install psycopg2-binary")
    sys.exit(1)

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = False
cur = conn.cursor()

try:
    # Find first active company
    cur.execute("SELECT id, code, name FROM companies WHERE is_active = TRUE ORDER BY created_at LIMIT 1")
    row = cur.fetchone()
    if not row:
        print("ERROR: No hay empresas en la base de datos.")
        print("Registra una empresa primero desde la web app.")
        sys.exit(1)

    company_id, company_code, company_name = row
    print(f"Empresa: {company_name} ({company_code})")

    # Check if user already exists (anywhere)
    cur.execute("SELECT id, company_id, username, is_superadmin FROM users WHERE username = %s", (USERNAME,))
    existing = cur.fetchone()

    if existing:
        user_id, user_company_id, user_username, is_sa = existing
        cur.execute(
            "UPDATE users SET is_superadmin = TRUE, role = 'ADMIN', password_hash = %s WHERE id = %s",
            (pwd_hash, user_id)
        )
        conn.commit()
        print(f"OK: Usuario '{USERNAME}' promovido a superadmin y contraseña actualizada.")
    else:
        new_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO users (id, company_id, username, email, password_hash, full_name,
               role, is_active, is_superadmin, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, 'ADMIN', TRUE, TRUE, NOW(), NOW())""",
            (new_id, str(company_id), USERNAME, EMAIL, pwd_hash, FULLNAME)
        )
        conn.commit()
        print(f"OK: Superadmin '{USERNAME}' creado en empresa '{company_name}'.")

    print(f"\nCredenciales de produccion:")
    print(f"  Usuario:   {USERNAME}")
    print(f"  Password:  {PASSWORD}")
    print(f"  URL:       https://dragofactu-production.up.railway.app")

except Exception as e:
    conn.rollback()
    print(f"ERROR: {e}")
    sys.exit(1)
finally:
    cur.close()
    conn.close()
