import json
from flask import request
from flask_login import current_user
from app import db
from app.auth.models import AuditLog


def log_action(action, entity, entity_id, entity_label, diff=None):
    """
    Registra una entrada en AuditLog dentro de la sesión actual.
    No hace commit — el llamador debe hacerlo junto con los datos principales.
    """
    entry = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        entity=entity,
        entity_id=entity_id,
        entity_label=entity_label,
        diff=json.dumps(diff, ensure_ascii=False, default=str) if diff else None,
        ip_address=request.remote_addr,
    )
    db.session.add(entry)


def make_diff(old: dict, new: dict):
    """Devuelve {campo: [valor_antiguo, valor_nuevo]} solo para los campos que cambiaron."""
    changed = {k: [old[k], new[k]] for k in old if old[k] != new[k]}
    return changed if changed else None
