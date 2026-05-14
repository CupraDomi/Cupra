from functools import wraps
from flask import abort
from flask_login import current_user


def jefe_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_jefe:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def permission_required(*perm_names):
    """
    Pasa si el usuario es jefe o tiene CUALQUIERA de los permisos indicados.
    Uso: @permission_required('conceder_permisos')
         @permission_required('ver_estadisticas')
         @permission_required('ver_historial_global', 'ver_historial_parcial')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.is_jefe:
                return f(*args, **kwargs)
            if any(current_user.has_permission(p) for p in perm_names):
                return f(*args, **kwargs)
            abort(403)
        return decorated
    return decorator


def allowed_delegaciones(user):
    """
    Devuelve un set con todas las delegaciones a las que el usuario tiene
    acceso, o None si tiene acceso global (jefe / ver_albaranes_todas).
    """
    if user.is_jefe or user.has_permission('ver_albaranes_todas'):
        return None
    allowed = set()
    if user.delegacion:
        allowed.add(user.delegacion)
    perm = user.get_active_permission('ver_albaranes_delegacion')
    if perm:
        for t in perm.targets.all():
            if t.target_delegacion:
                allowed.add(t.target_delegacion)
    return allowed


def can_view_albaran(user, note):
    """Comprueba si el usuario puede ver un albarán (lectura)."""
    allowed = allowed_delegaciones(user)
    if allowed is None:                       # acceso global
        return True
    if note.delegacion is None:
        # Albaranes sin delegación asignada: visibles para todos (compat. histórica)
        return True
    return note.delegacion in allowed


def require_albaran_view(note, user=None):
    """Helper para usar dentro de rutas: aborta 403 si no puede ver el albarán."""
    if user is None:
        user = current_user
    if not user.is_authenticated:
        abort(403)
    if not can_view_albaran(user, note):
        abort(403)
