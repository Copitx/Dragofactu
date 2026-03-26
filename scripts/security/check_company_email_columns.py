#!/usr/bin/env python3
"""Check/fix email template columns in companies table.

Usage:
  railway run -s Dragofactu -e production -- backend/venv/bin/python scripts/security/check_company_email_columns.py --check
  railway run -s Dragofactu -e production -- backend/venv/bin/python scripts/security/check_company_email_columns.py --apply
"""

from __future__ import annotations

import argparse
import os
import sys

import psycopg2

TARGET_COLUMNS = {
    "email_subject_template": "TEXT",
    "email_body_template": "TEXT",
}


def get_existing_columns(cur):
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'companies'
          AND column_name IN ('email_subject_template', 'email_body_template')
        ORDER BY column_name
        """
    )
    return {row[0] for row in cur.fetchall()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if args.check == args.apply:
        print("Use exactly one mode: --check or --apply")
        return 2

    database_url = os.getenv("DATABASE_URL")
    database_public_url = os.getenv("DATABASE_PUBLIC_URL")
    if database_url and "railway.internal" in database_url and database_public_url:
        # Local scripts cannot resolve Railway private DNS; use public URL when available.
        database_url = database_public_url
    if not database_url:
        print("DATABASE_URL is not set")
        return 2

    conn = psycopg2.connect(database_url)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            existing = get_existing_columns(cur)
            missing = [c for c in TARGET_COLUMNS if c not in existing]

            print(f"existing={sorted(existing)}")
            print(f"missing={missing}")

            if args.check:
                return 0 if not missing else 1

            if not missing:
                print("No schema changes needed.")
                conn.rollback()
                return 0

            for column in missing:
                ddl = f"ALTER TABLE companies ADD COLUMN IF NOT EXISTS {column} {TARGET_COLUMNS[column]}"
                cur.execute(ddl)

            conn.commit()
            print(f"Applied: added {len(missing)} column(s): {missing}")
            return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
