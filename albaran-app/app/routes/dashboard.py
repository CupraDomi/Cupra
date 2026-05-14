from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import func
from app import db
from app.constants import MACHINE_CATEGORIES
from app.models import Machine, DeliveryNote, Client

bp = Blueprint('dashboard', __name__)

# Reexportado por compatibilidad con otras vistas que ya importan de aquí.
CATEGORIES = MACHINE_CATEGORIES


@bp.route('/')
@login_required
def index():
    cat_filter    = request.args.get('cat', '')
    status_filter = request.args.get('status', '')

    q = Machine.query
    if cat_filter:
        q = q.filter_by(category=cat_filter)
    if status_filter:
        q = q.filter_by(status=status_filter)
    machines = q.order_by(Machine.code).all()

    # Una sola query para conteos de máquinas por estado.
    machine_counts = dict(
        db.session.query(Machine.status, func.count(Machine.id))
        .group_by(Machine.status).all()
    )
    total_machines = sum(machine_counts.values())

    stats = {
        'total':    total_machines,
        'free':     machine_counts.get('free', 0),
        'occupied': machine_counts.get('occupied', 0),
        'reserved': machine_counts.get('reserved', 0),
        'repair':   machine_counts.get('repair', 0),
        'active_albaranes': db.session.query(func.count(DeliveryNote.id))
                              .filter_by(status='active').scalar() or 0,
        'total_clients':    db.session.query(func.count(Client.id)).scalar() or 0,
    }

    return render_template('dashboard/index.html',
                           machines=machines,
                           stats=stats,
                           categories=MACHINE_CATEGORIES,
                           cat_filter=cat_filter,
                           status_filter=status_filter)
