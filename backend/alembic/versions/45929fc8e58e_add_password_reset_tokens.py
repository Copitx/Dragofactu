"""add_password_reset_tokens

Revision ID: 45929fc8e58e
Revises: 8adb19140edc
Create Date: 2026-05-07 13:57:14.590078
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers
revision: str = '45929fc8e58e'
down_revision: Union[str, None] = '8adb19140edc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_GUID = sa.String(36)


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    return name in insp.get_table_names()


def upgrade() -> None:
    if _table_exists("password_reset_tokens"):
        return

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", _GUID, nullable=False),
        sa.Column("user_id", _GUID, nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_password_reset_token_hash"),
    )
    op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])
    op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"])


def downgrade() -> None:
    op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
