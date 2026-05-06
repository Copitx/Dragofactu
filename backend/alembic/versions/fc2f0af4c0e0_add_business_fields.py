"""add_business_fields

Revision ID: fc2f0af4c0e0
Revises: 003
Create Date: 2026-05-06 23:27:43.662217
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers
revision: str = 'fc2f0af4c0e0'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in the given table."""
    bind = op.get_bind()
    insp = inspect(bind)
    columns = [col["name"] for col in insp.get_columns(table_name)]
    return column_name in columns


def _table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    bind = op.get_bind()
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def upgrade() -> None:
    # audit_logs — may already exist from SQLAlchemy auto-create on startup
    if not _table_exists('audit_logs'):
        op.create_table(
            'audit_logs',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('company_id', sa.String(36), nullable=False),
            sa.Column('user_id', sa.String(36), nullable=False),
            sa.Column('action', sa.String(length=20), nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('entity_id', sa.String(length=32), nullable=True),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True),
                      server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )

    # clients — business fields
    for col_name, col_def in [
        ('payment_method', sa.Column('payment_method', sa.String(50), nullable=True)),
        ('payment_days', sa.Column('payment_days', sa.Integer(), nullable=True)),
        ('contact_person', sa.Column('contact_person', sa.String(100), nullable=True)),
        ('bank_iban', sa.Column('bank_iban', sa.String(255), nullable=True)),
        ('default_discount', sa.Column('default_discount', sa.Float(), nullable=True)),
        ('notes_internal', sa.Column('notes_internal', sa.Text(), nullable=True)),
    ]:
        if not _column_exists('clients', col_name):
            op.add_column('clients', col_def)

    # companies — trade_name + smtp + email templates + logo
    for col_name, col_def in [
        ('trade_name', sa.Column('trade_name', sa.String(200), nullable=True)),
        ('logo_base64', sa.Column('logo_base64', sa.Text(), nullable=True)),
        ('pdf_footer_text', sa.Column('pdf_footer_text', sa.Text(), nullable=True)),
        ('smtp_host', sa.Column('smtp_host', sa.String(200), nullable=True)),
        ('smtp_port', sa.Column('smtp_port', sa.Integer(), nullable=True)),
        ('smtp_user', sa.Column('smtp_user', sa.String(200), nullable=True)),
        ('smtp_password_encrypted', sa.Column('smtp_password_encrypted', sa.Text(), nullable=True)),
        ('smtp_use_tls', sa.Column('smtp_use_tls', sa.Boolean(), nullable=True)),
        ('smtp_from_email', sa.Column('smtp_from_email', sa.String(200), nullable=True)),
        ('smtp_from_name', sa.Column('smtp_from_name', sa.String(200), nullable=True)),
        ('email_subject_template', sa.Column('email_subject_template', sa.String(300), nullable=True)),
        ('email_body_template', sa.Column('email_body_template', sa.Text(), nullable=True)),
    ]:
        if not _column_exists('companies', col_name):
            op.add_column('companies', col_def)

    # document_lines — measurements
    if not _column_exists('document_lines', 'measurements'):
        op.add_column('document_lines', sa.Column('measurements', sa.String(200), nullable=True))

    # documents — business fields
    for col_name, col_def in [
        ('client_reference', sa.Column('client_reference', sa.String(100), nullable=True)),
        ('payment_method', sa.Column('payment_method', sa.String(50), nullable=True)),
        ('execution_location', sa.Column('execution_location', sa.String(200), nullable=True)),
        ('payment_date', sa.Column('payment_date', sa.Date(), nullable=True)),
    ]:
        if not _column_exists('documents', col_name):
            op.add_column('documents', col_def)

    # users — is_superadmin
    if not _column_exists('users', 'is_superadmin'):
        op.add_column('users', sa.Column(
            'is_superadmin', sa.Boolean(), nullable=False, server_default=sa.false()
        ))


def downgrade() -> None:
    op.drop_column('users', 'is_superadmin')
    op.drop_column('documents', 'payment_date')
    op.drop_column('documents', 'execution_location')
    op.drop_column('documents', 'payment_method')
    op.drop_column('documents', 'client_reference')
    op.drop_column('document_lines', 'measurements')
    op.drop_column('companies', 'email_body_template')
    op.drop_column('companies', 'email_subject_template')
    op.drop_column('companies', 'smtp_from_name')
    op.drop_column('companies', 'smtp_from_email')
    op.drop_column('companies', 'smtp_use_tls')
    op.drop_column('companies', 'smtp_password_encrypted')
    op.drop_column('companies', 'smtp_user')
    op.drop_column('companies', 'smtp_port')
    op.drop_column('companies', 'smtp_host')
    op.drop_column('companies', 'pdf_footer_text')
    op.drop_column('companies', 'logo_base64')
    op.drop_column('companies', 'trade_name')
    op.drop_column('clients', 'notes_internal')
    op.drop_column('clients', 'default_discount')
    op.drop_column('clients', 'bank_iban')
    op.drop_column('clients', 'contact_person')
    op.drop_column('clients', 'payment_days')
    op.drop_column('clients', 'payment_method')
