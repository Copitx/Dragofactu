#!/usr/bin/env python3
"""
Script no interactivo para crear superadmin en producción via railway run.

Uso:
    railway run python3 scripts/create_superadmin_noninteractive.py

Variables de entorno (opcionales — si no se definen usa los valores hardcoded abajo):
    SA_USERNAME   SA_EMAIL   SA_PASSWORD   SA_FULLNAME
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models import User, Company, UserRole
from app.core.security import hash_password

USERNAME  = os.getenv("SA_USERNAME",  "jaime")
EMAIL     = os.getenv("SA_EMAIL",     "jaime@dragofactu.local")
PASSWORD  = os.getenv("SA_PASSWORD",  "Drago2026!SA")
FULLNAME  = os.getenv("SA_FULLNAME",  "Jaime Superadmin")

db = SessionLocal()
try:
    # Find first active company
    company = db.query(Company).filter(Company.is_active == True).order_by(Company.created_at).first()
    if not company:
        print("ERROR: No hay empresas en la base de datos. Registra una empresa primero.")
        sys.exit(1)

    print(f"Empresa encontrada: {company.name} ({company.code})")

    # Check if user already exists
    existing = db.query(User).filter(
        User.company_id == company.id,
        User.username == USERNAME
    ).first()

    if existing:
        # Promote to superadmin
        existing.is_superadmin = True
        existing.role = UserRole.ADMIN
        existing.password_hash = hash_password(PASSWORD)
        db.commit()
        print(f"OK: Usuario '{USERNAME}' promovido a superadmin y contraseña actualizada.")
    else:
        # Check username across all companies
        any_existing = db.query(User).filter(User.username == USERNAME).first()
        if any_existing:
            # Promote that user
            any_existing.is_superadmin = True
            any_existing.role = UserRole.ADMIN
            any_existing.password_hash = hash_password(PASSWORD)
            db.commit()
            print(f"OK: Usuario '{USERNAME}' (empresa: {any_existing.company_id}) promovido a superadmin.")
        else:
            new_user = User(
                id=uuid.uuid4(),
                company_id=company.id,
                username=USERNAME,
                email=EMAIL,
                password_hash=hash_password(PASSWORD),
                full_name=FULLNAME,
                role=UserRole.ADMIN,
                is_active=True,
                is_superadmin=True,
            )
            db.add(new_user)
            db.commit()
            print(f"OK: Superadmin '{USERNAME}' creado en empresa '{company.name}'.")

    print(f"\nCredenciales de produccion:")
    print(f"  Usuario:   {USERNAME}")
    print(f"  Password:  {PASSWORD}")
    print(f"  URL:       https://dragofactu-production.up.railway.app")

finally:
    db.close()
