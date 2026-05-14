from datetime import date
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app import db
from app.models import Machine, DeliveryNote, DeliveryNoteMachine
from app.constants import DELEGACIONES, MACHINE_CATEGORIES
from app.auth.decorators import allowed_delegaciones

bp = Blueprint('disponibilidad', __name__)


@bp.route('/')
@login_required
def index():
    date_from_str  = request.args.get('date_from', '').strip()
    date_to_str    = request.args.get('date_to', '').strip()
    category_f     = request.args.get('category', '').strip()
    delegacion_f   = request.args.get('delegacion', '').strip()

    available   = []
    unavailable = []   # list of (machine, [delivery_note, ...])
    searched    = False
    error_msg   = None

    valid_cats = {code for code, _ in MACHINE_CATEGORIES}

    if date_from_str and date_to_str:
        try:
            date_from = date.fromisoformat(date_from_str)
            date_to   = date.fromisoformat(date_to_str)
        except ValueError:
            date_from = date_to = None
            error_msg = 'Fechas inválidas.'

        if date_from and date_to:
            if date_from > date_to:
                error_msg = 'La fecha de inicio no puede ser posterior a la fecha de fin.'
            else:
                searched = True

                # IDs de albaranes activos que solapan el rango pedido.
                # Solapan si: rental_start <= date_to AND (rental_end IS NULL OR rental_end >= date_from)
                busy_notes_q = DeliveryNote.query.filter(
                    DeliveryNote.status == 'active',
                    DeliveryNote.rental_start <= date_to,
                    db.or_(
                        DeliveryNote.rental_end.is_(None),
                        DeliveryNote.rental_end >= date_from,
                    )
                )

                # Filtrar por delegación si el usuario tiene restricción
                allowed = allowed_delegaciones(current_user)
                if allowed is not None:
                    busy_notes_q = busy_notes_q.filter(
                        db.or_(
                            DeliveryNote.delegacion.is_(None),
                            DeliveryNote.delegacion.in_(list(allowed) or ['__none__']),
                        )
                    )

                busy_note_ids = [r.id for r in busy_notes_q.with_entities(DeliveryNote.id).all()]

                # Máquinas ocupadas → mapear machine_id → notas
                busy_machine_ids = set()
                busy_info = {}  # machine_id -> list of DeliveryNote
                if busy_note_ids:
                    dnms = (
                        DeliveryNoteMachine.query
                        .filter(DeliveryNoteMachine.delivery_note_id.in_(busy_note_ids))
                        .options(
                            joinedload(DeliveryNoteMachine.delivery_note)
                            .joinedload(DeliveryNote.client)
                        )
                        .all()
                    )
                    for dnm in dnms:
                        busy_machine_ids.add(dnm.machine_id)
                        busy_info.setdefault(dnm.machine_id, []).append(dnm.delivery_note)

                # Consultar todas las máquinas activas con filtros opcionales
                q = Machine.query.filter(Machine.deleted_at.is_(None))
                if category_f and category_f in valid_cats:
                    q = q.filter(Machine.category == category_f)
                if delegacion_f and delegacion_f in DELEGACIONES:
                    q = q.filter(Machine.current_delegacion == delegacion_f)

                machines = q.order_by(Machine.category, Machine.code).all()

                for m in machines:
                    if m.id in busy_machine_ids or m.status == 'repair':
                        unavailable.append((m, busy_info.get(m.id, [])))
                    else:
                        available.append(m)

    return render_template(
        'disponibilidad/index.html',
        available=available,
        unavailable=unavailable,
        searched=searched,
        error_msg=error_msg,
        date_from=date_from_str,
        date_to=date_to_str,
        category_f=category_f,
        delegacion_f=delegacion_f,
        categories=MACHINE_CATEGORIES,
        delegaciones=DELEGACIONES,
    )
