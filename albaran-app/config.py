import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # SECRET_KEY: en producción DEBE venir de la variable de entorno.
    # En desarrollo, si no está, se genera una efímera por proceso (las sesiones
    # se invalidan al reiniciar — eso es lo deseable).
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # Render entrega DATABASE_URL con prefijo "postgres://" (obsoleto en SQLAlchemy 2).
    # Lo normalizamos a "postgresql://" para evitar el error de dialecto.
    _db_url = os.environ.get('DATABASE_URL',
                             f'sqlite:///{os.path.join(BASE_DIR, "albaran.db")}')
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── CSRF (Flask-WTF) ────────────────────────────────────────────────────
    WTF_CSRF_TIME_LIMIT = 60 * 60 * 8        # 8 horas
    WTF_CSRF_SSL_STRICT = True

    # ── Cookies de sesión ───────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # En producción (Render) SESSION_COOKIE_SECURE se activa automáticamente
    # si DATABASE_URL existe (señal de que estamos en producción).
    _in_prod = bool(os.environ.get('DATABASE_URL'))
    SESSION_COOKIE_SECURE   = os.environ.get('SESSION_COOKIE_SECURE', '1' if _in_prod else '0') == '1'

    # ── Datos de empresa ────────────────────────────────────────────────────
    COMPANY_NAME    = os.environ.get('COMPANY_NAME',    'Soluciones Integrales de Maquinaria Sur')
    COMPANY_ADDRESS = os.environ.get('COMPANY_ADDRESS', 'Calle Gabriel Ramos Bejarano 122 A-B, 14014, Córdoba')
    COMPANY_PHONE   = os.environ.get('COMPANY_PHONE',   '957740004')
    COMPANY_EMAIL   = os.environ.get('COMPANY_EMAIL',   'administracion@simsur.es')
    COMPANY_CIF     = os.environ.get('COMPANY_CIF',     'B14933931')
