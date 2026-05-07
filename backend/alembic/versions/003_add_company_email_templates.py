"""Add company email templates

Revision ID: 003
Revises: 002
Create Date: 2026-03-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    columns = [col["name"] for col in insp.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    if not _column_exists("companies", "email_subject_template"):
        op.add_column("companies", sa.Column("email_subject_template", sa.String(length=300), nullable=True))
    if not _column_exists("companies", "email_body_template"):
        op.add_column("companies", sa.Column("email_body_template", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "email_body_template")
    op.drop_column("companies", "email_subject_template")
