"""add_supplier_catalog

Revision ID: fef0f61562b2
Revises: fc2f0af4c0e0
Create Date: 2026-05-07 06:10:34.869552
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'fef0f61562b2'
down_revision: Union[str, None] = 'fc2f0af4c0e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'supplier_catalog',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('company_id', sa.String(36), nullable=False),
        sa.Column('supplier_id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('supplier_ref', sa.String(length=50), nullable=True),
        sa.Column('purchase_price', sa.Float(), nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),
        sa.Column('min_order_qty', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'supplier_id', 'product_id', name='uq_supplier_catalog_entry'),
    )
    op.create_index(op.f('ix_supplier_catalog_company_id'), 'supplier_catalog', ['company_id'], unique=False)
    op.create_index(op.f('ix_supplier_catalog_product_id'), 'supplier_catalog', ['product_id'], unique=False)
    op.create_index(op.f('ix_supplier_catalog_supplier_id'), 'supplier_catalog', ['supplier_id'], unique=False)
    # audit_logs column types are already correct in SQLite — no alter needed


def downgrade() -> None:
    op.drop_index(op.f('ix_supplier_catalog_supplier_id'), table_name='supplier_catalog')
    op.drop_index(op.f('ix_supplier_catalog_product_id'), table_name='supplier_catalog')
    op.drop_index(op.f('ix_supplier_catalog_company_id'), table_name='supplier_catalog')
    op.drop_table('supplier_catalog')
