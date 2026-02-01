"""Create companies table

Revision ID: 001
Revises:
Create Date: 2026-02-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'companies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('legal_name', sa.String(200)),
        sa.Column('tax_id', sa.String(20)),
        sa.Column('address', sa.Text),
        sa.Column('city', sa.String(100)),
        sa.Column('postal_code', sa.String(10)),
        sa.Column('province', sa.String(100)),
        sa.Column('country', sa.String(100), server_default='Espana'),
        sa.Column('phone', sa.String(20)),
        sa.Column('email', sa.String(100)),
        sa.Column('website', sa.String(200)),
        sa.Column('logo_path', sa.String(500)),
        sa.Column('default_language', sa.String(5), server_default='es'),
        sa.Column('default_currency', sa.String(3), server_default='EUR'),
        sa.Column('tax_rate', sa.Float, server_default='21.0'),
        sa.Column('plan_type', sa.String(20), server_default='free'),
        sa.Column('max_users', sa.Integer, server_default='5'),
        sa.Column('max_documents_month', sa.Integer, server_default='100'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('subscription_expires', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table('companies')
