"""
Populate the database with realistic sample data.
Run once: python seed.py
"""
from app import create_app, db
from app.models import Machine, Client, ClientContact, DeliveryNote, DeliveryNoteMachine, MachineStatusLog
from datetime import date, datetime

app = create_app()

MACHINES = [
    # Aerial Work Platforms — Diesel
    ('AWP-D-001', 'Plataforma tijera diésel 12m',   'AWP', 'D',    'Altura trabajo: 12m | Carga: 450kg | Peso: 5.200kg | Año: 2019'),
    ('AWP-D-002', 'Plataforma tijera diésel 16m',   'AWP', 'D',    'Altura trabajo: 16m | Carga: 450kg | Peso: 6.800kg | Año: 2020'),
    ('AWP-D-003', 'Plataforma articulada diésel 20m','AWP','D',    'Altura trabajo: 20m | Alcance lateral: 9m | Año: 2021'),
    ('AWP-D-004', 'Plataforma articulada diésel 28m','AWP','D',    'Altura trabajo: 28m | Alcance lateral: 16m | Año: 2022'),
    # Aerial Work Platforms — Electric
    ('AWP-E-001', 'Plataforma tijera eléctrica 8m',  'AWP', 'E',   'Altura trabajo: 8m | Carga: 450kg | Interior/exterior | Año: 2021'),
    ('AWP-E-002', 'Plataforma tijera eléctrica 10m', 'AWP', 'E',   'Altura trabajo: 10m | Carga: 450kg | Año: 2022'),
    ('AWP-E-003', 'Plataforma vertical eléctrica 6m','AWP', 'E',   'Altura trabajo: 6m | 1 persona | Compacta | Año: 2023'),
    # Forklifts — Diesel
    ('FLT-D-001', 'Carretilla diésel 3.5T',          'FLT', 'D',   'Capacidad: 3.500kg | Mástil: 4.5m | Año: 2018'),
    ('FLT-D-002', 'Carretilla diésel 5T',             'FLT', 'D',   'Capacidad: 5.000kg | Mástil: 5m | Ruedas neumáticas | Año: 2020'),
    ('FLT-D-003', 'Carretilla diésel 7T',             'FLT', 'D',   'Capacidad: 7.000kg | Mástil: 4m | Uso portuario | Año: 2019'),
    # Forklifts — Electric
    ('FLT-E-001', 'Carretilla eléctrica 2T',          'FLT', 'E',   'Capacidad: 2.000kg | Mástil: 4m | Interior | Año: 2022'),
    ('FLT-E-002', 'Carretilla eléctrica 3T',          'FLT', 'E',   'Capacidad: 3.000kg | Mástil: 5m | Año: 2023'),
    # Dumpers
    ('DMP-3T-001', 'Dúmper articulado 3T',            'DMP', '3T',  'Capacidad: 3.000kg | Tracción 4x4 | Descarga frontal | Año: 2020'),
    ('DMP-6T-001', 'Dúmper articulado 6T',            'DMP', '6T',  'Capacidad: 6.000kg | Tracción 4x4 | Año: 2019'),
    ('DMP-6T-002', 'Dúmper articulado 6T cabina',     'DMP', '6T',  'Capacidad: 6.000kg | Con cabina ROPS/FOPS | Año: 2021'),
    ('DMP-R-3T-001','Dúmper de vía 3T con raíles',   'DMP', 'R-3T','Capacidad: 3.000kg | Apto vía ferroviaria | UIC60 | Año: 2020'),
    ('DMP-R-6T-001','Dúmper de vía 6T con raíles',   'DMP', 'R-6T','Capacidad: 6.000kg | Apto vía ferroviaria | Año: 2018'),
    # Excavators
    ('EXC-3T-001', 'Miniexcavadora 3T',               'EXC', '3T',  'Peso: 3.200kg | Profundidad excav.: 2.5m | Año: 2021'),
    ('EXC-8T-001', 'Excavadora 8T',                   'EXC', '8T',  'Peso: 8.500kg | Profundidad excav.: 4.2m | Año: 2019'),
    ('EXC-20T-001','Excavadora 20T',                  'EXC', '20T', 'Peso: 20.000kg | Profundidad excav.: 6.5m | Año: 2020'),
    # Telescopic Handlers
    ('TLH-17M-001','Manipulador telescópico 17m 3.5T','TLH','17M', 'Altura max: 17m | Capacidad: 3.500kg | Año: 2021'),
    ('TLH-25M-001','Manipulador telescópico 25m 5T',  'TLH','25M', 'Altura max: 25m | Capacidad: 5.000kg | Rotativo | Año: 2022'),
    # Rail Track Hammers
    ('RTH-001',    'Martillo hidráulico de vía',      'RTH', '',    'Para trabajos en vía ferroviaria | Compatible UIC54/60 | Año: 2017'),
    ('RTH-002',    'Martillo neumático de vía pesado','RTH', '',    'Alta potencia | Trabajo continuo | Año: 2019'),
    # Generator Sets
    ('GEN-005K-001','Grupo electrógeno 5kVA',         'GEN', '005K','Potencia: 5kVA | Monofásico | Insonorizado | Año: 2020'),
    ('GEN-020K-001','Grupo electrógeno 20kVA',        'GEN', '020K','Potencia: 20kVA | Trifásico | Año: 2019'),
    ('GEN-045K-001','Grupo electrógeno 45kVA',        'GEN', '045K','Potencia: 45kVA | Trifásico | Remolque | Año: 2021'),
    ('GEN-100K-001','Grupo electrógeno 100kVA',       'GEN', '100K','Potencia: 100kVA | Trifásico | Cabinado | Año: 2020'),
    ('GEN-200K-001','Grupo electrógeno 200kVA',       'GEN', '200K','Potencia: 200kVA | Trifásico | Año: 2018'),
    ('GEN-500K-001','Grupo electrógeno 500kVA',       'GEN', '500K','Potencia: 500kVA | Gran evento / industria | Año: 2022'),
    # Tools
    ('TOL-COMPACTOR-001','Placa compactadora vibrante','TOL','COMPACTOR','Peso: 90kg | Ancho trabajo: 50cm | Gasolina | Año: 2021'),
    ('TOL-PUMP-001',     'Bomba de achique 3"',        'TOL','PUMP',     'Caudal: 1.100 l/min | Altura: 28m | Gasolina | Año: 2020'),
    ('TOL-WELD-001',     'Equipo de soldadura MIG',    'TOL','WELD',     '200A | MIG/MAG | Con carrete y manguera | Año: 2022'),
]

