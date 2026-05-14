"""add signature fields to delivery_notes

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-12
"""
from alembic import op
import sqlalchemy as sa

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('delivery_notes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('signature_token',         sa.String(64),              nullable=True))
        batch_op.add_column(sa.Column('signature_token_expires', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('signature_data',          sa.Text,                    nullable=True))
        batch_op.add_column(sa.Column('signed_at',               sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('signer_name',             sa.String(120),             nullable=True))


def downgrade():
    with op.batch_alter_table('delivery_notes', schema=None) as batch_op:
        batch_op.drop_column('signer_name')
        batch_op.drop_column('signed_at')
        batch_op.drop_column('signature_data')
        batch_op.drop_column('signature_token_expires')
        batch_op.drop_column('signature_token')
