from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify
from app import db
from app.models import DeliveryNote

bp = Blueprint('firma', __name__)


def _utcnow():
    """Naive UTC — compatible con lo que SQLite devuelve al leer DateTime."""
    return datetime.utcnow()


def _naive(dt):
    """Elimina tzinfo si lo tiene, para comparar con datetimes naive de SQLite."""
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


def _is_expired(note):
    exp = _naive(note.signature_token_expires)
    return exp is not None and exp < _utcnow()


@bp.route('/<token>', methods=['GET'])
def sign(token):
    note = DeliveryNote.query.filter_by(signature_token=token).first()
    if not note or _is_expired(note):
        return render_template('firma/expired.html'), 410

    if note.signed_at:
        return render_template('firma/done.html', note=note)

    machines = [dnm.machine for dnm in note.machines.all()]
    return render_template('firma/index.html', note=note, machines=machines)


@bp.route('/<token>', methods=['POST'])
def sign_post(token):
    note = DeliveryNote.query.filter_by(signature_token=token).first()
    if not note or _is_expired(note):
        return jsonify({'error': 'Token inválido o expirado'}), 410

    if note.signed_at:
        return jsonify({'error': 'Este albarán ya ha sido firmado'}), 400

    data           = request.get_json(silent=True) or {}
    signer_name    = (data.get('signer_name') or '').strip()
    signature_data = (data.get('signature_data') or '').strip()

    if not signer_name:
        return jsonify({'error': 'Introduce tu nombre completo'}), 400
    if not signature_data or signature_data in ('data:,', 'data:image/png;base64,'):
        return jsonify({'error': 'La firma está vacía. Firma en el recuadro.'}), 400

    note.signer_name             = signer_name
    note.signature_data          = signature_data
    note.signed_at               = _utcnow()
    note.signature_token         = None   # invalidar — solo se usa una vez
    note.signature_token_expires = None
    db.session.commit()

    return jsonify({'ok': True})
