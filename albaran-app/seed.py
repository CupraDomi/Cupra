"""
Datos de demostración: clientes, albaranes y partes de reparación.
Las máquinas las genera seed-machines (ya existente en run.py).
Ejecutar vía: flask seed-demo  (con SEED_DEMO=1)
"""
from datetime import date, datetime, timedelta, timezone
from app import db
from app.models import (Machine, MachineStatusLog, Client, ClientContact,
                        DeliveryNote, DeliveryNoteMachine, RepairOrder, RepairComment)
from app.auth.models import User


# ──────────────────────────────────────────────────────────────────────────────
# CLIENTES
# ──────────────────────────────────────────────────────────────────────────────
CLIENTS = [
    ('C-FERRO-001',   'company',    'Ferrovial Construcción S.A.',
     'A-28012345', 'Calle Príncipe de Vergara, 135, 28002 Madrid',
     '+34 91 586 2500', 'alquileres@ferrovial.com',
     'Cliente preferente. Facturación mensual. Requieren albarán firmado.'),
    ('C-ACCIONA-001', 'company',    'Acciona Infraestructuras S.A.',
     'A-08001234', 'Av. de Europa, 18, 28108 Alcobendas, Madrid',
     '+34 91 663 2850', 'maquinaria@acciona.com',
     'Obras de infraestructuras. Pago a 60 días.'),
    ('C-VIAS-001',    'company',    'Vías y Construcciones S.L.',
     'B-46009876', 'Polígono Industrial Sur, Nave 12, 46190 Valencia',
     '+34 96 312 4500', 'compras@viasyconstrucciones.es',
     'Especialistas en obra ferroviaria. Habituales de dúmperes de vía y RTH.'),
    ('C-SACYR-001',   'company',    'Sacyr Construcción S.A.U.',
     'A-78976395', 'Paseo de la Castellana, 83-85, 28046 Madrid',
     '+34 91 545 5000', 'flota@sacyr.com',
     'Grandes proyectos de infraestructura. Contratos marco anuales.'),
    ('C-ORTIZ-001',   'company',    'Constructora San José S.A.',
     'A-14045678', 'Av. de la Innovación, 1, 14014 Córdoba',
     '+34 957 400 200', 'compras@ortiz-construccion.es',
     'Cliente local. Obras en la provincia de Córdoba principalmente.'),
    ('C-GARCIA-001',  'individual', 'García Martínez, Pedro',
     '12345678A', 'Calle Mayor, 22, 14900 Lucena, Córdoba',
     '+34 600 111 222', 'pedro.garcia.obras@gmail.com',
     'Autónomo. Obras menores. Pago al contado.'),
    ('C-RUBIO-001',   'individual', 'Rubio Fernández, Antonio',
     '87654321B', 'C/ Tendillas, 5, 14001 Córdoba',
     '+34 650 333 444', 'antonio.rubio@gmail.com',
     'Pequeñas obras de reforma. Alquileres de corta duración.'),
    ('C-MALAGA-001',  'company',    'Málaga Obras y Servicios S.L.',
     'B-29098765', 'Polígono El Viso, Nave 3, 29006 Málaga',
     '+34 95 232 5100', 'operaciones@malagaobras.es',
     'Obras de urbanización en Costa del Sol.'),
    ('C-HISPANIA-001','company',    'Hispania Infraestructuras S.L.',
     'B-41023456', 'Calle Resolana, 50, 41009 Sevilla',
     '+34 95 491 2300', 'alquileres@hispania-infra.es',
     'Proyectos de saneamiento en Andalucía occidental.'),
    ('C-INGEOBRA-001','company',    'Ingeobra Andalucía S.L.',
     'B-14078901', 'Av. del Brillante, 89, 14012 Córdoba',
     '+34 957 265 300', 'ingenieria@ingeobra.es',
     'Ingeniería y construcción. Cliente desde 2019.'),
    ('C-PORTGRA-001', 'company',    'Portgranada S.L.',
     'B-18056789', 'Polígono PISA, Av. de la Ciencia, 18, 18015 Granada',
     '+34 958 400 100', 'logistica@portgranada.es',
     'Logística y almacenaje. Alquiler habitual de carretillas.'),
    ('C-CADIZ-001',   'company',    'Bahía Obras y Reformas S.L.',
     'B-11034567', 'Polígono Las Aletas, Nave 7, 11510 Puerto Real, Cádiz',
     '+34 956 201 400', 'obras@bahiareformas.es',
     'Construcción naval y obras portuarias.'),
    ('C-ENRESA-001',  'company',    'Enresa Proyectos Industriales S.A.',
     'A-14056789', 'Av. de la Electrónica, 33, 14014 Córdoba',
     '+34 957 190 500', 'proyectos@enresa-industrial.es',
     'Sector industrial. Montajes en fábrica.'),
    ('C-RENOVAB-001', 'company',    'Renovables Betis S.L.',
     'B-41067890', 'C/ Antonio Bienvenida, 12, 41009 Sevilla',
     '+34 95 477 3300', 'operaciones@renovablesbetis.es',
     'Instalación de parques eólicos y fotovoltaicos en Andalucía.'),
    ('C-JAENCON-001', 'company',    'Construcciones Úbeda S.L.',
     'B-23045678', 'Polígono Los Olivares, Nave 14, 23400 Úbeda, Jaén',
     '+34 953 750 200', 'compras@construcciones-ubeda.es',
     'Obras en la provincia de Jaén. Clientes habituales de RTH.'),
]

