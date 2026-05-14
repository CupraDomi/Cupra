import os
import click
from app import create_app, db

app = create_app()


@app.cli.command('seed-admin-env')
def seed_admin_env():
    """Crea el admin leyendo ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_FULLNAME.
    Si ya existe algún usuario, no hace nada (seguro para redeploys)."""
    from app.auth.models import User
    password = os.environ.get('ADMIN_PASSWORD')
    if not password:
        click.echo('ADMIN_PASSWORD no definida — saltando creación de admin.')
        return
    if User.query.first():
        click.echo('Ya existen usuarios — saltando seed.')
        return
    username  = os.environ.get('ADMIN_USERNAME', 'admin')
    full_name = os.environ.get('ADMIN_FULLNAME', 'Administrador')
    user = User(username=username, full_name=full_name,
                role='jefe', must_change_password=False)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.secho(f'✓ Usuario "{username}" creado con rol jefe.', fg='green')


@app.cli.command('seed-demo')
def seed_demo():
    """Carga datos de demostración (máquinas, clientes, albaranes, reparaciones).
    Solo actúa si la variable de entorno SEED_DEMO=1 está definida."""
    if os.environ.get('SEED_DEMO') != '1':
        click.echo('SEED_DEMO != 1 — saltando carga de datos de demo.')
        return
    click.echo('Cargando datos de demostración...')
    import seed as seed_module
    seed_module.seed()


