from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import RepairOrder, RepairComment, Machine, MachineStatusLog
from app.constants import DELEGACIONES
from app.auth.helpers import log_action

bp = Blueprint('reparaciones', __name__)


@bp.route('/')
@login_required
def index():
    status_f    = request.args.get('status', 'open')
    delegacion_f = request.args.get('delegacion', '')

    q = RepairOrder.query
    if status_f in ('open', 'closed'):
        q = q.filter_by(status=status_f)
    if delegacion_f in DELEGACIONES:
        q = q.filter_by(delegacion=delegacion_f)

    orders = q.order_by(RepairOrder.created_at.desc()).all()

    return render_template('reparaciones/index.html',
                           orders=orders,
                           status_f=status_f,
                           delegacion_f=delegacion_f,
                           delegaciones=DELEGACIONES)


@bp.route('/<int:order_id>')
@login_required
def detail(order_id):
    order = RepairOrder.query.get_or_404(order_id)
    comments = order.comments.all()
    return render_template('reparaciones/detail.html',
                           order=order,
                           comments=comments,
                           delegaciones=DELEGACIONES)


@bp.route('/<int:order_id>/comentar', methods=['POST'])
@login_required
def comentar(order_id):
    order = RepairOrder.query.get_or_404(order_id)
    if order.status == 'closed':
        flash('No se pueden añadir comentarios a un parte cerrado.', 'warning')
        return redirect(url_for('reparaciones.detail', order_id=order_id))

    text = request.form.get('text', '').strip()
    if not text:
        flash('El comentario no puede estar vacío.', 'warning')
        return redirect(url_for('reparaciones.detail', order_id=order_id))

    comment = RepairComment(
        repair_order_id = order_id,
        text            = text,
        created_at      = datetime.now(timezone.utc),
        created_by_id   = current_user.id,
    )
    db.session.add(comment)
    db.session.commit()
    flash('Comentario añadido.', 'success')
    return redirect(url_for('reparaciones.detail', order_id=order_id))


@bp.route('/<int:order_id>/cerrar', methods=['POST'])
@login_required
def cerrar(order_id):
    order = RepairOrder.query.get_or_404(order_id)
    if order.status == 'closed':
        flash('Este parte ya está cerrado.', 'warning')
        return redirect(url_for('reparaciones.detail', order_id=order_id))

    resolution  = request.form.get('resolution_notes', '').strip() or None
    cost_raw    = request.form.get('cost', '').strip()
    new_status  = request.form.get('machine_status', 'free')
    if new_status not in ('free', 'reserved'):
        new_status = 'free'

    try:
        order.cost             = float(cost_raw) if cost_raw else order.cost
    except ValueError:
        pass
    order.resolution_notes = resolution
    order.status           = 'closed'
    order.closed_at        = datetime.now(timezone.utc)
    order.closed_by_id     = current_user.id

    # Cambiar el estado de la máquina si sigue en reparación
    machine = order.machine
    if machine.status == 'repair':
        old_status = machine.status
        machine.status = new_status
        db.session.add(MachineStatusLog(
            machine_id=machine.id,
            old_status=old_status,
            new_status=new_status,
            delivery_note_id=None,
            changed_by=current_user.username,
        ))
        log_action('updated', 'machine', machine.id, machine.code,
                   diff={'status': [old_status, new_status]})

    log_action('updated', 'repair_order', order.id, f'Parte #{order.id} ({machine.code})')
    db.session.commit()
    flash(f'Parte de reparación cerrado. Máquina marcada como "{new_status}".', 'success')
    return redirect(url_for('reparaciones.detail', order_id=order_id))


@bp.route('/<int:order_id>/editar', methods=['POST'])
@login_required
def editar(order_id):
    order = RepairOrder.query.get_or_404(order_id)
    if order.status == 'closed':
        flash('No se puede editar un parte cerrado.', 'warning')
        return redirect(url_for('reparaciones.detail', order_id=order_id))

    deleg = request.form.get('delegacion', '').strip()
    order.delegacion     = deleg if deleg in DELEGACIONES else None
    order.description    = request.form.get('description', '').strip() or order.description
    est = request.form.get('estimated_days', '').strip()
    order.estimated_days = int(est) if est.isdigit() else None
    cost_raw = request.form.get('cost', '').strip()
    try:
        order.cost = float(cost_raw) if cost_raw else None
    except ValueError:
        pass

    db.session.commit()
    flash('Parte actualizado.', 'success')
    return redirect(url_for('reparaciones.detail', order_id=order_id))