CONTACTS = {
    'C-FERRO-001':   [('Juan Pérez Ruiz',   'Jefe de compras',     '+34 91 586 2501', 'jperez@ferrovial.com'),
                      ('Laura Sanz',         'Administrativa',      '+34 91 586 2502', 'lsanz@ferrovial.com')],
    'C-ACCIONA-001': [('Roberto Iglesias',   'Responsable flota',  '+34 91 663 2851', 'riglesias@acciona.com'),
                      ('Mónica Ruiz',        'Técnica de obra',    '+34 650 789 012', 'mruiz@acciona.com')],
    'C-VIAS-001':    [('María Torres',       'Dirección obra',     '+34 96 312 4501', 'mtorres@viasyconstrucciones.es'),
                      ('Carlos Rueda',       'Técnico ferroviario','+34 645 234 567', 'crueda@viasyconstrucciones.es')],
    'C-SACYR-001':   [('Ignacio Molina',     'Resp. maquinaria',   '+34 91 545 5010', 'imolina@sacyr.com')],
    'C-ORTIZ-001':   [('Francisco Ortiz',    'Gerente',            '+34 957 400 201', 'fortiz@ortiz-construccion.es'),
                      ('Ana Herrera',        'Administrativa',     '+34 957 400 202', 'aherrera@ortiz-construccion.es')],
    'C-GARCIA-001':  [('Pedro García',       'Titular',            '+34 600 111 222', 'pedro.garcia.obras@gmail.com')],
    'C-RUBIO-001':   [('Antonio Rubio',      'Titular',            '+34 650 333 444', 'antonio.rubio@gmail.com')],
    'C-MALAGA-001':  [('Jesús Moreno',       'Jefe de obra',       '+34 95 232 5101', 'jmoreno@malagaobras.es'),
                      ('Carmen Jiménez',     'Compras',            '+34 600 456 789', 'cjimenez@malagaobras.es')],
    'C-HISPANIA-001':[('Diego Castillo',     'Director técnico',   '+34 95 491 2301', 'dcastillo@hispania-infra.es')],
    'C-INGEOBRA-001':[('Miguel Ángel Reyes', 'Responsable flota',  '+34 957 265 301', 'mreyes@ingeobra.es'),
                      ('Cristina López',     'Administración',     '+34 670 234 567', 'clopez@ingeobra.es')],
    'C-PORTGRA-001': [('Salvador Gómez',     'Jefe de almacén',    '+34 958 400 101', 'sgomez@portgranada.es')],
    'C-CADIZ-001':   [('Ramón Díaz',         'Encargado',          '+34 956 201 401', 'rdiaz@bahiareformas.es')],
    'C-ENRESA-001':  [('Alberto Sánchez',    'Ing. de proyectos',  '+34 957 190 501', 'asanchez@enresa-industrial.es')],
    'C-RENOVAB-001': [('Patricia Medina',    'Resp. operaciones',  '+34 95 477 3301', 'pmedina@renovablesbetis.es'),
                      ('Javier Luna',        'Técnico eólico',     '+34 680 123 456', 'jluna@renovablesbetis.es')],
    'C-JAENCON-001': [('Eduardo Palma',      'Encargado obra',     '+34 953 750 201', 'epalma@construcciones-ubeda.es')],
}


