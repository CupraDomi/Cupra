"""add_repair_notes_to_machines

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-12

"""
from alembic import op
import sqlalchemy as sa


revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('machines', schema=None) as batch_op:
        batch_op.add_column(sa.Column('repair_notes', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('machines', schema=None) as batch_op:
        batch_op.drop_column('repair_notes')