CLIENTS = [
    # (client_code, client_type, company_name, tax_id, address, phone, email, notes)
    ('C-FERRO-001', 'company',    'Ferrovial Construcción S.A.',
     'A-28012345', 'Calle Príncipe de Vergara, 135, 28002 Madrid',
     '+34 91 586 2500', 'alquileres@ferrovial.com',
     'Cliente preferente. Facturación mensual.'),

    ('C-ACCIONA-001', 'company',  'Acciona Infraestructuras S.A.',
     'A-08001234', 'Av. de Europa, 18, 28108 Alcobendas, Madrid',
     '+34 91 663 2850', 'maquinaria@acciona.com',
     'Requieren albaranes firmados en papel.'),

    ('C-GARCIA-001', 'individual','García Martínez, Pedro',
     '12345678A', 'Calle Mayor, 22, 28300 Aranjuez, Madrid',
     '+34 600 111 222', 'pedro.garcia.obras@gmail.com',
     'Autónomo. Pago al contado.'),

    ('C-VIAS-001',   'company',   'Vías y Construcciones S.L.',
     'B-46009876', 'Polígono Industrial Sur, Nave 12, 46190 Valencia',
     '+34 96 312 4500', 'compras@viasyconstrucciones.es',
     'Especialistas en obra ferroviaria. Clientes habituales de dúmperes de vía.'),

    ('C-OBRAS-001',  'company',   'Obras Públicas Levante S.L.U.',
     'B-03098765', 'Av. de Elche, 71, 03008 Alicante',
     '+34 96 510 3300', 'alquiler@obrasnivante.com',
     ''),
]

CONTACTS = {
    'C-FERRO-001':   [('Juan Pérez Ruiz',    'Jefe de compras',   '+34 91 586 2501', 'jperez@ferrovial.com'),
                      ('Laura Sanz',          'Administrativa',    '+34 91 586 2502', 'lsanz@ferrovial.com')],
    'C-ACCIONA-001': [('Roberto Iglesias',    'Responsable flota', '+34 91 663 2851', 'riglesias@acciona.com')],
    'C-GARCIA-001':  [('Pedro García',        'Titular',           '+34 600 111 222', 'pedro.garcia.obras@gmail.com')],
    'C-VIAS-001':    [('María Torres',        'Dirección obra',    '+34 96 312 4501', 'mtorres@viasyconstrucciones.es'),
                      ('Carlos Rueda',        'Técnico',           '+34 645 234 567', 'crueda@viasyconstrucciones.es')],
    'C-OBRAS-001':   [('Antonio Navarro',     'Encargado',         '+34 96 510 3301', 'anavarro@obrasnivante.com')],
}

