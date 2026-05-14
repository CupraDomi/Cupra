"""
Poblar la base de datos con datos de demostración realistas.
Ejecutar localmente: python seed.py
Desde Flask CLI:     flask seed-demo
"""
from datetime import date, datetime, timezone
from app import create_app, db
from app.models import (Machine, MachineStatusLog, Client, ClientContact,
                        DeliveryNote, DeliveryNoteMachine, RepairOrder, RepairComment)
from app.auth.models import User

app = create_app()

# ──────────────────────────────────────────────────────────────────────────────
# MÁQUINAS
# ──────────────────────────────────────────────────────────────────────────────
# (code, name, category, variant, specs, status, current_delegacion)

MACHINES = [
    # ── Plataformas elevadoras diésel ────────────────────────────────────────
    ('AWP-D-001', 'Plataforma tijera diésel 12m',      'AWP', 'D',
     'Altura trabajo: 12m | Carga: 450kg | Peso: 5.200kg | Año: 2019',
     'free', 'Córdoba'),
    ('AWP-D-002', 'Plataforma tijera diésel 16m',      'AWP', 'D',
     'Altura trabajo: 16m | Carga: 450kg | Peso: 6.800kg | Año: 2020',
     'occupied', 'Sevilla'),
    ('AWP-D-003', 'Plataforma articulada diésel 20m',  'AWP', 'D',
     'Altura trabajo: 20m | Alcance lateral: 9m | Año: 2021',
     'occupied', 'Málaga'),
    ('AWP-D-004', 'Plataforma articulada diésel 28m',  'AWP', 'D',
     'Altura trabajo: 28m | Alcance lateral: 16m | Año: 2022',
     'free', 'Córdoba'),
    ('AWP-D-005', 'Plataforma articulada diésel 32m',  'AWP', 'D',
     'Altura trabajo: 32m | Alcance lateral: 18m | Montada en camión | Año: 2023',
     'occupied', 'Granada'),
    ('AWP-D-006', 'Plataforma tijera diésel 14m 4x4',  'AWP', 'D',
     'Altura trabajo: 14m | Carga: 500kg | Todo terreno | Año: 2021',
     'free', 'Sevilla'),
    ('AWP-D-007', 'Plataforma articulada diésel 24m',  'AWP', 'D',
     'Altura trabajo: 24m | Alcance lateral: 12m | Año: 2020',
     'repair', 'Córdoba'),
    ('AWP-D-008', 'Plataforma tijera diésel 18m',      'AWP', 'D',
     'Altura trabajo: 18m | Carga: 680kg | Año: 2022',
     'free', 'Jaén'),

    # ── Plataformas elevadoras eléctricas ────────────────────────────────────
    ('AWP-E-001', 'Plataforma tijera eléctrica 8m',   'AWP', 'E',
     'Altura trabajo: 8m | Carga: 450kg | Interior/exterior | Año: 2021',
     'free', 'Córdoba'),
    ('AWP-E-002', 'Plataforma tijera eléctrica 10m',  'AWP', 'E',
     'Altura trabajo: 10m | Carga: 450kg | Año: 2022',
     'occupied', 'Cádiz'),
    ('AWP-E-003', 'Plataforma vertical eléctrica 6m', 'AWP', 'E',
     'Altura trabajo: 6m | 1 persona | Compacta | Año: 2023',
     'free', 'Sevilla'),
    ('AWP-E-004', 'Plataforma tijera eléctrica 12m',  'AWP', 'E',
     'Altura trabajo: 12m | Carga: 500kg | Ultra silenciosa | Año: 2023',
     'occupied', 'Málaga'),
    ('AWP-E-005', 'Plataforma mástil vertical 8m',    'AWP', 'E',
     'Altura trabajo: 8m | Ancho: 0,76m | Muy compacta | Año: 2022',
     'free', 'Córdoba'),
    ('AWP-E-006', 'Plataforma articulada eléctrica 16m','AWP','E',
     'Altura trabajo: 16m | Batería litio | Zero emisiones | Año: 2024',
     'free', 'Granada'),

    # ── Carretillas diésel ────────────────────────────────────────────────────
    ('FLT-D-001', 'Carretilla diésel 3.5T',     'FLT', 'D',
     'Capacidad: 3.500kg | Mástil triple: 4,5m | Año: 2018',
     'free', 'Córdoba'),
    ('FLT-D-002', 'Carretilla diésel 5T',       'FLT', 'D',
     'Capacidad: 5.000kg | Mástil: 5m | Ruedas neumáticas | Año: 2020',
     'occupied', 'Sevilla'),
    ('FLT-D-003', 'Carretilla diésel 7T',       'FLT', 'D',
     'Capacidad: 7.000kg | Mástil: 4m | Uso portuario | Año: 2019',
     'free', 'Cádiz'),
    ('FLT-D-004', 'Carretilla diésel 10T',      'FLT', 'D',
     'Capacidad: 10.000kg | Mástil: 3,5m | Industrial pesado | Año: 2021',
     'free', 'Córdoba'),
    ('FLT-D-005', 'Carretilla diésel 3T todo terreno','FLT','D',
     'Capacidad: 3.000kg | 4x4 | Obra exterior | Año: 2022',
     'repair', 'Málaga'),

    # ── Carretillas eléctricas ────────────────────────────────────────────────
    ('FLT-E-001', 'Carretilla eléctrica 2T',    'FLT', 'E',
     'Capacidad: 2.000kg | Mástil: 4m | Interior | Año: 2022',
     'free', 'Córdoba'),
    ('FLT-E-002', 'Carretilla eléctrica 3T',    'FLT', 'E',
     'Capacidad: 3.000kg | Mástil: 5m | Año: 2023',
     'occupied', 'Jaén'),
    ('FLT-E-003', 'Apilador eléctrico 1.5T',    'FLT', 'E',
     'Capacidad: 1.500kg | Altura: 3,3m | Pasillo estrecho | Año: 2023',
     'free', 'Sevilla'),
    ('FLT-E-004', 'Retráctil eléctrico 2.5T',   'FLT', 'E',
     'Capacidad: 2.500kg | Mástil: 6m | Almacén alto | Año: 2022',
     'free', 'Córdoba'),

    # ── Dúmperes ─────────────────────────────────────────────────────────────
    ('DMP-3T-001', 'Dúmper articulado 3T',          'DMP', '3T',
     'Capacidad: 3.000kg | Tracción 4x4 | Descarga frontal | Año: 2020',
     'occupied', 'Granada'),
    ('DMP-3T-002', 'Dúmper articulado 3T cabina',   'DMP', '3T',
     'Capacidad: 3.000kg | Con cabina ROPS | Año: 2022',
     'free', 'Córdoba'),
    ('DMP-6T-001', 'Dúmper articulado 6T',          'DMP', '6T',
     'Capacidad: 6.000kg | Tracción 4x4 | Año: 2019',
     'free', 'Sevilla'),
    ('DMP-6T-002', 'Dúmper articulado 6T cabina',   'DMP', '6T',
     'Capacidad: 6.000kg | Con cabina ROPS/FOPS | Año: 2021',
     'occupied', 'Málaga'),
    ('DMP-9T-001', 'Dúmper articulado 9T',          'DMP', '9T',
     'Capacidad: 9.000kg | Tracción 4x4 | Grandes movimientos de tierra | Año: 2020',
     'free', 'Córdoba'),
    ('DMP-R-3T-001','Dúmper de vía 3T',             'DMP', 'R-3T',
     'Capacidad: 3.000kg | Apto vía ferroviaria | UIC60 | Año: 2020',
     'occupied', 'Jaén'),
    ('DMP-R-6T-001','Dúmper de vía 6T',             'DMP', 'R-6T',
     'Capacidad: 6.000kg | Apto vía ferroviaria | UIC54/60 | Año: 2018',
     'occupied', 'Jaén'),
    ('DMP-R-9T-001','Dúmper de vía 9T',             'DMP', 'R-9T',
     'Capacidad: 9.000kg | Vía ferroviaria | Gran capacidad | Año: 2021',
     'free', 'Córdoba'),

    # ── Excavadoras ──────────────────────────────────────────────────────────
    ('EXC-1T-001',  'Miniexcavadora 1.5T',           'EXC', '1T',
     'Peso: 1.500kg | Profundidad: 1,8m | Muy compacta | Año: 2023',
     'free', 'Sevilla'),
    ('EXC-3T-001',  'Miniexcavadora 3T',             'EXC', '3T',
     'Peso: 3.200kg | Profundidad: 2,5m | Año: 2021',
     'occupied', 'Cádiz'),
    ('EXC-5T-001',  'Excavadora 5T',                 'EXC', '5T',
     'Peso: 5.500kg | Profundidad: 3,5m | Brazo largo | Año: 2020',
     'free', 'Córdoba'),
    ('EXC-8T-001',  'Excavadora 8T',                 'EXC', '8T',
     'Peso: 8.500kg | Profundidad: 4,2m | Año: 2019',
     'occupied', 'Málaga'),
    ('EXC-14T-001', 'Excavadora 14T',                'EXC', '14T',
     'Peso: 14.000kg | Profundidad: 5m | Rastrillo y cuchara | Año: 2021',
     'free', 'Córdoba'),
    ('EXC-20T-001', 'Excavadora 20T',                'EXC', '20T',
     'Peso: 20.000kg | Profundidad: 6,5m | Año: 2020',
     'repair', 'Granada'),
    ('EXC-30T-001', 'Excavadora 30T',                'EXC', '30T',
     'Peso: 30.000kg | Profundidad: 7,5m | Alta potencia | Año: 2019',
     'free', 'Sevilla'),

    # ── Manipuladores telescópicos ────────────────────────────────────────────
    ('TLH-14M-001', 'Manipulador telescópico 14m 3T', 'TLH', '14M',
     'Altura max: 14m | Capacidad: 3.000kg | Año: 2020',
     'free', 'Córdoba'),
    ('TLH-17M-001', 'Manipulador telescópico 17m 3.5T','TLH','17M',
     'Altura max: 17m | Capacidad: 3.500kg | Año: 2021',
     'occupied', 'Sevilla'),
    ('TLH-25M-001', 'Manipulador telescópico 25m 5T', 'TLH', '25M',
     'Altura max: 25m | Capacidad: 5.000kg | Rotativo | Año: 2022',
     'occupied', 'Granada'),
    ('TLH-30M-001', 'Manipulador telescópico 30m 4T', 'TLH', '30M',
     'Altura max: 30m | Capacidad: 4.000kg | Rotativo | Año: 2023',
     'free', 'Málaga'),

    # ── Martillos de vía ferroviaria ──────────────────────────────────────────
    ('RTH-001', 'Martillo hidráulico de vía UIC60',   'RTH', '',
     'Para trabajos en vía ferroviaria | Compatible UIC54/60 | Año: 2017',
     'occupied', 'Jaén'),
    ('RTH-002', 'Martillo neumático de vía pesado',    'RTH', '',
     'Alta potencia | Trabajo continuo | Año: 2019',
     'free', 'Córdoba'),
    ('RTH-003', 'Bateadora de vía manual',             'RTH', '',
     'Compactación balasto | 1 operario | Año: 2020',
     'occupied', 'Jaén'),
    ('RTH-004', 'Esmeriladora de carril',              'RTH', '',
     'Perfilado de carril | Motor gasolina | Año: 2021',
     'free', 'Córdoba'),

    # ── Grupos electrógenos ───────────────────────────────────────────────────
    ('GEN-005K-001', 'Grupo electrógeno 5kVA',   'GEN', '005K',
     'Potencia: 5kVA | Monofásico | Insonorizado | Año: 2020',
     'free', 'Córdoba'),
    ('GEN-005K-002', 'Grupo electrógeno 5kVA',   'GEN', '005K',
     'Potencia: 5kVA | Monofásico | Portátil | Año: 2021',
     'occupied', 'Cádiz'),
    ('GEN-020K-001', 'Grupo electrógeno 20kVA',  'GEN', '020K',
     'Potencia: 20kVA | Trifásico | Año: 2019',
     'occupied', 'Sevilla'),
    ('GEN-045K-001', 'Grupo electrógeno 45kVA',  'GEN', '045K',
     'Potencia: 45kVA | Trifásico | Remolque | Año: 2021',
     'free', 'Córdoba'),
    ('GEN-045K-002', 'Grupo electrógeno 45kVA',  'GEN', '045K',
     'Potencia: 45kVA | Trifásico | Cabinado | Año: 2022',
     'occupied', 'Málaga'),
    ('GEN-100K-001', 'Grupo electrógeno 100kVA', 'GEN', '100K',
     'Potencia: 100kVA | Trifásico | Cabinado | Año: 2020',
     'occupied', 'Granada'),
    ('GEN-200K-001', 'Grupo electrógeno 200kVA', 'GEN', '200K',
     'Potencia: 200kVA | Trifásico | Gran obra | Año: 2018',
     'free', 'Sevilla'),
    ('GEN-500K-001', 'Grupo electrógeno 500kVA', 'GEN', '500K',
     'Potencia: 500kVA | Gran evento / industria | Año: 2022',
     'free', 'Córdoba'),

    # ── Herramientas y accesorios ─────────────────────────────────────────────
    ('TOL-COMPACTOR-001', 'Placa compactadora vibrante', 'TOL', 'COMPACTOR',
     'Peso: 90kg | Ancho trabajo: 50cm | Gasolina | Año: 2021',
     'occupied', 'Córdoba'),
    ('TOL-COMPACTOR-002', 'Rodillo compactador 1T',      'TOL', 'COMPACTOR',
     'Peso: 1.000kg | Doble tambor | Asfalto y suelo | Año: 2020',
     'free', 'Sevilla'),
    ('TOL-PUMP-001',     'Bomba de achique 3"',           'TOL', 'PUMP',
     'Caudal: 1.100 l/min | Altura: 28m | Gasolina | Año: 2020',
     'occupied', 'Cádiz'),
    ('TOL-PUMP-002',     'Bomba sumergible 2"',           'TOL', 'PUMP',
     'Caudal: 360 l/min | Eléctrica | Aguas limpias | Año: 2022',
     'free', 'Córdoba'),
    ('TOL-WELD-001',     'Equipo de soldadura MIG 200A',  'TOL', 'WELD',
     '200A | MIG/MAG | Con carrete y manguera | Año: 2022',
     'free', 'Málaga'),
    ('TOL-HAMMER-001',   'Martillo demoledor eléctrico',  'TOL', 'HAMMER',
     '1.700W | 45J | Con cincel y paleta | Año: 2021',
     'occupied', 'Jaén'),
    ('TOL-SAW-001',      'Cortadora de pavimento diésel', 'TOL', 'SAW',
     'Disco 400mm | Profundidad 140mm | Agua | Año: 2020',
     'free', 'Córdoba'),
]


