"""add_invoice_fields_to_delivery_notes

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-11 22:37:51.858331

"""
from alembic import op
import sqlalchemy as sa


revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('delivery_notes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('invoice_number', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('invoice_generated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table('delivery_notes', schema=None) as batch_op:
        batch_op.drop_column('invoice_generated_at')
        batch_op.drop_column('invoice_number')
