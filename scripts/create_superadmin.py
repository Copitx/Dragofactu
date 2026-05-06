#!/usr/bin/env python3
"""
Script para crear o promover un superadmin de plataforma.

IMPORTANTE: Este es el ÚNICO mecanismo para activar is_superadmin=True.
Nunca se puede hacer via API. Ejecutar solo en servidor con acceso directo a BD.

Uso:
    cd backend
    source venv/bin/activate
    python ../scripts/create_superadmin.py

Variables de entorno:
    SUPERADMIN_USERNAME  - Username del superadmin (default: pide por input)
    SUPERADMIN_EMAIL     - Email del superadmin
    SUPERADMIN_PASSWORD  - Password (min 12 chars para superadmin)
    SUPERADMIN_COMPANY   - Código de empresa a la que estará asociado
"""
import os
import sys
import getpass
import uuid

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models import User, Company, UserRole
from app.core.security import hash_password
from app.core.security_utils import PasswordValidator


def main():
    print("=" * 60)
    print("  DRAGOFACTU — Crear / Promover Superadmin de Plataforma")
    print("=" * 60)
    print()
    print("⚠️  ATENCIÓN: Los superadmins tienen acceso a TODAS las empresas.")
    print("   Usa esto solo para cuentas de administradores de confianza.")
    print()

    db = SessionLocal()

    try:
        # List existing companies
        companies = db.query(Company).filter(Company.is_active == True).all()
        if not companies:
            print("❌ No hay empresas registradas. Registra una empresa primero.")
            sys.exit(1)

        print("Empresas disponibles:")
        for c in companies:
            print(f"  [{c.code}] {c.name}")
        print()

        # Get company
        company_code = os.getenv("SUPERADMIN_COMPANY") or input("Código de empresa: ").strip()
        company = db.query(Company).filter(Company.code == company_code).first()
        if not company:
            print(f"❌ Empresa '{company_code}' no encontrada.")
            sys.exit(1)

        # Check existing users in company
        existing_users = db.query(User).filter(
            User.company_id == company.id,
            User.is_active == True
        ).all()

        if existing_users:
            print(f"\nUsuarios en '{company.name}':")
            for u in existing_users:
                sa_tag = " [SUPERADMIN]" if u.is_superadmin else ""
                print(f"  [{u.username}] {u.full_name} - {u.role.value}{sa_tag}")
            print()

            promote_choice = input("¿Promover usuario existente a superadmin? (s/n): ").strip().lower()
            if promote_choice == "s":
                username = os.getenv("SUPERADMIN_USERNAME") or input("Username a promover: ").strip()
                user = db.query(User).filter(
                    User.company_id == company.id,
                    User.username == username
                ).first()
                if not user:
                    print(f"❌ Usuario '{username}' no encontrado en esta empresa.")
                    sys.exit(1)
                if user.is_superadmin:
                    print(f"ℹ️  '{username}' ya es superadmin.")
                    sys.exit(0)

                confirm = input(f"¿Confirmar promoción de '{username}' a superadmin? (ESCRIBIR 'CONFIRMAR'): ").strip()
                if confirm != "CONFIRMAR":
                    print("Cancelado.")
                    sys.exit(0)

                user.is_superadmin = True
                user.role = UserRole.ADMIN
                db.commit()
                print(f"\n✅ '{username}' ahora es superadmin de plataforma.")
                return

        # Create new superadmin user
        print("\nCrear nuevo usuario superadmin:")
        username = os.getenv("SUPERADMIN_USERNAME") or input("Username: ").strip()
        email = os.getenv("SUPERADMIN_EMAIL") or input("Email: ").strip()

        # Check duplicates
        if db.query(User).filter(User.company_id == company.id, User.username == username).first():
            print(f"❌ Username '{username}' ya existe en esta empresa.")
            sys.exit(1)

        # Password with higher requirement for superadmin
        password = os.getenv("SUPERADMIN_PASSWORD")
        if not password:
            password = getpass.getpass("Password (min 12 chars): ")
            confirm_password = getpass.getpass("Confirmar password: ")
            if password != confirm_password:
                print("❌ Las contraseñas no coinciden.")
                sys.exit(1)

        if len(password) < 12:
            print("❌ La contraseña del superadmin debe tener al menos 12 caracteres.")
            sys.exit(1)

        try:
            PasswordValidator.validate_or_raise(password)
        except Exception as e:
            print(f"❌ Contraseña inválida: {e}")
            sys.exit(1)

        full_name = input("Nombre completo: ").strip() or username

        confirm = input(f"\n¿Crear superadmin '{username}' en empresa '{company.name}'? (ESCRIBIR 'CONFIRMAR'): ").strip()
        if confirm != "CONFIRMAR":
            print("Cancelado.")
            sys.exit(0)

        new_user = User(
            id=uuid.uuid4(),
            company_id=company.id,
            username=username,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True,
            is_superadmin=True,
        )
        db.add(new_user)
        db.commit()

        print(f"\n✅ Superadmin '{username}' creado correctamente.")
        print(f"   Empresa: {company.name} ({company.code})")
        print(f"   URL: https://dragofactu-production.up.railway.app")
        print(f"\n⚠️  Guarda estas credenciales de forma segura.")

    except KeyboardInterrupt:
        print("\nCancelado.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