# ──────────────────────────────────────────────────────────────────────────────
# ALBARANES
# Se referencian máquinas por categoría+variante+número → se buscan dinámicamente
# ──────────────────────────────────────────────────────────────────────────────
# (num, client_code, machine_codes[], start, end,
#  pricing_mode, price_rate, price_unit, total_price,
#  delegacion, location, notes, created_by, status)

NOTES_DATA = [
    # ── Cerrados (histórico 2025) ────────────────────────────────────────────
    ('ALB-2025-0001', 'C-FERRO-001',
     ['AWP-AD20-001', 'GEN-045KVA-001'],
     date(2025, 9, 1), date(2025, 11, 30),
     'closed', None, None, 22500.0,
     'Córdoba', 'Viaducto A-45, tramo Córdoba Norte',
     'Incluye transporte y montaje.', 'Ana López', 'closed'),

    ('ALB-2025-0002', 'C-ACCIONA-001',
     ['EXC-G200-001'],
     date(2025, 10, 1), date(2025, 12, 15),
     'open', 450.0, 'day', None,
     'Sevilla', 'AVE Tramo Sevilla-Antequera',
     '', 'Carlos Vega', 'closed'),

    ('ALB-2025-0003', 'C-VIAS-001',
     ['DMP-V30-001', 'DMP-V60-001', 'RTH-H085-001'],
     date(2025, 11, 1), date(2026, 1, 31),
     'open', 1200.0, 'week', None,
     'Jaén', 'Renovación vía Renfe — tramo Jaén-Linares',
     'Permisos ADIF adjuntos.', 'Ana López', 'closed'),

    ('ALB-2025-0004', 'C-GARCIA-001',
     ['FLT-CD30-001'],
     date(2025, 11, 10), date(2025, 11, 30),
     'closed', None, None, 1100.0,
     'Córdoba', 'Nave industrial Polígono Las Quemadas, Córdoba',
     '', 'Marcos Torres', 'closed'),

    ('ALB-2025-0005', 'C-MALAGA-001',
     ['AWP-TE12-001', 'GEN-020KVA-001'],
     date(2025, 12, 1), date(2026, 1, 15),
     'open', 195.0, 'day', None,
     'Málaga', 'Rehabilitación fachada, Paseo del Limonar, Málaga',
     '', 'Ana López', 'closed'),

    ('ALB-2025-0006', 'C-SACYR-001',
     ['TLH-R25-001', 'GEN-100KVA-001'],
     date(2025, 10, 15), date(2025, 12, 31),
     'open', 3200.0, 'week', None,
     'Granada', 'Parque eólico Sierra de Baza',
     'Acceso especial. Camión grúa necesario.', 'Carlos Vega', 'closed'),

    ('ALB-2026-0001', 'C-VIAS-001',
     ['RTH-H120-001', 'DMP-V90-001'],
     date(2026, 1, 15), date(2026, 3, 15),
     'open', 980.0, 'week', None,
     'Jaén', 'Mantenimiento vía Cercanías Jaén',
     '', 'Marcos Torres', 'closed'),

    ('ALB-2026-0002', 'C-ORTIZ-001',
     ['EXC-ME50-001', 'DMP-A30-001'],
     date(2026, 2, 1), date(2026, 3, 31),
     'closed', None, None, 8600.0,
     'Córdoba', 'Canalización pluviales — C/ Cronista Rey Díaz, Córdoba',
     '', 'Ana López', 'closed'),

    ('ALB-2026-0003', 'C-CADIZ-001',
     ['FLT-CD50-001'],
     date(2026, 2, 10), date(2026, 3, 10),
     'open', 220.0, 'day', None,
     'Cádiz', 'Astilleros Cádiz, zona de carga',
     '', 'Carlos Vega', 'closed'),

    ('ALB-2026-0004', 'C-GARCIA-001',
     ['TOL-CBT-001', 'TOL-BBA-001'],
     date(2026, 3, 5), date(2026, 3, 25),
     'open', 75.0, 'day', None,
     'Córdoba', 'Urbanización Los Pinos, Lucena',
     '', 'Marcos Torres', 'closed'),

    ('ALB-2026-0005', 'C-PORTGRA-001',
     ['FLT-CE20-001'],
     date(2026, 3, 1), date(2026, 4, 30),
     'open', 85.0, 'day', None,
     'Granada', 'Almacén logístico, Polígono PISA, Granada',
     'Uso en interior.', 'Ana López', 'closed'),

    ('ALB-2026-0006', 'C-HISPANIA-001',
     ['EXC-ME80-001', 'DMP-V60-002'],
     date(2026, 3, 15), date(2026, 5, 15),
     'closed', None, None, 14200.0,
     'Málaga', 'Obra de saneamiento — Polígono El Viso, Vélez-Málaga',
     '', 'Carlos Vega', 'closed'),

    ('ALB-2026-0007', 'C-RUBIO-001',
     ['AWP-TE06-001'],
     date(2026, 4, 1), date(2026, 4, 15),
     'closed', None, None, 680.0,
     'Córdoba', 'Reforma local C/ Cruz Conde, Córdoba',
     '', 'Marcos Torres', 'closed'),

    ('ALB-2026-0008', 'C-ENRESA-001',
     ['FLT-RE20-001', 'TOL-VIB-001'],
     date(2026, 4, 7), date(2026, 4, 30),
     'open', 130.0, 'day', None,
     'Córdoba', 'Planta industrial Almogávares, Córdoba',
     'Montaje de estructura metálica.', 'Ana López', 'closed'),

    # ── Activos ──────────────────────────────────────────────────────────────
    ('ALB-2026-0009', 'C-FERRO-001',
     ['AWP-AD33-001'],
     date(2026, 5, 2), None,
     'closed', None, None, 9800.0,
     'Granada', 'Puente sobre el Genil — A-92, Granada',
     '', 'Ana López', 'active'),

    ('ALB-2026-0010', 'C-ACCIONA-001',
     ['TLH-R20-001', 'GEN-045KVA-002'],
     date(2026, 5, 5), None,
     'open', 2800.0, 'week', None,
     'Sevilla', 'Parque eólico Alcalá de Guadaíra',
     'Requiere grúa de acompañamiento.', 'Carlos Vega', 'active'),

    ('ALB-2026-0011', 'C-VIAS-001',
     ['DMP-V30-002', 'RTH-H085-002', 'RTH-H120-002'],
     date(2026, 5, 6), None,
     'open', 1450.0, 'week', None,
     'Jaén', 'Renovación vía Jaén-Úbeda, PK 12-28',
     'ADIF: expediente 2026-JA-018.', 'Marcos Torres', 'active'),

    ('ALB-2026-0012', 'C-ORTIZ-001',
     ['EXC-M30-001'],
     date(2026, 5, 8), None,
     'open', 185.0, 'day', None,
     'Cádiz', 'Urbanización El Puerto, El Puerto de Santa María',
     '', 'Ana López', 'active'),

    ('ALB-2026-0013', 'C-JAENCON-001',
     ['DMP-V60-003', 'RTH-H150-001'],
     date(2026, 5, 9), None,
     'open', 900.0, 'week', None,
     'Jaén', 'Mantenimiento vías, zona Úbeda-Baeza',
     'Coordinación con ADIF zona sur.', 'Carlos Vega', 'active'),

    ('ALB-2026-0014', 'C-RENOVAB-001',
     ['TLH-R25-002', 'GEN-100KVA-002'],
     date(2026, 5, 3), None,
     'open', 3500.0, 'week', None,
     'Granada', 'Parque eólico Baza-Norte, Fase II',
     'Incluye operador.', 'Ana López', 'active'),

    ('ALB-2026-0015', 'C-INGEOBRA-001',
     ['AWP-TD12-001'],
     date(2026, 5, 7), None,
     'open', 280.0, 'day', None,
     'Sevilla', 'Rehabilitación puente C/ Resolana, Sevilla',
     '', 'Marcos Torres', 'active'),

    ('ALB-2026-0016', 'C-HISPANIA-001',
     ['EXC-ME80-002'],
     date(2026, 5, 10), None,
     'open', 380.0, 'day', None,
     'Málaga', 'Ampliación red saneamiento — Estepona',
     '', 'Carlos Vega', 'active'),

    ('ALB-2026-0017', 'C-CADIZ-001',
     ['FLT-CD25-001'],
     date(2026, 5, 12), None,
     'open', 175.0, 'day', None,
     'Sevilla', 'Puerto de Sevilla, zona de contenedores',
     '', 'Ana López', 'active'),

    ('ALB-2026-0018', 'C-PORTGRA-001',
     ['FLT-CE15-001', 'FLT-AP15-001'],
     date(2026, 5, 5), None,
     'open', 145.0, 'day', None,
     'Granada', 'Centro logístico Amazon, Zona Franca Granada',
     'Dos turnos.', 'Marcos Torres', 'active'),

    ('ALB-2026-0019', 'C-SACYR-001',
     ['AWP-TE10-001', 'GEN-010KVA-001'],
     date(2026, 5, 13), None,
     'open', 210.0, 'day', None,
     'Cádiz', 'Rehabilitación fachada histórica — Cádiz centro',
     '', 'Ana López', 'active'),

    ('ALB-2026-0020', 'C-RUBIO-001',
     ['TOL-MTH-001'],
     date(2026, 5, 14), None,
     'open', 55.0, 'day', None,
     'Jaén', 'Reforma interior C/ Fuente Nueva, Jaén',
     '', 'Carlos Vega', 'active'),
]


