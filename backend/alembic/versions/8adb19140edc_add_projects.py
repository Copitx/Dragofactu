"""add_projects

Revision ID: 8adb19140edc
Revises: fef0f61562b2
Create Date: 2026-05-07 06:18:03.655486
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '8adb19140edc'
down_revision: Union[str, None] = 'fef0f61562b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_GUID = sa.String(36)


def upgrade() -> None:
    op.create_table(
        'projects',
        sa.Column('id', _GUID, nullable=False),
        sa.Column('company_id', _GUID, nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('client_id', _GUID, nullable=True),
        sa.Column('address', sa.String(length=300), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('estimated_value', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_by', _GUID, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'code', name='uq_project_company_code'),
    )
    op.create_index(op.f('ix_projects_client_id'), 'projects', ['client_id'], unique=False)
    op.create_index(op.f('ix_projects_code'), 'projects', ['code'], unique=False)
    op.create_index(op.f('ix_projects_company_id'), 'projects', ['company_id'], unique=False)

    op.create_table(
        'project_documents',
        sa.Column('id', _GUID, nullable=False),
        sa.Column('project_id', _GUID, nullable=False),
        sa.Column('document_id', _GUID, nullable=False),
        sa.Column('company_id', _GUID, nullable=False),
        sa.Column('linked_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'document_id', name='uq_project_document'),
    )

    op.create_table(
        'project_expenses',
        sa.Column('id', _GUID, nullable=False),
        sa.Column('project_id', _GUID, nullable=False),
        sa.Column('company_id', _GUID, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('description', sa.String(length=300), nullable=False),
        sa.Column('supplier', sa.String(length=150), nullable=True),
        sa.Column('document_ref', sa.String(length=50), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('category', sa.String(length=20), nullable=True),
        sa.Column('worker_id', _GUID, nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_project_expenses_company_id'), 'project_expenses', ['company_id'], unique=False)
    op.create_index(op.f('ix_project_expenses_project_id'), 'project_expenses', ['project_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_project_expenses_project_id'), table_name='project_expenses')
    op.drop_index(op.f('ix_project_expenses_company_id'), table_name='project_expenses')
    op.drop_table('project_expenses')
    op.drop_table('project_documents')
    op.drop_index(op.f('ix_projects_company_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_code'), table_name='projects')
    op.drop_index(op.f('ix_projects_client_id'), table_name='projects')
    op.drop_table('projects')