@app.cli.command('seed-admin')
@click.option('--username', default='admin', show_default=True)
@click.option('--password', default='cambiar_ahora', show_default=True)
@click.option('--full-name', default='Administrador', show_default=True)
def seed_admin(username, password, full_name):
    """Crea el primer usuario jefe si no existe ninguno todavía."""
    from app.auth.models import User
    if User.query.first():
        click.echo('Ya existen usuarios en la base de datos. Abortando.', err=True)
        raise SystemExit(1)
    user = User(username=username, full_name=full_name, role='jefe', must_change_password=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.secho(f'✓ Usuario "{username}" creado con rol jefe.', fg='green')
    click.secho(f'  Contraseña inicial: {password}', fg='yellow')


@app.cli.command('seed-workers')
def seed_workers():
    """Crea trabajadores de prueba si no existen ya."""
    from app.auth.models import User
    workers = [
        ('david',    'David García',    'Córdoba'),
        ('patricio', 'Patricio Ruiz',   'Málaga'),
        ('diego',    'Diego Fernández', 'Sevilla'),
        ('ana',      'Ana Martínez',    'Cádiz'),
        ('luis',     'Luis Sánchez',    'Jaén'),
    ]
    created = 0
    for username, full_name, delegacion in workers:
        if User.query.filter_by(username=username).first():
            continue
        u = User(username=username, full_name=full_name, role='worker',
                 delegacion=delegacion, must_change_password=True)
        u.set_password('trabajador1234')
        db.session.add(u)
        created += 1
    db.session.commit()
    click.secho(f'✓ {created} trabajadores creados (contraseña: trabajador1234).', fg='green')


@app.cli.command('seed-machines')
@click.option('--clear', is_flag=True, help='Eliminar todas las máquinas existentes antes de sembrar.')
def seed_machines(clear):
    """Poblar la base de datos hasta ~400 máquinas de flota realistas."""
    from app.models import Machine

    if clear:
        n = Machine.query.delete()
        db.session.commit()
        click.echo(f'  {n} máquinas eliminadas.')

    existing = {m.code for m in Machine.query.with_entities(Machine.code).all()}

    REPAIR_NOTES = [
        'Fallo en el sistema hidráulico. Pendiente de revisión por técnico.',
        'Motor de elevación averiado. En espera de piezas de recambio.',
        'Batería en mal estado, no mantiene carga. Pedido de baterías realizado.',
        'Fuga de aceite hidráulico en manguera superior. Manguera en pedido.',
        'Sistema eléctrico con cortocircuito en cuadro de mandos. En diagnóstico.',
        'Neumático trasero dañado por objeto cortante en obra. Pendiente sustitución.',
        'Freno de servicio con desgaste excesivo. Revisión urgente en taller.',
        'Alarma de inclinación defectuosa, activación errónea constante.',
        'Daños en barandilla de plataforma de trabajo. Reparación de soldadura.',
        'Motor diésel con sobrecalentamiento. Revisión del circuito de refrigeración.',
        'Cilindro de extensión del brazo con pérdida de presión.',
        'Cargador de baterías defectuoso. Unidad de sustitución en camino.',
        'Sensor de carga averiado — bloqueo de seguridad permanente activo.',
        'Caja de cambios con ruidos anómalos en marcha atrás. En diagnóstico.',
        'Bomba hidráulica con cavitación. Desmontaje y revisión en taller.',
        'Turbocompresor averiado. Pendiente de presupuesto del fabricante.',
        'Control remoto dañado por caída en obra. Unidad de recambio solicitada.',
        'Correa de distribución en mal estado. Cambio programado esta semana.',
        'Eje de transmisión con juego excesivo. Revisión en taller propio.',
        'Filtros de aire y combustible colmatados. Sustitución y limpieza en curso.',
    ]

    # Distribución de estados: 70% libre, 20% ocupada, 7% reparación, 3% reservada
    STATUS_PATTERN = (
        ['free'] * 70 + ['occupied'] * 20 + ['repair'] * 7 + ['reserved'] * 3
    )

    total_created = 0
    repair_idx = 0

    def add_batch(category, variant, name, specs, count):
        nonlocal total_created, repair_idx
        created_in_batch = 0
        for i in range(1, count + 1):
            code = f'{category}-{variant}-{i:03d}'
            if code in existing:
                continue
            pos = (total_created + i) % 100
            status = STATUS_PATTERN[pos]
            rn = None
            if status == 'repair':
                rn = REPAIR_NOTES[repair_idx % len(REPAIR_NOTES)]
                repair_idx += 1
            db.session.add(Machine(
                code=code, name=name, category=category,
                variant=variant, specs=specs, status=status, repair_notes=rn,
            ))
            created_in_batch += 1
        total_created += created_in_batch

    # ── AWP — Plataformas Elevadoras (100) ──────────────────────────────────

    # Tijeras Eléctricas (40)
    add_batch('AWP','TE06','Plataforma Tijera Eléctrica 6m',
        'Altura trab.: 6 m | Cap.: 230 kg | Ancho plat.: 0,75 m | Peso: 1.200 kg\nAlimentación: Eléctrica 24 V | Uso interior',5)
    add_batch('AWP','TE08','Plataforma Tijera Eléctrica 8m',
        'Altura trab.: 8 m | Cap.: 230 kg | Ancho plat.: 1,14 m | Peso: 2.100 kg\nAlimentación: Eléctrica 24 V | Uso interior',6)
    add_batch('AWP','TE10','Plataforma Tijera Eléctrica 10m',
        'Altura trab.: 10 m | Cap.: 230 kg | Ancho plat.: 1,14 m | Peso: 2.400 kg\nAlimentación: Eléctrica 24 V | Interior/Exterior',6)
    add_batch('AWP','TE12','Plataforma Tijera Eléctrica 12m',
        'Altura trab.: 12 m | Cap.: 450 kg | Ancho plat.: 1,16 m | Peso: 3.200 kg\nAlimentación: Eléctrica 48 V | Exterior terreno firme',7)
    add_batch('AWP','TE14','Plataforma Tijera Eléctrica 14m',
        'Altura trab.: 14 m | Cap.: 450 kg | Ancho plat.: 1,52 m | Peso: 4.100 kg\nAlimentación: Eléctrica 48 V | Exterior',6)
    add_batch('AWP','TE16','Plataforma Tijera Eléctrica 16m',
        'Altura trab.: 16 m | Cap.: 450 kg | Ancho plat.: 1,52 m | Peso: 5.200 kg\nAlimentación: Eléctrica 48 V | Gran capacidad exterior',5)
    add_batch('AWP','TE18','Plataforma Tijera Eléctrica 18m',
        'Altura trab.: 18 m | Cap.: 680 kg | Ancho plat.: 1,83 m | Peso: 6.800 kg\nAlimentación: Eléctrica 48 V | Gran plataforma exterior',5)

    # Tijeras Diésel (17)
    add_batch('AWP','TD10','Plataforma Tijera Diésel 10m',
        'Altura trab.: 10 m | Cap.: 450 kg | Ancho plat.: 1,52 m | Peso: 3.800 kg\nMotor: Diésel Kubota | Tracción 4x4 | Todo terreno',4)
    add_batch('AWP','TD12','Plataforma Tijera Diésel 12m',
        'Altura trab.: 12 m | Cap.: 680 kg | Ancho plat.: 1,52 m | Peso: 5.100 kg\nMotor: Diésel | Tracción 4x4 | Todo terreno',4)
    add_batch('AWP','TD14','Plataforma Tijera Diésel 14m',
        'Altura trab.: 14 m | Cap.: 680 kg | Ancho plat.: 1,83 m | Peso: 6.200 kg\nMotor: Diésel | Tracción 4x4 | Pendiente máx 45%',3)
    add_batch('AWP','TD16','Plataforma Tijera Diésel 16m',
        'Altura trab.: 16 m | Cap.: 680 kg | Ancho plat.: 1,83 m | Peso: 7.400 kg\nMotor: Diésel | Tracción 4x4 | Pendiente máx 45%',3)
    add_batch('AWP','TD18','Plataforma Tijera Diésel 18m',
        'Altura trab.: 18 m | Cap.: 680 kg | Ancho plat.: 2,44 m | Peso: 9.100 kg\nMotor: Diésel | Tracción 4x4 | Gran plataforma',3)

    # Articuladas Diésel (22)
    add_batch('AWP','AD12','Plataforma Articulada Diésel 12m',
        'Altura trab.: 12 m | Alcance hor.: 6,5 m | Cap.: 200 kg | Peso: 4.000 kg\nMotor: Diésel | Giro 360° | Compacta',4)
    add_batch('AWP','AD16','Plataforma Articulada Diésel 16m',
        'Altura trab.: 16 m | Alcance hor.: 8,5 m | Cap.: 230 kg | Peso: 6.200 kg\nMotor: Diésel | Giro 360° | Todo terreno',4)
    add_batch('AWP','AD20','Plataforma Articulada Diésel 20m',
        'Altura trab.: 20 m | Alcance hor.: 12 m | Cap.: 230 kg | Peso: 8.500 kg\nMotor: Diésel | Giro 360° | Todo terreno 4x4',4)
    add_batch('AWP','AD26','Plataforma Articulada Diésel 26m',
        'Altura trab.: 26 m | Alcance hor.: 16 m | Cap.: 230 kg | Peso: 12.000 kg\nMotor: Diésel | Giro 360° | Tracción 4x4',3)
    add_batch('AWP','AD33','Plataforma Articulada Diésel 33m',
        'Altura trab.: 33 m | Alcance hor.: 21 m | Cap.: 230 kg | Peso: 16.500 kg\nMotor: Diésel | Giro 360° | Gran altura',3)
    add_batch('AWP','AD43','Plataforma Articulada Diésel 43m',
        'Altura trab.: 43 m | Alcance hor.: 27 m | Cap.: 230 kg | Peso: 22.000 kg\nMotor: Diésel | Giro 360° | Alta gama',2)
    add_batch('AWP','AD53','Plataforma Articulada Diésel 53m',
        'Altura trab.: 53 m | Alcance hor.: 24 m | Cap.: 230 kg | Peso: 30.000 kg\nMotor: Diésel | Giro 360° | Máxima altura',2)

    # Telescópicas Diésel (10)
    add_batch('AWP','RD20','Plataforma Telescópica Diésel 20m',
        'Altura trab.: 20 m | Alcance hor.: 13,5 m | Cap.: 230 kg | Peso: 8.200 kg\nMotor: Diésel | Brazo telescópico | Todo terreno',3)
    add_batch('AWP','RD26','Plataforma Telescópica Diésel 26m',
        'Altura trab.: 26 m | Alcance hor.: 20 m | Cap.: 230 kg | Peso: 12.500 kg\nMotor: Diésel | Brazo telescópico | Todo terreno 4x4',3)
    add_batch('AWP','RD33','Plataforma Telescópica Diésel 33m',
        'Altura trab.: 33 m | Alcance hor.: 22 m | Cap.: 230 kg | Peso: 17.000 kg\nMotor: Diésel | Brazo telescópico | Gran alcance',2)
    add_batch('AWP','RD43','Plataforma Telescópica Diésel 43m',
        'Altura trab.: 43 m | Alcance hor.: 29 m | Cap.: 230 kg | Peso: 23.000 kg\nMotor: Diésel | Brazo telescópico | Alta gama',2)

    # Mástil Vertical Eléctrico (11)
    add_batch('AWP','VM05','Plataforma Mástil Vertical Eléctrica 5m',
        'Altura trab.: 5 m | Cap.: 150 kg | Ancho: 0,66 m | Peso: 450 kg\nEléctrica | Muy compacta | Uso interior | 1 persona',3)
    add_batch('AWP','VM06','Plataforma Mástil Vertical Eléctrica 6m',
        'Altura trab.: 6 m | Cap.: 200 kg | Ancho: 0,76 m | Peso: 680 kg\nEléctrica | Compacta | Uso interior | 1 persona',4)
    add_batch('AWP','VM08','Plataforma Mástil Vertical Eléctrica 8m',
        'Altura trab.: 8 m | Cap.: 200 kg | Ancho: 0,81 m | Peso: 950 kg\nEléctrica | Uso interior | 1 persona',4)

    # ── FLT — Carretillas Elevadoras (60) ────────────────────────────────────

    # Contrapesada Diésel (25)
    add_batch('FLT','CD15','Carretilla Contrapesada Diésel 1.5T',
        'Cap.: 1.500 kg | Alzada: 3 m | Motor: Diésel | Neumáticos: 6.00-9\nUso exterior | Cabina abierta',3)
    add_batch('FLT','CD20','Carretilla Contrapesada Diésel 2.0T',
        'Cap.: 2.000 kg | Alzada: 3 m | Motor: Diésel | Neumáticos: 7.00-12\nUso exterior | Cabina con techo',4)
    add_batch('FLT','CD25','Carretilla Contrapesada Diésel 2.5T',
        'Cap.: 2.500 kg | Alzada: 4 m | Motor: Diésel | Neumáticos: 7.00-12\nUso exterior | Con cabina',4)
    add_batch('FLT','CD30','Carretilla Contrapesada Diésel 3.0T',
        'Cap.: 3.000 kg | Alzada: 4,5 m | Motor: Diésel | Neumáticos: 8.25-15\nUso exterior | Triple mástil disponible',4)
    add_batch('FLT','CD40','Carretilla Contrapesada Diésel 4.0T',
        'Cap.: 4.000 kg | Alzada: 5 m | Motor: Diésel | Neumáticos: 8.25-15\nUso exterior | Alta capacidad',3)
    add_batch('FLT','CD50','Carretilla Contrapesada Diésel 5.0T',
        'Cap.: 5.000 kg | Alzada: 5 m | Motor: Diésel | Neumáticos: 9.00-20\nUso exterior | Cabina cerrada',3)
    add_batch('FLT','CD70','Carretilla Contrapesada Diésel 7.0T',
        'Cap.: 7.000 kg | Alzada: 4 m | Motor: Diésel | Neumáticos: 10.00-20\nUso exterior | Gran capacidad',2)
    add_batch('FLT','CD100','Carretilla Contrapesada Diésel 10T',
        'Cap.: 10.000 kg | Alzada: 4 m | Motor: Diésel | Neumáticos: 12.00-24\nUso exterior | Alta capacidad industrial',2)

    # Contrapesada Eléctrica (17)
    add_batch('FLT','CE15','Carretilla Contrapesada Eléctrica 1.5T',
        'Cap.: 1.500 kg | Alzada: 3 m | Batería: 48 V / 400 Ah | Peso: 2.900 kg\nUso interior/exterior | Silenciosa',3)
    add_batch('FLT','CE20','Carretilla Contrapesada Eléctrica 2.0T',
        'Cap.: 2.000 kg | Alzada: 3,5 m | Batería: 48 V / 500 Ah | Peso: 3.500 kg\nUso interior/exterior | Sin emisiones',4)
    add_batch('FLT','CE25','Carretilla Contrapesada Eléctrica 2.5T',
        'Cap.: 2.500 kg | Alzada: 4 m | Batería: 80 V / 500 Ah | Peso: 4.200 kg\nUso interior/exterior | Sin emisiones',3)
    add_batch('FLT','CE30','Carretilla Contrapesada Eléctrica 3.0T',
        'Cap.: 3.000 kg | Alzada: 4,5 m | Batería: 80 V / 600 Ah | Peso: 5.100 kg\nUso interior/exterior | Alta capacidad',4)
    add_batch('FLT','CE40','Carretilla Contrapesada Eléctrica 4.0T',
        'Cap.: 4.000 kg | Alzada: 5 m | Batería: 80 V / 750 Ah | Peso: 6.500 kg\nUso interior/exterior | Sin emisiones',3)

    # Retráctil Eléctrica (11)
    add_batch('FLT','RE12','Carretilla Retráctil Eléctrica 1.2T',
        'Cap.: 1.200 kg | Alzada: 7 m | Batería: 48 V / 375 Ah\nUso interior | Pasillo estrecho 2,5 m | Cabina estrecha',2)
    add_batch('FLT','RE16','Carretilla Retráctil Eléctrica 1.6T',
        'Cap.: 1.600 kg | Alzada: 8 m | Batería: 48 V / 450 Ah\nUso interior | Pasillo 2,7 m | Alta alzada',3)
    add_batch('FLT','RE20','Carretilla Retráctil Eléctrica 2.0T',
        'Cap.: 2.000 kg | Alzada: 9 m | Batería: 80 V / 500 Ah\nUso interior | Triple mástil | Gran alzada',3)
    add_batch('FLT','RE25','Carretilla Retráctil Eléctrica 2.5T',
        'Cap.: 2.500 kg | Alzada: 10 m | Batería: 80 V / 600 Ah\nUso interior | Máxima alzada | Almacén de gran altura',3)

    # Apiladora Eléctrica (7)
    add_batch('FLT','AP10','Apiladora Eléctrica 1.0T',
        'Cap.: 1.000 kg | Alzada: 3 m | Batería: 24 V\nUso interior | Compacta | Sin conductor a bordo',3)
    add_batch('FLT','AP15','Apiladora Eléctrica 1.5T',
        'Cap.: 1.500 kg | Alzada: 4 m | Batería: 24 V\nUso interior | Conductor a pie | Ligera',2)
    add_batch('FLT','AP20','Apiladora Eléctrica 2.0T',
        'Cap.: 2.000 kg | Alzada: 5 m | Batería: 24 V\nUso interior | Conductor a pie | Alta alzada',2)

    # ── DMP — Dúmperes (40) ──────────────────────────────────────────────────

    add_batch('DMP','A10','Dúmper Articulado 1T',
        'Cap.: 1.000 kg | Motor: Diésel | Tracción 4x4 | Articulado\nAncho: 0,85 m | Todo terreno | Vuelco frontal',5)
    add_batch('DMP','A15','Dúmper Articulado 1.5T',
        'Cap.: 1.500 kg | Motor: Diésel | Tracción 4x4 | Articulado\nAncho: 1,05 m | Todo terreno | Vuelco frontal',5)
    add_batch('DMP','A30','Dúmper Articulado 3T',
        'Cap.: 3.000 kg | Motor: Diésel | Tracción 4x4 | Articulado\nAncho: 1,35 m | Todo terreno | Basculante',5)
    add_batch('DMP','V30','Dúmper Volquete 4x4 3T',
        'Cap.: 3.000 kg | Motor: Diésel | Tracción 4x4 | Rígido\nAncho: 1,55 m | Vuelco trasero | Obra civil',4)
    add_batch('DMP','V60','Dúmper Volquete 4x4 6T',
        'Cap.: 6.000 kg | Motor: Diésel | Tracción 4x4 | Rígido\nAncho: 1,85 m | Vuelco trasero | Alta capacidad',4)
    add_batch('DMP','V90','Dúmper Volquete 4x4 9T',
        'Cap.: 9.000 kg | Motor: Diésel | Tracción 4x4 | Rígido\nAncho: 2,10 m | Vuelco trasero | Gran capacidad',4)
    add_batch('DMP','O10','Dúmper de Oruga 1T',
        'Cap.: 1.000 kg | Motor: Diésel | Oruga de goma\nAncho: 0,78 m | Muy baja presión suelo | Terreno blando',4)
    add_batch('DMP','O15','Dúmper de Oruga 1.5T',
        'Cap.: 1.500 kg | Motor: Diésel | Oruga de goma\nAncho: 0,95 m | Baja presión suelo | Vuelco frontal',5)
    add_batch('DMP','O30','Dúmper de Oruga 3T',
        'Cap.: 3.000 kg | Motor: Diésel | Oruga de goma\nAncho: 1,20 m | Baja presión suelo | Laderas pronunciadas',4)

    # ── EXC — Excavadoras (40) ───────────────────────────────────────────────

    add_batch('EXC','M08','Miniexcavadora 0.8T',
        'Peso: 850 kg | Motor: Diésel monocilíndrico | Prof. exc.: 1,5 m\nAncho con cuchara: 0,78 m | Sin colada | Interior/Patios',3)
    add_batch('EXC','M10','Miniexcavadora 1.0T',
        'Peso: 1.000 kg | Motor: Diésel | Prof. exc.: 1,8 m\nAncho: 0,85 m | Sin colada | Jardines y espacios reducidos',4)
    add_batch('EXC','M15','Miniexcavadora 1.5T',
        'Peso: 1.550 kg | Motor: Diésel Kubota | Prof. exc.: 2,2 m\nAncho: 0,98 m | Sin colada | Versátil | 3 cucharas incluidas',4)
    add_batch('EXC','M20','Miniexcavadora 2.0T',
        'Peso: 2.000 kg | Motor: Diésel | Prof. exc.: 2,5 m\nAncho: 1,10 m | Sin colada | Gran versatilidad',3)
    add_batch('EXC','M30','Miniexcavadora 3.0T',
        'Peso: 3.000 kg | Motor: Diésel | Prof. exc.: 3,0 m\nAncho: 1,35 m | Sin colada | Máxima capacidad mini',3)
    add_batch('EXC','ME50','Excavadora Midi 5T',
        'Peso: 5.000 kg | Motor: Diésel | Prof. exc.: 3,5 m | Alcance: 6,5 m\nCabina ROPS/FOPS | Sin colada | Versátil',3)
    add_batch('EXC','ME60','Excavadora Midi 6T',
        'Peso: 6.100 kg | Motor: Diésel | Prof. exc.: 4,0 m | Alcance: 7,2 m\nCabina ROPS/FOPS | Potente',3)
    add_batch('EXC','ME80','Excavadora Midi 8T',
        'Peso: 8.200 kg | Motor: Diésel | Prof. exc.: 4,5 m | Alcance: 7,8 m\nCabina | Todo terreno | Alta productividad',3)
    add_batch('EXC','ME100','Excavadora Midi 10T',
        'Peso: 10.500 kg | Motor: Diésel | Prof. exc.: 5,0 m | Alcance: 8,5 m\nCabina | Obra civil | Potente',2)
    add_batch('EXC','G140','Excavadora Grande 14T',
        'Peso: 14.000 kg | Motor: Diésel | Prof. exc.: 5,5 m | Alcance: 9,0 m\nCabina | Obra civil y demolición',3)
    add_batch('EXC','G200','Excavadora Grande 20T',
        'Peso: 20.500 kg | Motor: Diésel | Prof. exc.: 6,3 m | Alcance: 10,0 m\nCabina | Obra civil pesada',3)
    add_batch('EXC','G300','Excavadora Grande 30T',
        'Peso: 30.000 kg | Motor: Diésel | Prof. exc.: 7,0 m | Alcance: 11,5 m\nCabina | Gran obra civil',2)
    add_batch('EXC','G380','Excavadora Grande 38T',
        'Peso: 38.500 kg | Motor: Diésel | Prof. exc.: 8,0 m | Alcance: 12,5 m\nCabina | Alta producción | Cantera/obra',2)
    add_batch('EXC','G500','Excavadora Grande 50T',
        'Peso: 50.000 kg | Motor: Diésel | Prof. exc.: 9,0 m | Alcance: 14,0 m\nCabina | Máxima capacidad | Grandes obras',2)

    # ── TLH — Manipuladores Telescópicos (35) ────────────────────────────────

    add_batch('TLH','R17','Manipulador Telescópico Rotante 17m / 2.6T',
        'Cap.: 2.600 kg | Alcance: 17 m | Peso: 9.800 kg | Motor: Diésel\nGiro 360° | Tracción 4x4 | Transmisión automática',4)
    add_batch('TLH','R20','Manipulador Telescópico Rotante 20m / 3.5T',
        'Cap.: 3.500 kg | Alcance: 20 m | Peso: 12.500 kg | Motor: Diésel\nGiro 360° | Tracción 4x4 | Todo terreno',4)
    add_batch('TLH','R22','Manipulador Telescópico Rotante 22m / 4T',
        'Cap.: 4.000 kg | Alcance: 22 m | Peso: 14.200 kg | Motor: Diésel\nGiro 360° | Tracción 4x4 | Estabilizadores',3)
    add_batch('TLH','R25','Manipulador Telescópico Rotante 25m / 6T',
        'Cap.: 6.000 kg | Alcance: 25 m | Peso: 18.000 kg | Motor: Diésel\nGiro 360° | Alta capacidad | Obra pesada',3)
    add_batch('TLH','R30','Manipulador Telescópico Rotante 30m / 7T',
        'Cap.: 7.000 kg | Alcance: 30 m | Peso: 22.000 kg | Motor: Diésel\nGiro 360° | Máximo alcance | Alta capacidad',3)
    add_batch('TLH','F07','Manipulador Telescópico Fijo 7m / 3T',
        'Cap.: 3.000 kg | Alzada: 7 m | Peso: 6.500 kg | Motor: Diésel\nTracción 4x4 | Compacto | Obra mediana',3)
    add_batch('TLH','F08','Manipulador Telescópico Fijo 8m / 4T',
        'Cap.: 4.000 kg | Alzada: 8 m | Peso: 8.200 kg | Motor: Diésel\nTracción 4x4 | Todo terreno | Versátil',3)
    add_batch('TLH','F12','Manipulador Telescópico Fijo 12m / 6T',
        'Cap.: 6.000 kg | Alzada: 12 m | Peso: 11.500 kg | Motor: Diésel\nTracción 4x4 | Alta capacidad',3)
    add_batch('TLH','F14','Manipulador Telescópico Fijo 14m / 7T',
        'Cap.: 7.000 kg | Alzada: 14 m | Peso: 14.000 kg | Motor: Diésel\nTracción 4x4 | Máxima capacidad fijo',3)
    add_batch('TLH','C10','Manipulador Telescópico Compacto 10m / 2.5T',
        'Cap.: 2.500 kg | Alzada: 10 m | Peso: 5.200 kg | Motor: Diésel\nCompacto | Interior/exterior | Anchura 1,9 m',3)
    add_batch('TLH','C13','Manipulador Telescópico Compacto 13m / 3.7T',
        'Cap.: 3.700 kg | Alzada: 13 m | Peso: 7.100 kg | Motor: Diésel\nCompacto | Anchura 2,1 m | Versátil',3)

    # ── RTH — Martillos de Vía (15) ──────────────────────────────────────────

    add_batch('RTH','H065','Martillo de Vía 65 kg',
        'Peso: 65 kg | Energía golpe: 250 J | Frec.: 600 gpm\nMotor: Diésel | Burilado y demolición ligera',3)
    add_batch('RTH','H085','Martillo de Vía 85 kg',
        'Peso: 85 kg | Energía golpe: 350 J | Frec.: 550 gpm\nMotor: Diésel | Demolición y pavimento',3)
    add_batch('RTH','H120','Martillo de Vía 120 kg',
        'Peso: 120 kg | Energía golpe: 550 J | Frec.: 500 gpm\nMotor: Diésel | Demolición media | Con silenciador',3)
    add_batch('RTH','H150','Martillo de Vía 150 kg',
        'Peso: 150 kg | Energía golpe: 750 J | Frec.: 450 gpm\nMotor: Diésel | Demolición pesada | ROPS',3)
    add_batch('RTH','H250','Martillo de Vía 250 kg',
        'Peso: 250 kg | Energía golpe: 1.500 J | Frec.: 350 gpm\nMotor: Diésel | Gran demolición | Alta energía',3)

    # ── GEN — Grupos Electrógenos (70) ───────────────────────────────────────

    add_batch('GEN','010KVA','Grupo Electrógeno 10 kVA',
        'Potencia: 10 kVA / 8 kW | Motor: Diésel monocilíndrico\nDepósito: 30 L | Autonomía: 8 h | Silenciado',4)
    add_batch('GEN','015KVA','Grupo Electrógeno 15 kVA',
        'Potencia: 15 kVA / 12 kW | Motor: Diésel\nDepósito: 40 L | Autonomía: 8 h | Silenciado',4)
    add_batch('GEN','020KVA','Grupo Electrógeno 20 kVA',
        'Potencia: 20 kVA / 16 kW | Motor: Diésel\nDepósito: 50 L | Autonomía: 10 h | Insonorizado',6)
    add_batch('GEN','030KVA','Grupo Electrógeno 30 kVA',
        'Potencia: 30 kVA / 24 kW | Motor: Diésel\nDepósito: 70 L | Autonomía: 10 h | Insonorizado',6)
    add_batch('GEN','045KVA','Grupo Electrógeno 45 kVA',
        'Potencia: 45 kVA / 36 kW | Motor: Diésel\nDepósito: 100 L | Autonomía: 10 h | Insonorizado',6)
    add_batch('GEN','060KVA','Grupo Electrógeno 60 kVA',
        'Potencia: 60 kVA / 48 kW | Motor: Diésel Kubota\nDepósito: 140 L | Autonomía: 12 h | Cuadro ATS',6)
    add_batch('GEN','075KVA','Grupo Electrógeno 75 kVA',
        'Potencia: 75 kVA / 60 kW | Motor: Diésel Perkins\nDepósito: 200 L | Autonomía: 12 h | Cuadro ATS',6)
    add_batch('GEN','100KVA','Grupo Electrógeno 100 kVA',
        'Potencia: 100 kVA / 80 kW | Motor: Diésel Perkins\nDepósito: 250 L | Autonomía: 12 h | Cuadro ATS | Remolque',6)
    add_batch('GEN','130KVA','Grupo Electrógeno 130 kVA',
        'Potencia: 130 kVA / 104 kW | Motor: Diésel\nDepósito: 300 L | Autonomía: 12 h | Cuadro ATS | Remolque',6)
    add_batch('GEN','150KVA','Grupo Electrógeno 150 kVA',
        'Potencia: 150 kVA / 120 kW | Motor: Diésel Volvo\nDepósito: 400 L | Autonomía: 14 h | Sincronizable',4)
    add_batch('GEN','200KVA','Grupo Electrógeno 200 kVA',
        'Potencia: 200 kVA / 160 kW | Motor: Diésel Volvo\nDepósito: 500 L | Autonomía: 14 h | Sincronizable',4)
    add_batch('GEN','250KVA','Grupo Electrógeno 250 kVA',
        'Potencia: 250 kVA / 200 kW | Motor: Diésel Cummins\nDepósito: 600 L | Autonomía: 14 h | Sincronizable',4)
    add_batch('GEN','350KVA','Grupo Electrógeno 350 kVA',
        'Potencia: 350 kVA / 280 kW | Motor: Diésel Cummins\nDepósito: 800 L | Autonomía: 16 h | Sincronizable | Sobre semirremolque',4)
    add_batch('GEN','500KVA','Grupo Electrógeno 500 kVA',
        'Potencia: 500 kVA / 400 kW | Motor: Diésel Cummins\nDepósito: 1.200 L | Autonomía: 16 h | Sincronizable | Sobre semirremolque',4)

    # ── TOL — Herramientas y Accesorios (40) ─────────────────────────────────

    add_batch('TOL','CBT','Compactador de Bandeja Vibrante',
        'Peso: 75 kg | Fuerza centrífuga: 15 kN | Ancho: 50 cm\nMotor: Honda GX160 | Rendimiento: 300 m²/h',4)
    add_batch('TOL','CRU','Compactador de Rulo Vibrante',
        'Peso: 1.500 kg | Ancho tambor: 100 cm | Motor: Diésel\nPara subbase y asfalto | Rendimiento: 800 m²/h',4)
    add_batch('TOL','PSN','Pisón Compactador (Saltarín)',
        'Peso: 60 kg | Fuerza: 14,5 kN | Motor: Honda 4T\nIdeal zanjas y espacios estrechos | 680 gpm',3)
    add_batch('TOL','MTH','Martillo Eléctrico Demoledor 10 kg',
        'Peso: 10 kg | Potencia: 1.500 W | Energía golpe: 45 J\nCon maletín y 3 puntas | Demolición y cincelado',4)
    add_batch('TOL','CAS','Cortadora de Asfalto/Hormigón',
        'Peso: 95 kg | Disco: 350 mm | Motor: Diésel Honda\nProfundidad corte: 125 mm | Con sistema de agua',3)
    add_batch('TOL','BBA','Bomba de Aguas Sucias 4"',
        'Caudal: 1.200 L/min | Altura: 8 m | Boca: 4"\nMotor: Diésel | Paso sólidos: 35 mm | Achicar obras',4)
    add_batch('TOL','HMG','Hormigonera 500 L',
        'Capacidad: 500 L / 350 L de mezcla | Motor: Diésel\nPeso: 320 kg | Producción: 7 m³/h | Remolcable',4)
    add_batch('TOL','TOR','Torre de Iluminación 4x1000W',
        'Potencia: 4 × 1.000 W | Altura mástil: 9 m | Motor: Diésel\nAutonomía: 100 h | Área iluminación: 4.000 m²',4)
    add_batch('TOL','VIB','Aguja Vibradora de Hormigón',
        'Longitud manguera: 6 m | Cabezal: 38 mm | Motor: Eléctrico 230V\nFrecuencia: 12.000 rpm | Compactación hormigón',4)
    add_batch('TOL','CAB','Cabestrante Eléctrico 2T',
        'Cap.: 2.000 kg | Cable: 15 m | Motor: Eléctrico 230V\nVelocidad: 8 m/min | Con mando a distancia',3)
    add_batch('TOL','REM','Remolque Portamáquinas 3.5T',
        'PMA: 3.500 kg | Dimensiones: 4,2 × 2,1 m | Rampas abatibles\nEngancha turismo/furgoneta | Rampa 2 m',3)

    db.session.commit()

    final_count = Machine.query.count()
    by_status = {}
    for m in Machine.query.all():
        by_status[m.status] = by_status.get(m.status, 0) + 1

    click.secho(f'\n✓ Flota actualizada: {final_count} máquinas en total '
                f'({total_created} añadidas en esta ejecución).', fg='green')
    for st, cnt in sorted(by_status.items()):
        labels = {'free': 'Libres', 'occupied': 'Ocupadas',
                  'repair': 'En reparación', 'reserved': 'Reservadas'}
        click.echo(f'  {labels.get(st, st):15} {cnt:>4}')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
