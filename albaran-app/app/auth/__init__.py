from flask import Blueprint

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Importar rutas después del blueprint para evitar importaciones circulares
from app.auth import routes  # noqa: E402, F401
