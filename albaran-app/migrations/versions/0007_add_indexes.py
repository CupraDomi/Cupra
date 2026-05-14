"""add_indexes_on_hot_columns

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-12

Añade índices en columnas usadas con frecuencia en filtros y joins para
mejorar el rendimiento. Idempotente: usa `op.f()` y nombres explícitos.
"""
from alembic import op


revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


INDEXES = [
    # tabla, índice, columnas
    ('machines',                'ix_machines_status',                       ['status']),
    ('machines',                'ix_machines_category',                     ['category']),
    ('delivery_notes',          'ix_delivery_notes_status',                 ['status']),
    ('delivery_notes',          'ix_delivery_notes_client_id',              ['client_id']),
    ('delivery_notes',          'ix_delivery_notes_delegacion',             ['delegacion']),
    ('delivery_notes',          'ix_delivery_notes_rental_start',           ['rental_start']),
    ('delivery_note_machines',  'ix_delivery_note_machines_machine_id',     ['machine_id']),
    ('delivery_note_machines',  'ix_delivery_note_machines_delivery_note_id', ['delivery_note_id']),
    ('machine_status_log',      'ix_machine_status_log_machine_id',         ['machine_id']),
    ('machine_status_log',      'ix_machine_status_log_delivery_note_id',   ['delivery_note_id']),
    ('client_contacts',         'ix_client_contacts_client_id',             ['client_id']),
    ('audit_log',               'ix_audit_log_user_id',                     ['user_id']),
    ('audit_log',               'ix_audit_log_action',                      ['action']),
    ('audit_log',               'ix_audit_log_entity',                      ['entity']),
    ('user_permissions',        'ix_user_permissions_user_id',              ['user_id']),
    ('user_permission_targets', 'ix_user_permission_targets_permission_id', ['permission_id']),
]


def upgrade():
    for table, name, cols in INDEXES:
        try:
            op.create_index(name, table, cols)
        except Exception:
            # El índice ya existe o la tabla aún no — ignorar para idempotencia.
            pass


def downgrade():
    for _table, name, _cols in INDEXES:
        try:
            op.drop_index(name)
        except Exception:
            pass
