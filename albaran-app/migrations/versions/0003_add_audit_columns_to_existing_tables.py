"""add_audit_columns_to_existing_tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-11 21:42:24.075129

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('updated_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('deleted_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table('delivery_notes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('updated_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table('machines', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('updated_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('deleted_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table('machines', schema=None) as batch_op:
        batch_op.drop_column('deleted_at')
        batch_op.drop_column('deleted_by_id')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('updated_by_id')
        batch_op.drop_column('created_by_id')

    with op.batch_alter_table('delivery_notes', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('updated_by_id')
        batch_op.drop_column('created_by_id')

    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.drop_column('deleted_at')
        batch_op.drop_column('deleted_by_id')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('updated_by_id')
        batch_op.drop_column('created_by_id')