def seed():
    with app.app_context():
        # Clear existing data
        for Model in [MachineStatusLog, DeliveryNoteMachine, DeliveryNote,
                      ClientContact, Client, Machine]:
            Model.query.delete()
        db.session.commit()

        # ── Machines ──────────────────────────────────────────────────────
        machine_map = {}
        for code, name, cat, variant, specs in MACHINES:
            m = Machine(code=code, name=name, category=cat,
                        variant=variant, specs=specs, status='free')
            db.session.add(m)
            machine_map[code] = m
        db.session.flush()

        # ── Clients ───────────────────────────────────────────────────────
        client_map = {}
        for code, ctype, name, tax, addr, phone, email, notes in CLIENTS:
            c = Client(client_code=code, client_type=ctype, company_name=name,
                       tax_id=tax, address=addr, phone=phone, email=email, notes=notes)
            db.session.add(c)
            client_map[code] = c
        db.session.flush()

        for client_code, contacts in CONTACTS.items():
            client = client_map[client_code]
            for cname, role, phone, email in contacts:
                db.session.add(ClientContact(
                    client_id=client.id, name=cname, role=role, phone=phone, email=email))

        db.session.flush()

        # ── Delivery notes ────────────────────────────────────────────────
        notes_data = [
            # (albaran_no, client_code, machine_codes, start, end, pricing_mode,
            #  price_rate, price_unit, total_price, location, notes, created_by, status)
            ('ALB-2026-0001', 'C-FERRO-001',
             ['AWP-D-003', 'GEN-045K-001'],
             date(2026, 1, 10), date(2026, 3, 10),
             'closed', None, None, 18500.0,
             'Viaducto M-50, Madrid', 'Incluye transporte y montaje.', 'Ana López', 'closed'),

            ('ALB-2026-0002', 'C-ACCIONA-001',
             ['EXC-20T-001'],
             date(2026, 2, 1), date(2026, 4, 30),
             'open', 450.0, 'day', None,
             'AVE Tramo Murcia-Almería', '', 'Carlos Vega', 'closed'),

            ('ALB-2026-0003', 'C-VIAS-001',
             ['DMP-R-3T-001', 'DMP-R-6T-001', 'RTH-001'],
             date(2026, 3, 15), None,
             'open', 1200.0, 'week', None,
             'Renovación vía Renfe — Albacete', 'Material ferroviario. Permisos adjuntos.', 'Ana López', 'active'),

            ('ALB-2026-0004', 'C-GARCIA-001',
             ['FLT-D-001'],
             date(2026, 4, 1), date(2026, 4, 30),
             'closed', None, None, 1400.0,
             'Nave industrial polígono Cobo Calleja', '', 'Marcos Torres', 'closed'),

            ('ALB-2026-0005', 'C-OBRAS-001',
             ['AWP-E-002', 'GEN-020K-001'],
             date(2026, 4, 15), None,
             'open', 180.0, 'day', None,
             'Rehabilitación fachada C/ Mayor 14, Alicante', '', 'Ana López', 'active'),

            ('ALB-2026-0006', 'C-ACCIONA-001',
             ['TLH-25M-001', 'GEN-100K-001'],
             date(2026, 5, 1), None,
             'open', 3200.0, 'week', None,
             'Parque eólico Sierra Nevada', 'Acceso especial. Camión grúa necesario.', 'Carlos Vega', 'active'),

            ('ALB-2026-0007', 'C-FERRO-001',
             ['AWP-D-004'],
             date(2026, 5, 5), None,
             'closed', None, None, 7200.0,
             'Puente sobre el Tajo, Toledo', '', 'Ana López', 'active'),

            ('ALB-2026-0008', 'C-VIAS-001',
             ['RTH-002', 'DMP-R-3T-001'],
             date(2026, 1, 20), date(2026, 2, 20),
             'open', 950.0, 'week', 3800.0,
             'Mantenimiento vía Cercanías Madrid', '', 'Marcos Torres', 'closed'),

            ('ALB-2026-0009', 'C-GARCIA-001',
             ['TOL-COMPACTOR-001', 'TOL-PUMP-001'],
             date(2026, 5, 8), None,
             'open', 65.0, 'day', None,
             'Urbanización Los Pinos, Aranjuez', '', 'Marcos Torres', 'active'),

            ('ALB-2026-0010', 'C-OBRAS-001',
             ['EXC-3T-001', 'DMP-3T-001'],
             date(2026, 5, 2), date(2026, 5, 31),
             'closed', None, None, 4800.0,
             'Canalización aguas pluviales Alicante', '', 'Ana López', 'active'),
        ]

        for (num, client_code, machine_codes, start, end,
             pmode, prate, punit, total, location, notes_text, created_by, status) in notes_data:

            note = DeliveryNote(
                albaran_number=num,
                client_id=client_map[client_code].id,
                rental_start=start,
                rental_end=end,
                pricing_mode=pmode,
                price_rate=prate,
                price_unit=punit,
                total_price=total,
                location=location,
                notes=notes_text,
                created_by=created_by,
                status=status,
                created_at=datetime(2026, start.month, start.day, 9, 0),
            )
            db.session.add(note)
            db.session.flush()

            for mcode in machine_codes:
                m = machine_map[mcode]
                db.session.add(DeliveryNoteMachine(
                    delivery_note_id=note.id, machine_id=m.id))
                if status == 'active':
                    old = m.status
                    m.status = 'occupied'
                    db.session.add(MachineStatusLog(
                        machine_id=m.id, old_status=old, new_status='occupied',
                        delivery_note_id=note.id, changed_by=created_by,
                        changed_at=datetime(2026, start.month, start.day, 9, 0),
                    ))

        db.session.commit()
        print("✓ Base de datos poblada correctamente.")
        print(f"  • {len(MACHINES)} máquinas")
        print(f"  • {len(CLIENTS)} clientes")
        print(f"  • {len(notes_data)} albaranes")

if __name__ == '__main__':
    seed()
