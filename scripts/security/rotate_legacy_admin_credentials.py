#!/usr/bin/env python3
"""
Rotate legacy bootstrap credentials for admin users.

Usage examples:
  python scripts/security/rotate_legacy_admin_credentials.py --username admin --show-password
  python scripts/security/rotate_legacy_admin_credentials.py --company-id <uuid> --username admin
  python scripts/security/rotate_legacy_admin_credentials.py --all-admins --show-password
"""

from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path
from typing import Iterable

# Ensure backend imports work when script is executed from repository root.
REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database import SessionLocal  # type: ignore  # noqa: E402
from app.models.user import User, UserRole  # type: ignore  # noqa: E402
from app.core.security import hash_password  # type: ignore  # noqa: E402


def _iter_target_users(db, username: str, company_id: str | None, all_admins: bool) -> Iterable[User]:
    query = db.query(User).filter(User.is_active.is_(True))

    if all_admins:
        query = query.filter(User.role == UserRole.ADMIN)
    else:
        query = query.filter(User.username == username)

    if company_id:
        query = query.filter(User.company_id == company_id)

    return query.all()


def main() -> int:
    parser = argparse.ArgumentParser(description="Rotate legacy bootstrap admin credentials")
    parser.add_argument("--username", default="admin", help="Target username when not using --all-admins")
    parser.add_argument("--company-id", help="Optional company UUID filter")
    parser.add_argument("--all-admins", action="store_true", help="Rotate all active admin users")
    parser.add_argument(
        "--password-length",
        type=int,
        default=20,
        help="Generated password length hint (token_urlsafe, approximate)",
    )
    parser.add_argument(
        "--show-password",
        action="store_true",
        help="Print generated passwords to stdout (handle securely)",
    )
    args = parser.parse_args()

    rotated = 0

    with SessionLocal() as db:
        users = _iter_target_users(db, args.username, args.company_id, args.all_admins)

        if not users:
            print("No matching active users found. Nothing to rotate.")
            return 1

        print(f"Found {len(users)} user(s) to rotate.")

        for user in users:
            new_password = secrets.token_urlsafe(max(12, args.password_length))
            user.password_hash = hash_password(new_password)
            rotated += 1

            identity = f"{user.username} (company_id={user.company_id}, user_id={user.id})"
            if args.show_password:
                print(f"ROTATED: {identity} -> {new_password}")
            else:
                print(f"ROTATED: {identity} -> [hidden]")

        db.commit()

    print(f"Rotation complete. Updated {rotated} user(s).")
    if not args.show_password:
        print("Tip: use --show-password only in secure terminals and rotate again if exposed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
