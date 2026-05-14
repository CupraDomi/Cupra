"""
Constantes compartidas en toda la aplicación.
Centralizadas aquí para evitar duplicación entre blueprints.
"""

DELEGACIONES = ['Córdoba', 'Málaga', 'Sevilla', 'Cádiz', 'Jaén', 'Granada']

MACHINE_CATEGORIES = [
    ('AWP', 'Plataforma Elevadora'),
    ('FLT', 'Carretilla Elevadora'),
    ('DMP', 'Dúmper'),
    ('EXC', 'Excavadora'),
    ('TLH', 'Manipulador Telescópico'),
    ('RTH', 'Martillo de Vía'),
    ('GEN', 'Grupo Electrógeno'),
    ('TOL', 'Herramienta / Accesorio'),
]

MACHINE_STATUSES = [
    ('free',     'Libre'),
    ('occupied', 'Ocupada'),
    ('reserved', 'Reservada'),
    ('repair',   'En reparación'),
]

ALBARAN_STATUSES = [
    ('active',    'Activo'),
    ('closed',    'Cerrado'),
    ('cancelled', 'Cancelado'),
]
