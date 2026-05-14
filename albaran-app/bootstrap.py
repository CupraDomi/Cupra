"""
Bootstrap robusto para arranque en cloud.
Crea las tablas (migraciones primero, db.create_all() como fallback)
y carga los datos iniciales (admin + demo si SEED_DEMO=1).

Se ejecuta automáticamente desde el Dockerfile antes de gunicorn.
"""
import os
import sys
import traceback


def main():
    print('═' * 60, flush=True)
    print('  BOOTSTRAP albaran-app', flush=True)
    print('═' * 60, flush=True)
    print(f'PORT             = {os.environ.get("PORT", "(no definida)")}', flush=True)
    print(f'DATABASE_URL     = {"SI" if os.environ.get("DATABASE_URL") else "NO (usará SQLite)"}', flush=True)
    print(f'SEED_DEMO        = {os.environ.get("SEED_DEMO", "(no definida)")}', flush=True)
    print(f'ADMIN_PASSWORD   = {"SI" if os.environ.get("ADMIN_PASSWORD") else "NO"}', flush=True)
    print(f'ADMIN_USERNAME   = {os.environ.get("ADMIN_USERNAME", "(no definida)")}', flush=True)
    print('─' * 60, flush=True)

    # 1. Crear la app y aplicar migraciones (con fallback)
    print('[1/3] Importando app y conectando a la base de datos...', flush=True)
    from app import create_app, db
    app = create_app()

    with app.app_context():
        # Comprobar conexión
        from sqlalchemy import text
        try:
            db.session.execute(text('SELECT 1'))
            print('       ✓ Conexión a la base de datos OK', flush=True)
        except Exception as e:
            print(f'       ✗ FALLO al conectar: {e}', flush=True)
            traceback.print_exc()
            sys.exit(1)

        # 2. Aplicar migraciones (con fallback a create_all)
        print('[2/3] Aplicando migraciones...', flush=True)
        try:
            from flask_migrate import upgrade as alembic_upgrade
            alembic_upgrade()
            print('       ✓ Migraciones aplicadas correctamente', flush=True)
        except Exception as e:
            print(f'       ⚠ Migraciones fallaron: {e}', flush=True)
            traceback.print_exc()
            print('       → Fallback: db.create_all()', flush=True)
            try:
                db.create_all()
                print('       ✓ Tablas creadas via db.create_all()', flush=True)
            except Exception as e2:
                print(f'       ✗ db.create_all() también falló: {e2}', flush=True)
                traceback.print_exc()
                sys.exit(1)

        # 3. Crear admin + cargar demo
        print('[3/3] Creando admin y cargando demo...', flush=True)
        from app.auth.models import User

        if not User.query.first():
            password = os.environ.get('ADMIN_PASSWORD')
            if password:
                username  = os.environ.get('ADMIN_USERNAME', 'admin')
                full_name = os.environ.get('ADMIN_FULLNAME', 'Administrador')
                user = User(username=username, full_name=full_name,
                            role='jefe', must_change_password=False)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                print(f'       ✓ Usuario "{username}" creado con rol jefe', flush=True)
            else:
                print('       ⚠ ADMIN_PASSWORD no definida — no se crea admin', flush=True)
        else:
            print('       ✓ Ya hay usuarios — saltando creación de admin', flush=True)

        # Cargar demo si SEED_DEMO=1 y la BD está vacía
        if os.environ.get('SEED_DEMO') == '1':
            from app.models import Machine
            if Machine.query.count() == 0:
                print('       → SEED_DEMO=1 y BD vacía — cargando datos demo...', flush=True)
                try:
                    from run import _populate_machines
                    _populate_machines()
                    db.session.commit()
                    import seed as seed_module
                    seed_module.seed()
                    print('       ✓ Datos demo cargados', flush=True)
                except Exception as e:
                    print(f'       ⚠ Carga demo falló: {e}', flush=True)
                    traceback.print_exc()
            else:
                count = Machine.query.count()
                print(f'       ✓ Ya hay {count} máquinas — saltando demo', flush=True)
        else:
            print('       ✓ SEED_DEMO != 1 — saltando demo', flush=True)

    print('═' * 60, flush=True)
    print('  Bootstrap completo — arrancando gunicorn', flush=True)
    print('═' * 60, flush=True)


if __name__ == '__main__':
    main()