# ──────────────────────────────────────────────────────────────────────────────
# CLIENTES
# ──────────────────────────────────────────────────────────────────────────────
# (client_code, client_type, company_name, tax_id, address, phone, email, notes)

CLIENTS = [
    ('C-FERRO-001',   'company',
     'Ferrovial Construcción S.A.',
     'A-28012345', 'Calle Príncipe de Vergara, 135, 28002 Madrid',
     '+34 91 586 2500', 'alquileres@ferrovial.com',
     'Cliente preferente. Facturación mensual. Requieren albarán firmado.'),

    ('C-ACCIONA-001', 'company',
     'Acciona Infraestructuras S.A.',
     'A-08001234', 'Av. de Europa, 18, 28108 Alcobendas, Madrid',
     '+34 91 663 2850', 'maquinaria@acciona.com',
     'Obras de infraestructuras. Pago a 60 días.'),

    ('C-VIAS-001',    'company',
     'Vías y Construcciones S.L.',
     'B-46009876', 'Polígono Industrial Sur, Nave 12, 46190 Valencia',
     '+34 96 312 4500', 'compras@viasyconstrucciones.es',
     'Especialistas en obra ferroviaria. Habituales de dúmperes de vía y RTH.'),

    ('C-SACYR-001',   'company',
     'Sacyr Construcción S.A.U.',
     'A-78976395', 'Paseo de la Castellana, 83-85, 28046 Madrid',
     '+34 91 545 5000', 'flota@sacyr.com',
     'Grandes proyectos de infraestructura. Contratos marco anuales.'),

    ('C-ORTIZ-001',   'company',
     'Constructora San José S.A.',
     'A-14045678', 'Av. de la Innovación, 1, 14014 Córdoba',
     '+34 957 400 200', 'compras@ortiz-construccion.es',
     'Cliente local. Obras en la provincia de Córdoba principalmente.'),

    ('C-GARCIA-001',  'individual',
     'García Martínez, Pedro',
     '12345678A', 'Calle Mayor, 22, 14900 Lucena, Córdoba',
     '+34 600 111 222', 'pedro.garcia.obras@gmail.com',
     'Autónomo. Obras menores. Pago al contado.'),

    ('C-RUBIO-001',   'individual',
     'Rubio Fernández, Antonio',
     '87654321B', 'C/ Tendillas, 5, 14001 Córdoba',
     '+34 650 333 444', 'antonio.rubio@gmail.com',
     'Pequeñas obras de reforma. Alquileres de corta duración.'),

    ('C-MALAGA-001',  'company',
     'Málaga Obras y Servicios S.L.',
     'B-29098765', 'Polígono El Viso, Nave 3, 29006 Málaga',
     '+34 95 232 5100', 'operaciones@malagaobras.es',
     'Obras de urbanización en Costa del Sol.'),

    ('C-HISPANIA-001','company',
     'Hispania Infraestructuras S.L.',
     'B-41023456', 'Calle Resolana, 50, 41009 Sevilla',
     '+34 95 491 2300', 'alquileres@hispania-infra.es',
     'Proyectos de saneamiento y abastecimiento en Andalucía occidental.'),

    ('C-INGEOBRA-001','company',
     'Ingeobra Andalucía S.L.',
     'B-14078901', 'Av. del Brillante, 89, 14012 Córdoba',
     '+34 957 265 300', 'ingenieria@ingeobra.es',
     'Ingeniería y construcción. Cliente desde 2019.'),

    ('C-PORTGRA-001', 'company',
     'Portgranada S.L.',
     'B-18056789', 'Polígono PISA, Av. de la Ciencia, 18, 18015 Granada',
     '+34 958 400 100', 'logistica@portgranada.es',
     'Empresa de logística y almacenaje. Alquiler habitual de carretillas.'),

    ('C-CADIZ-001',   'company',
     'Bahía Obras y Reformas S.L.',
     'B-11034567', 'Polígono Las Aletas, Nave 7, 11510 Puerto Real, Cádiz',
     '+34 956 201 400', 'obras@bahiareformas.es',
     'Construcción naval y obras portuarias.'),

    ('C-ENRESA-001',  'company',
     'Enresa Proyectos Industriales S.A.',
     'A-14056789', 'Av. de la Electrónica, 33, 14014 Córdoba',
     '+34 957 190 500', 'proyectos@enresa-industrial.es',
     'Sector industrial. Montajes en fábrica.'),

    ('C-RENOVAB-001', 'company',
     'Renovables Betis S.L.',
     'B-41067890', 'C/ Antonio Bienvenida, 12, 41009 Sevilla',
     '+34 95 477 3300', 'operaciones@renovablesbetis.es',
     'Instalación de parques eólicos y fotovoltaicos en Andalucía.'),

    ('C-JAENCON-001', 'company',
     'Construcciones Úbeda S.L.',
     'B-23045678', 'Polígono Los Olivares, Nave 14, 23400 Úbeda, Jaén',
     '+34 953 750 200', 'compras@construcciones-ubeda.es',
     'Obras en la provincia de Jaén. Clientes habituales de material ferroviario.'),
]


