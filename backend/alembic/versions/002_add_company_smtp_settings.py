"""Add per-company SMTP settings

Revision ID: 002
Revises: 001
Create Date: 2026-03-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("smtp_host", sa.String(length=200), nullable=True))
    op.add_column("companies", sa.Column("smtp_port", sa.Integer(), nullable=True, server_default="587"))
    op.add_column("companies", sa.Column("smtp_user", sa.String(length=200), nullable=True))
    op.add_column("companies", sa.Column("smtp_password_encrypted", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("smtp_use_tls", sa.Boolean(), nullable=True, server_default=sa.text("true")))
    op.add_column("companies", sa.Column("smtp_from_email", sa.String(length=200), nullable=True))
    op.add_column("companies", sa.Column("smtp_from_name", sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "smtp_from_name")
    op.drop_column("companies", "smtp_from_email")
    op.drop_column("companies", "smtp_use_tls")
    op.drop_column("companies", "smtp_password_encrypted")
    op.drop_column("companies", "smtp_user")
    op.drop_column("companies", "smtp_port")
    op.drop_column("companies", "smtp_host")