# ──────────────────────────────────────────────────────────────────────────────
# PARTES DE REPARACIÓN (para máquinas que estén en status='repair')
# ──────────────────────────────────────────────────────────────────────────────
# Se asignarán a las primeras máquinas en repair que se encuentren por categoría
REPAIR_DESCRIPTIONS = [
    ('AWP', 'Fallo en el sistema hidráulico: pérdida de presión en cilindro del brazo articulado. '
            'La plataforma no alcanza la altura máxima de trabajo.', 7,
     [('Revisado sistema hidráulico. Detectada rotura en retén del cilindro. '
       'Pedido repuesto al proveedor (JLG Parts). ETA: 3-4 días.', -4),
      ('Recibidos retenedores. Iniciada sustitución.', -1)]),

    ('FLT', 'Tracción trasera sin respuesta. Probable fallo en diferencial trasero '
            'o en la transmisión hidrostática.', 10,
     [('Diagnóstico inicial: se descarta el diferencial. Problema en bomba hidrostática. '
       'Consultado con taller externo especializado.', -7),
      ('Taller externo confirma fallo en bomba. Presupuesto: 2.800 €. '
       'Pendiente aprobación de dirección.', -3)]),

    ('EXC', 'Motor no arranca. Avería eléctrica: posible fallo en centralita de motor '
            'o solenoide de arranque.', 5,
     [('Comprobado solenoide — OK. Centralita enviada a diagnóstico externo.', -10),
      ('Centralita defectuosa confirmada. Pedido recambio original. ETA: 5-7 días.', -6),
      ('Recambio recibido. Iniciada instalación.', -2)]),

    ('GEN', 'Grupo electrógeno no da tensión en bornes de salida. '
            'Posible fallo en alternador o regulador de voltaje.', 4,
     [('Medida tensión en campo del alternador — sin excitación. '
       'Regulador de voltaje averiado. Unidad de repuesto solicitada.', -3)]),

    ('TLH', 'Brazo telescópico no se extiende completamente. '
            'Fuga interna en cilindro de extensión.', 6,
     [('Desmontado cilindro. Confirmada rotura de junta interior. '
       'Enviado a taller hidráulico externo para rectificado.', -5),
      ('Cilindro listo. Reinstalación prevista para mañana.', -1)]),
]