CONTACTS = {
    'C-FERRO-001':   [
        ('Juan Pérez Ruiz',   'Jefe de compras',    '+34 91 586 2501', 'jperez@ferrovial.com'),
        ('Laura Sanz',        'Administrativa',     '+34 91 586 2502', 'lsanz@ferrovial.com'),
    ],
    'C-ACCIONA-001': [
        ('Roberto Iglesias',  'Responsable flota',  '+34 91 663 2851', 'riglesias@acciona.com'),
        ('Mónica Ruiz',       'Técnica de obra',    '+34 650 789 012', 'mruiz@acciona.com'),
    ],
    'C-VIAS-001':    [
        ('María Torres',      'Dirección obra',     '+34 96 312 4501', 'mtorres@viasyconstrucciones.es'),
        ('Carlos Rueda',      'Técnico ferroviario','+34 645 234 567', 'crueda@viasyconstrucciones.es'),
    ],
    'C-SACYR-001':   [
        ('Ignacio Molina',    'Resp. maquinaria',   '+34 91 545 5010', 'imolina@sacyr.com'),
    ],
    'C-ORTIZ-001':   [
        ('Francisco Ortiz',   'Gerente',            '+34 957 400 201', 'fortiz@ortiz-construccion.es'),
        ('Ana Herrera',       'Administrativa',     '+34 957 400 202', 'aherrera@ortiz-construccion.es'),
    ],
    'C-GARCIA-001':  [
        ('Pedro García',      'Titular',            '+34 600 111 222', 'pedro.garcia.obras@gmail.com'),
    ],
    'C-RUBIO-001':   [
        ('Antonio Rubio',     'Titular',            '+34 650 333 444', 'antonio.rubio@gmail.com'),
    ],
    'C-MALAGA-001':  [
        ('Jesús Moreno',      'Jefe de obra',       '+34 95 232 5101', 'jmoreno@malagaobras.es'),
        ('Carmen Jiménez',    'Compras',            '+34 600 456 789', 'cjimenez@malagaobras.es'),
    ],
    'C-HISPANIA-001':[
        ('Diego Castillo',    'Director técnico',   '+34 95 491 2301', 'dcastillo@hispania-infra.es'),
    ],
    'C-INGEOBRA-001':[
        ('Miguel Ángel Reyes','Responsable flota',  '+34 957 265 301', 'mreyes@ingeobra.es'),
        ('Cristina López',    'Administración',     '+34 670 234 567', 'clopez@ingeobra.es'),
    ],
    'C-PORTGRA-001': [
        ('Salvador Gómez',    'Jefe de almacén',    '+34 958 400 101', 'sgomez@portgranada.es'),
    ],
    'C-CADIZ-001':   [
        ('Ramón Díaz',        'Encargado',          '+34 956 201 401', 'rdiaz@bahiareformas.es'),
    ],
    'C-ENRESA-001':  [
        ('Alberto Sánchez',   'Ing. de proyectos',  '+34 957 190 501', 'asanchez@enresa-industrial.es'),
    ],
    'C-RENOVAB-001': [
        ('Patricia Medina',   'Resp. operaciones',  '+34 95 477 3301', 'pmedina@renovablesbetis.es'),
        ('Javier Luna',       'Técnico eólico',     '+34 680 123 456', 'jluna@renovablesbetis.es'),
    ],
    'C-JAENCON-001': [
        ('Eduardo Palma',     'Encargado obra',     '+34 953 750 201', 'epalma@construcciones-ubeda.es'),
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
# ALBARANES
# ──────────────────────────────────────────────────────────────────────────────
# (num, client_code, machine_codes[], start, end,
#  pricing_mode, price_rate, price_unit, total_price,
#  delegacion, location, notes, created_by, status)

NOTES_DATA = [
    # ── Cerrados ────────────────────────────────────────────────────────────
    ('ALB-2025-0001', 'C-FERRO-001',
     ['AWP-D-003', 'GEN-045K-001'],
     date(2025, 9, 1), date(2025, 11, 30),
     'closed', None, None, 22500.0,
     'Córdoba', 'Viaducto A-45, tramo Córdoba Norte', 'Incluye transporte y montaje.',
     'Ana López', 'closed'),

    ('ALB-2025-0002', 'C-ACCIONA-001',
     ['EXC-20T-001'],
     date(2025, 10, 1), date(2025, 12, 15),
     'open', 450.0, 'day', None,
     'Sevilla', 'AVE Tramo Sevilla-Antequera', '',
     'Carlos Vega', 'closed'),

    ('ALB-2025-0003', 'C-VIAS-001',
     ['DMP-R-3T-001', 'DMP-R-6T-001', 'RTH-001'],
     date(2025, 11, 1), date(2026, 1, 31),
     'open', 1200.0, 'week', None,
     'Jaén', 'Renovación vía Renfe — tramo Jaén-Linares', 'Permisos ADIF adjuntos.',
     'Ana López', 'closed'),

    ('ALB-2025-0004', 'C-GARCIA-001',
     ['FLT-D-001'],
     date(2025, 11, 10), date(2025, 11, 30),
     'closed', None, None, 1100.0,
     'Córdoba', 'Nave industrial Polígono Las Quemadas, Córdoba', '',
     'Marcos Torres', 'closed'),

    ('ALB-2025-0005', 'C-MALAGA-001',
     ['AWP-E-004', 'GEN-020K-001'],
     date(2025, 12, 1), date(2026, 1, 15),
     'open', 195.0, 'day', None,
     'Málaga', 'Rehabilitación fachada, Paseo del Limonar, Málaga', '',
     'Ana López', 'closed'),

    ('ALB-2025-0006', 'C-SACYR-001',
     ['TLH-25M-001', 'GEN-100K-001'],
     date(2025, 10, 15), date(2025, 12, 31),
     'open', 3200.0, 'week', None,
     'Granada', 'Parque eólico Sierra de Baza', 'Acceso especial. Camión grúa necesario.',
     'Carlos Vega', 'closed'),

    ('ALB-2026-0001', 'C-VIAS-001',
     ['RTH-002', 'DMP-R-9T-001'],
     date(2026, 1, 15), date(2026, 3, 15),
     'open', 980.0, 'week', None,
     'Jaén', 'Mantenimiento vía Cercanías Jaén', '',
     'Marcos Torres', 'closed'),

    ('ALB-2026-0002', 'C-ORTIZ-001',
     ['EXC-5T-001', 'DMP-3T-002'],
     date(2026, 2, 1), date(2026, 3, 31),
     'closed', None, None, 8600.0,
     'Córdoba', 'Canalización pluviales — C/ Cronista Rey Díaz, Córdoba', '',
     'Ana López', 'closed'),

    ('ALB-2026-0003', 'C-CADIZ-001',
     ['FLT-D-003'],
     date(2026, 2, 10), date(2026, 3, 10),
     'open', 220.0, 'day', None,
     'Cádiz', 'Astilleros Cádiz, zona de carga', '',
     'Carlos Vega', 'closed'),

    ('ALB-2026-0004', 'C-GARCIA-001',
     ['TOL-COMPACTOR-001', 'TOL-PUMP-001'],
     date(2026, 3, 5), date(2026, 3, 25),
     'open', 75.0, 'day', None,
     'Córdoba', 'Urbanización Los Pinos, Lucena', '',
     'Marcos Torres', 'closed'),

    ('ALB-2026-0005', 'C-PORTGRA-001',
     ['FLT-E-002'],
     date(2026, 3, 1), date(2026, 4, 30),
     'open', 85.0, 'day', None,
     'Granada', 'Almacén logístico, Polígono PISA, Granada', 'Uso en interior.',
     'Ana López', 'closed'),

    ('ALB-2026-0006', 'C-HISPANIA-001',
     ['EXC-8T-001', 'DMP-6T-002'],
     date(2026, 3, 15), date(2026, 5, 15),
     'closed', None, None, 14200.0,
     'Málaga', 'Obra de saneamiento — Polígono El Viso, Vélez-Málaga', '',
     'Carlos Vega', 'closed'),

    ('ALB-2026-0007', 'C-RUBIO-001',
     ['AWP-E-001'],
     date(2026, 4, 1), date(2026, 4, 15),
     'closed', None, None, 680.0,
     'Córdoba', 'Reforma local C/ Cruz Conde, Córdoba', '',
     'Marcos Torres', 'closed'),

    ('ALB-2026-0008', 'C-ENRESA-001',
     ['FLT-E-004', 'TOL-WELD-001'],
     date(2026, 4, 7), date(2026, 4, 30),
     'open', 130.0, 'day', None,
     'Córdoba', 'Planta industrial Almogávares, Córdoba', 'Montaje de estructura metálica.',
     'Ana López', 'closed'),

    # ── Activos ─────────────────────────────────────────────────────────────
    ('ALB-2026-0009', 'C-FERRO-001',
     ['AWP-D-005'],
     date(2026, 5, 2), None,
     'closed', None, None, 9800.0,
     'Granada', 'Puente sobre el Genil — A-92, Granada', '',
     'Ana López', 'active'),

    ('ALB-2026-0010', 'C-ACCIONA-001',
     ['TLH-17M-001', 'GEN-045K-002'],
     date(2026, 5, 5), None,
     'open', 2800.0, 'week', None,
     'Sevilla', 'Parque eólico Alcalá de Guadaíra', 'Requiere grúa de acompañamiento.',
     'Carlos Vega', 'active'),

    ('ALB-2026-0011', 'C-VIAS-001',
     ['DMP-R-3T-001', 'RTH-001', 'RTH-003'],
     date(2026, 5, 6), None,
     'open', 1450.0, 'week', None,
     'Jaén', 'Renovación vía Jaén-Úbeda, PK 12-28', 'ADIF: expediente 2026-JA-018.',
     'Marcos Torres', 'active'),

    ('ALB-2026-0012', 'C-ORTIZ-001',
     ['EXC-3T-001'],
     date(2026, 5, 8), None,
     'open', 185.0, 'day', None,
     'Cádiz', 'Urbanización El Puerto, El Puerto de Santa María', '',
     'Ana López', 'active'),

    ('ALB-2026-0013', 'C-JAENCON-001',
     ['DMP-R-6T-001', 'RTH-004'],
     date(2026, 5, 9), None,
     'open', 900.0, 'week', None,
     'Jaén', 'Mantenimiento vías, zona Úbeda-Baeza', 'Coordinación con Adif zona sur.',
     'Carlos Vega', 'active'),

    ('ALB-2026-0014', 'C-RENOVAB-001',
     ['TLH-25M-001', 'GEN-100K-001'],
     date(2026, 5, 3), None,
     'open', 3500.0, 'week', None,
     'Granada', 'Parque eólico Baza-Norte, Fase II', 'Incluye operador.',
     'Ana López', 'active'),

    ('ALB-2026-0015', 'C-INGEOBRA-001',
     ['AWP-D-002'],
     date(2026, 5, 7), None,
     'open', 280.0, 'day', None,
     'Sevilla', 'Rehabilitación puente C/ Resolana, Sevilla', '',
     'Marcos Torres', 'active'),

    ('ALB-2026-0016', 'C-HISPANIA-001',
     ['EXC-8T-001'],
     date(2026, 5, 10), None,
     'open', 380.0, 'day', None,
     'Málaga', 'Ampliación red saneamiento — Estepona', '',
     'Carlos Vega', 'active'),

    ('ALB-2026-0017', 'C-CADIZ-001',
     ['FLT-D-002'],
     date(2026, 5, 12), None,
     'open', 175.0, 'day', None,
     'Sevilla', 'Puerto de Sevilla, zona de contenedores', '',
     'Ana López', 'active'),

    ('ALB-2026-0018', 'C-PORTGRA-001',
     ['FLT-E-001', 'FLT-E-003'],
     date(2026, 5, 5), None,
     'open', 145.0, 'day', None,
     'Granada', 'Centro logístico Amazon, Zona Franca Granada', 'Dos turnos.',
     'Marcos Torres', 'active'),

    ('ALB-2026-0019', 'C-SACYR-001',
     ['AWP-E-002', 'GEN-005K-002'],
     date(2026, 5, 13), None,
     'open', 210.0, 'day', None,
     'Cádiz', 'Rehabilitación fachada histórica — Cádiz centro', '',
     'Ana López', 'active'),

    ('ALB-2026-0020', 'C-RUBIO-001',
     ['TOL-HAMMER-001'],
     date(2026, 5, 14), None,
     'open', 55.0, 'day', None,
     'Jaén', 'Reforma interior C/ Fuente Nueva, Jaén', '',
     'Carlos Vega', 'active'),
]


# ──────────────────────────────────────────────────────────────────────────────
# PARTES DE REPARACIÓN
# ──────────────────────────────────────────────────────────────────────────────
# Para las máquinas con status='repair'

REPAIRS = [
    # (machine_code, delegacion, description, estimated_days, cost, status,
    #  resolution_notes, created_at_offset_days, comments[])
    ('AWP-D-007', 'Córdoba',
     'Fallo en el sistema hidráulico: pérdida de presión en cilindro derecho del brazo articulado. La plataforma no alcanza la altura máxima de trabajo.',
     7, None, 'open', None, -5,
     [
         ('Revisado sistema hidráulico. Detectada rotura en retén del cilindro derecho. '
          'Pedido repuesto al proveedor (JLG Parts). ETA: 3-4 días.', -4),
         ('Recibidos retenedores. Iniciada sustitución.', -1),
     ]),
    ('FLT-D-005', 'Málaga',
     'Tracción trasera sin respuesta. Probable fallo en diferencial trasero o fallo en la transmisión hidrostática.',
     10, None, 'open', None, -8,
     [
         ('Diagnóstico inicial: se descarta el diferencial. Problema en bomba hidrostática. '
          'Consultado con taller externo especializado en CAT.', -7),
         ('Taller externo confirma fallo en bomba. Presupuesto: 2.800 €. '
          'Pendiente aprobación de dirección.', -3),
     ]),
    ('EXC-20T-001', 'Granada',
     'Motor no arranca. Avería eléctrica: posible fallo en centralita de motor o solenoide de arranque.',
     5, 1200.0, 'open', None, -12,
     [
         ('Comprobado solenoide — OK. Centralita enviada a diagnóstico externo.', -10),
         ('Centralita defectuosa confirmada. Pedido recambio original Komatsu. '
          'ETA: 5-7 días laborables.', -6),
         ('Recambio recibido. Iniciada instalación.', -2),
     ]),
]


# ──────────────────────────────────────────────────────────────────────────────
def seed():
    from datetime import timedelta
    utcnow = datetime.now(timezone.utc)

    with app.app_context():
        # ── Borrar datos existentes (preserva usuarios) ────────────────────
        from sqlalchemy import text
        RepairComment.query.delete()
        RepairOrder.query.delete()
        MachineStatusLog.query.delete()
        DeliveryNoteMachine.query.delete()
        DeliveryNote.query.delete()
        ClientContact.query.delete()
        Client.query.delete()
        Machine.query.delete()
        db.session.commit()

        admin = User.query.first()

        # ── Máquinas ───────────────────────────────────────────────────────
        machine_map = {}
        for code, name, cat, variant, specs, status, deleg in MACHINES:
            m = Machine(code=code, name=name, category=cat, variant=variant,
                        specs=specs, status=status, current_delegacion=deleg,
                        created_at=utcnow)
            db.session.add(m)
            machine_map[code] = m
        db.session.flush()

        # ── Clientes ───────────────────────────────────────────────────────
        client_map = {}
        for code, ctype, name, tax, addr, phone, email, notes in CLIENTS:
            c = Client(client_code=code, client_type=ctype, company_name=name,
                       tax_id=tax, address=addr, phone=phone, email=email,
                       notes=notes, created_at=utcnow)
            db.session.add(c)
            client_map[code] = c
        db.session.flush()

        for client_code, contacts in CONTACTS.items():
            client = client_map[client_code]
            for cname, role, phone, email in contacts:
                db.session.add(ClientContact(
                    client_id=client.id, name=cname, role=role,
                    phone=phone, email=email))
        db.session.flush()

        # ── Albaranes ──────────────────────────────────────────────────────
        for (num, client_code, machine_codes, start, end,
             pmode, prate, punit, total, deleg, location,
             notes_text, created_by, status) in NOTES_DATA:

            created_dt = datetime(start.year, start.month, start.day, 9, 0,
                                  tzinfo=timezone.utc)
            note = DeliveryNote(
                albaran_number=num,
                client_id=client_map[client_code].id,
                rental_start=start,
                rental_end=end,
                pricing_mode=pmode,
                price_rate=prate,
                price_unit=punit,
                total_price=total,
                delegacion=deleg,
                location=location,
                notes=notes_text,
                created_by=created_by,
                status=status,
                created_at=created_dt,
                created_by_id=admin.id if admin else None,
            )
            db.session.add(note)
            db.session.flush()

            for mcode in machine_codes:
                m = machine_map[mcode]
                db.session.add(DeliveryNoteMachine(
                    delivery_note_id=note.id, machine_id=m.id))
                if status == 'active' and m.status == 'occupied':
                    db.session.add(MachineStatusLog(
                        machine_id=m.id,
                        old_status='free',
                        new_status='occupied',
                        delivery_note_id=note.id,
                        changed_by=created_by,
                        changed_at=created_dt,
                    ))

        db.session.flush()

        # ── Partes de reparación ───────────────────────────────────────────
        for (mcode, deleg, desc, est_days, cost, rstatus, res_notes,
             days_ago, comments) in REPAIRS:
            m = machine_map[mcode]
            created_dt = utcnow + timedelta(days=days_ago)
            order = RepairOrder(
                machine_id=m.id,
                delegacion=deleg,
                description=desc,
                estimated_days=est_days,
                cost=cost,
                status=rstatus,
                resolution_notes=res_notes,
                created_at=created_dt,
                created_by_id=admin.id if admin else None,
            )
            db.session.add(order)
            db.session.flush()

            for comment_text, comment_days_ago in comments:
                db.session.add(RepairComment(
                    repair_order_id=order.id,
                    text=comment_text,
                    created_at=utcnow + timedelta(days=comment_days_ago),
                    created_by_id=admin.id if admin else None,
                ))

            # Registrar en el log de estado
            db.session.add(MachineStatusLog(
                machine_id=m.id,
                old_status='free',
                new_status='repair',
                changed_by='Sistema',
                changed_at=created_dt,
            ))

        db.session.commit()

        maq_total = len(MACHINES)
        cli_total = len(CLIENTS)
        alb_total = len(NOTES_DATA)
        alb_activos = sum(1 for n in NOTES_DATA if n[-1] == 'active')
        rep_total = len(REPAIRS)

        print('✓ Base de datos poblada correctamente.')
        print(f'  • {maq_total} máquinas  ({sum(1 for _,_,_,_,_,s,_ in MACHINES if s=="free")} libres, '
              f'{sum(1 for _,_,_,_,_,s,_ in MACHINES if s=="occupied")} ocupadas, '
              f'{sum(1 for _,_,_,_,_,s,_ in MACHINES if s=="repair")} en reparación)')
        print(f'  • {cli_total} clientes')
        print(f'  • {alb_total} albaranes  ({alb_activos} activos, {alb_total-alb_activos} cerrados)')
        print(f'  • {rep_total} partes de reparación')


if __name__ == '__main__':
    seed()
