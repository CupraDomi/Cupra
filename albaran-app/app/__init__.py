from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'

csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=['1000 per hour'],
    storage_uri='memory://',
)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Render (y cualquier reverse-proxy) termina TLS antes de llegar a Gunicorn.
    # Sin ProxyFix, url_for(_external=True) genera http:// en vez de https://,
    # rompiendo los QR de firma y la validación CSRF SSL-strict.
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Inyectar csrf_token() global en todos los templates.
    app.jinja_env.globals['csrf_token'] = generate_csrf

    # Importar modelos antes de registrar blueprints
    from app import models           # noqa: F401
    from app.auth import models as auth_models  # noqa: F401

    from app.auth.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Blueprints
    from app.routes.dashboard      import bp as dashboard_bp
    from app.routes.machines       import bp as machines_bp
    from app.routes.clients        import bp as clients_bp
    from app.routes.albaranes      import bp as albaranes_bp
    from app.routes.admin          import bp as admin_bp
    from app.routes.disponibilidad import bp as disponibilidad_bp
    from app.routes.firma          import bp as firma_bp
    from app.routes.reparaciones   import bp as reparaciones_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(machines_bp,       url_prefix='/machines')
    app.register_blueprint(clients_bp,        url_prefix='/clients')
    app.register_blueprint(albaranes_bp,      url_prefix='/albaranes')
    app.register_blueprint(admin_bp)
    app.register_blueprint(disponibilidad_bp, url_prefix='/disponibilidad')
    app.register_blueprint(firma_bp,          url_prefix='/firma')
    app.register_blueprint(reparaciones_bp,  url_prefix='/reparaciones')
    csrf.exempt(firma_bp)   # rutas públicas — el token actúa como autenticación

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    # Manejadores de errores
    from flask import render_template
    from flask_wtf.csrf import CSRFError

    @app.errorhandler(403)
    def _forbidden(e):
        return render_template('errors/error.html',
                               code=403, title='Acceso denegado',
                               message='No tienes permisos para acceder a este recurso.'), 403

    @app.errorhandler(404)
    def _not_found(e):
        return render_template('errors/error.html',
                               code=404, title='No encontrado',
                               message='La página que buscas no existe.'), 404

    @app.errorhandler(CSRFError)
    def _csrf_error(e):
        return render_template('errors/error.html',
                               code=400, title='Sesión expirada',
                               message='El formulario expiró. Recarga la página e inténtalo de nuevo.'), 400

    @app.errorhandler(429)
    def _rate_limited(e):
        return render_template('errors/error.html',
                               code=429, title='Demasiadas peticiones',
                               message='Has hecho demasiadas peticiones. Espera unos minutos.'), 429

    return app