# ──────────────────────────────────────────────────────────────────────────────
def seed():
    """Carga clientes, albaranes y partes de reparación sobre las máquinas existentes."""
    utcnow = datetime.now(timezone.utc)

    # ── Limpiar datos anteriores (preserva máquinas y usuarios) ───────────────
    RepairComment.query.delete()
    RepairOrder.query.delete()
    MachineStatusLog.query.delete()
    DeliveryNoteMachine.query.delete()
    DeliveryNote.query.delete()
    ClientContact.query.delete()
    Client.query.delete()
    db.session.commit()

    # Resetear máquinas ocupadas/reparación a libre (se reasignarán)
    Machine.query.filter(Machine.status.in_(['occupied', 'reserved'])).update(
        {'status': 'free'}, synchronize_session=False)
    db.session.commit()

    admin = User.query.first()

    # ── Clientes ───────────────────────────────────────────────────────────────
    client_map = {}
    for code, ctype, name, tax, addr, phone, email, notes in CLIENTS:
        c = Client(client_code=code, client_type=ctype, company_name=name,
                   tax_id=tax, address=addr, phone=phone, email=email,
                   notes=notes, created_at=utcnow,
                   created_by_id=admin.id if admin else None)
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

    # ── Albaranes ──────────────────────────────────────────────────────────────
    all_machines = {m.code: m for m in Machine.query.all()}

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
            m = all_machines.get(mcode)
            if m is None:
                # Si el código exacto no existe, buscar la primera de esa categoría/variante libre
                parts = mcode.split('-')
                cat = parts[0]
                var = parts[1] if len(parts) > 1 else ''
                m = Machine.query.filter_by(
                    category=cat, variant=var, status='free').first()
            if m is None:
                continue

            db.session.add(DeliveryNoteMachine(
                delivery_note_id=note.id, machine_id=m.id))

            if status == 'active':
                old_status = m.status
                m.status = 'occupied'
                m.current_delegacion = deleg
                db.session.add(MachineStatusLog(
                    machine_id=m.id,
                    old_status=old_status,
                    new_status='occupied',
                    delivery_note_id=note.id,
                    changed_by=created_by,
                    changed_at=created_dt,
                ))

        db.session.flush()

    # ── Partes de reparación ───────────────────────────────────────────────────
    delegaciones = ['Córdoba', 'Málaga', 'Sevilla', 'Cádiz', 'Jaén', 'Granada']
    repair_machines = Machine.query.filter_by(status='repair').all()
    repair_machines_by_cat = {}
    for m in repair_machines:
        repair_machines_by_cat.setdefault(m.category, []).append(m)

    for i, (cat, desc, est_days, comments) in enumerate(REPAIR_DESCRIPTIONS):
        machines_in_cat = repair_machines_by_cat.get(cat, [])
        if not machines_in_cat:
            # Tomar cualquier máquina libre y ponerla en reparación
            m = Machine.query.filter_by(status='free').first()
            if m is None:
                continue
            m.status = 'repair'
            m.repair_notes = desc
            db.session.flush()
        else:
            m = machines_in_cat[i % len(machines_in_cat)]

        deleg = delegaciones[i % len(delegaciones)]
        created_dt = utcnow + timedelta(days=-(12 - i * 2))

        order = RepairOrder(
            machine_id=m.id,
            delegacion=deleg,
            description=desc,
            estimated_days=est_days,
            status='open',
            created_at=created_dt,
            created_by_id=admin.id if admin else None,
        )
        db.session.add(order)
        db.session.flush()

        for comment_text, days_ago in comments:
            db.session.add(RepairComment(
                repair_order_id=order.id,
                text=comment_text,
                created_at=utcnow + timedelta(days=days_ago),
                created_by_id=admin.id if admin else None,
            ))

        db.session.add(MachineStatusLog(
            machine_id=m.id,
            old_status='free',
            new_status='repair',
            changed_by='Sistema demo',
            changed_at=created_dt,
        ))

    db.session.commit()

    total_m    = Machine.query.count()
    total_c    = Client.query.count()
    total_a    = DeliveryNote.query.count()
    total_actv = DeliveryNote.query.filter_by(status='active').count()
    total_r    = RepairOrder.query.count()

    print('✓ Datos de demo cargados correctamente.')
    print(f'  • {total_m} máquinas (preexistentes del seed-machines)')
    print(f'  • {total_c} clientes')
    print(f'  • {total_a} albaranes  ({total_actv} activos, {total_a - total_actv} cerrados)')
    print(f'  • {total_r} partes de reparación')
