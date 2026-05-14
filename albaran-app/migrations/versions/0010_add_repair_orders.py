"""add repair_orders and repair_comments tables

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-12
"""
from alembic import op
import sqlalchemy as sa

revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'repair_orders',
        sa.Column('id',               sa.Integer,              primary_key=True),
        sa.Column('machine_id',       sa.Integer,              sa.ForeignKey('machines.id'), nullable=False),
        sa.Column('delegacion',       sa.String(30),           nullable=True),
        sa.Column('description',      sa.Text,                 nullable=True),
        sa.Column('estimated_days',   sa.Integer,              nullable=True),
        sa.Column('cost',             sa.Float,                nullable=True),
        sa.Column('status',           sa.String(10),           nullable=False, server_default='open'),
        sa.Column('resolution_notes', sa.Text,                 nullable=True),
        sa.Column('created_at',       sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_id',    sa.Integer,              sa.ForeignKey('users.id'), nullable=True),
        sa.Column('closed_at',        sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_by_id',     sa.Integer,              sa.ForeignKey('users.id'), nullable=True),
    )
    op.create_index('ix_repair_orders_machine_id', 'repair_orders', ['machine_id'])
    op.create_index('ix_repair_orders_status',     'repair_orders', ['status'])

    op.create_table(
        'repair_comments',
        sa.Column('id',              sa.Integer, primary_key=True),
        sa.Column('repair_order_id', sa.Integer, sa.ForeignKey('repair_orders.id'), nullable=False),
        sa.Column('text',            sa.Text,    nullable=False),
        sa.Column('created_at',      sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_id',   sa.Integer, sa.ForeignKey('users.id'), nullable=True),
    )
    op.create_index('ix_repair_comments_order_id', 'repair_comments', ['repair_order_id'])


def downgrade():
    op.drop_table('repair_comments')
    op.drop_table('repair_orders')
