"""add_delegacion_fields

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-12

"""
from alembic import op
import sqlalchemy as sa


revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    # delivery_notes: add delegacion
    with op.batch_alter_table('delivery_notes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('delegacion', sa.String(length=30), nullable=True))

    # users: add delegacion
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('delegacion', sa.String(length=30), nullable=True))

    # user_permission_targets: make target_user_id nullable + add target_delegacion
    with op.batch_alter_table('user_permission_targets', schema=None) as batch_op:
        batch_op.alter_column('target_user_id', existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column('target_delegacion', sa.String(length=30), nullable=True))


def downgrade():
    with op.batch_alter_table('user_permission_targets', schema=None) as batch_op:
        batch_op.drop_column('target_delegacion')
        batch_op.alter_column('target_user_id', existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('delegacion')

    with op.batch_alter_table('delivery_notes', schema=None) as batch_op:
        batch_op.drop_column('delegacion')
