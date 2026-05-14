import re
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.constants import MACHINE_CATEGORIES, MACHINE_STATUSES
from app.models import Machine, MachineStatusLog, RepairOrder
from app.auth.helpers import log_action, make_diff

bp = Blueprint('machines', __name__)

# Reexportados para retro-compatibilidad con tests / admin
CATEGORIES = MACHINE_CATEGORIES
STATUSES   = MACHINE_STATUSES

_VALID_CATS     = {c for c, _ in MACHINE_CATEGORIES}
_VALID_STATUSES = {s for s, _ in MACHINE_STATUSES}
_CODE_RE        = re.compile(r'^[A-Z0-9\-_]{2,30}$')


@bp.route('/')
@login_required
def index():
    search = request.args.get('q', '').strip()
    cat    = request.args.get('cat', '')
    status = request.args.get('status', '')

    q = Machine.query
    if search:
        like = f'%{search}%'
        q = q.filter(
            db.or_(Machine.code.ilike(like), Machine.name.ilike(like))
        )
    if cat in _VALID_CATS:
        q = q.filter_by(category=cat)
    if status in _VALID_STATUSES:
        q = q.filter_by(status=status)

    machines = q.order_by(Machine.category, Machine.code).all()

    groups = {code: {'label': label, 'machines': []} for code, label in MACHINE_CATEGORIES}
    for m in machines:
        if m.category in groups:
            groups[m.category]['machines'].append(m)
        else:
            groups.setdefault(m.category, {'label': m.category, 'machines': []})['machines'].append(m)
    groups = {k: v for k, v in groups.items() if v['machines']}

    return render_template('machines/index.html',
                           groups=groups,
                           total=len(machines),
                           categories=MACHINE_CATEGORIES,
                           statuses=MACHINE_STATUSES,
                           search=search, cat=cat, status=status)


@bp.route('/flota')
@login_required
def flota():
    return redirect(url_for('machines.index'))


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        if not _CODE_RE.match(code):
            flash('El código debe ser 2-30 caracteres en mayúsculas, dígitos, "-" o "_".', 'danger')
            return render_template('machines/form.html',
                                   machine=None, categories=MACHINE_CATEGORIES, statuses=MACHINE_STATUSES)

        status = request.form.get('status', 'free')
        if status not in _VALID_STATUSES:
            status = 'free'
        category = request.form.get('category', '')
        if category not in _VALID_CATS:
            flash('Categoría no válida.', 'danger')
            return render_template('machines/form.html',
                                   machine=None, categories=MACHINE_CATEGORIES, statuses=MACHINE_STATUSES)

        machine = Machine(
            code         = code,
            name         = request.form['name'].strip(),
            category     = category,
            variant      = request.form.get('variant', '').strip() or None,
            specs        = request.form.get('specs', '').strip() or None,
            status       = status,
            notes        = request.form.get('notes', '').strip() or None,
            repair_notes = request.form.get('repair_notes', '').strip() if status == 'repair' else None,
            created_by_id = current_user.id,
        )
        db.session.add(machine)
        db.session.flush()
        log_action('created', 'machine', machine.id, machine.code)
        try:
            db.session.commit()
            flash(f'Máquina {machine.code} creada correctamente.', 'success')
            return redirect(url_for('machines.detail', machine_id=machine.id))
        except Exception:
            db.session.rollback()
            flash('Error: el código ya existe o hay un campo inválido.', 'danger')

    return render_template('machines/form.html',
                           machine=None,
                           categories=MACHINE_CATEGORIES,
                           statuses=MACHINE_STATUSES)


@bp.route('/<int:machine_id>')
@login_required
def detail(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    logs = (MachineStatusLog.query
            .filter_by(machine_id=machine_id)
            .order_by(MachineStatusLog.changed_at.desc())
            .limit(20).all())
    from app.models import DeliveryNoteMachine, DeliveryNote
    active = (db.session.query(DeliveryNote)
              .join(DeliveryNoteMachine)
              .filter(DeliveryNoteMachine.machine_id == machine_id,
                      DeliveryNote.status == 'active')
              .all())
    return render_template('machines/detail.html',
                           machine=machine, logs=logs, active_notes=active)


@bp.route('/<int:machine_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    if request.method == 'POST':
        old = {
            'name': machine.name, 'category': machine.category,
            'variant': machine.variant, 'specs': machine.specs,
            'status': machine.status, 'notes': machine.notes,
            'repair_notes': machine.repair_notes,
        }
        category = request.form.get('category', machine.category)
        if category not in _VALID_CATS:
            flash('Categoría no válida.', 'danger')
            return render_template('machines/form.html',
                                   machine=machine, categories=MACHINE_CATEGORIES, statuses=MACHINE_STATUSES)
        machine.name     = request.form['name'].strip()
        machine.category = category
        machine.variant  = request.form.get('variant', '').strip() or None
        machine.specs    = request.form.get('specs', '').strip() or None
        machine.notes    = request.form.get('notes', '').strip() or None

        old_status = old['status']
        new_status = request.form.get('status', old_status)
        if new_status not in _VALID_STATUSES:
            new_status = old_status
        machine.repair_notes = (
            request.form.get('repair_notes', '').strip() or None
            if new_status == 'repair' else None
        )
        if old_status != new_status:
            machine.status = new_status
            db.session.add(MachineStatusLog(
                machine_id=machine.id,
                old_status=old_status,
                new_status=new_status,
                delivery_note_id=None,
                changed_by=current_user.username,
            ))
            # Crear parte de reparación al entrar en 'repair'
            if new_status == 'repair':
                db.session.add(RepairOrder(
                    machine_id    = machine.id,
                    delegacion    = machine.current_delegacion,
                    description   = machine.repair_notes,
                    status        = 'open',
                    created_at    = datetime.now(timezone.utc),
                    created_by_id = current_user.id,
                ))
            # Cerrar parte abierto al salir de 'repair'
            elif old_status == 'repair':
                open_order = (RepairOrder.query
                              .filter_by(machine_id=machine.id, status='open')
                              .first())
                if open_order:
                    open_order.status    = 'closed'
                    open_order.closed_at = datetime.now(timezone.utc)
                    open_order.closed_by_id = current_user.id

        machine.updated_by_id = current_user.id
        machine.updated_at    = datetime.now(timezone.utc)

        new = {
            'name': machine.name, 'category': machine.category,
            'variant': machine.variant, 'specs': machine.specs,
            'status': machine.status, 'notes': machine.notes,
            'repair_notes': machine.repair_notes,
        }
        log_action('updated', 'machine', machine.id, machine.code, diff=make_diff(old, new))
        try:
            db.session.commit()
            flash('Máquina actualizada.', 'success')
            return redirect(url_for('machines.detail', machine_id=machine.id))
        except Exception:
            db.session.rollback()
            flash('Error al guardar los cambios.', 'danger')

    return render_template('machines/form.html',
                           machine=machine,
                           categories=MACHINE_CATEGORIES,
                           statuses=MACHINE_STATUSES)


@bp.route('/<int:machine_id>/delete', methods=['POST'])
@login_required
def delete(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    if machine.status == 'occupied':
        flash('No se puede eliminar una máquina ocupada en un albarán activo.', 'danger')
        return redirect(url_for('machines.detail', machine_id=machine_id))
    label = machine.code
    machine.deleted_by_id = current_user.id
    machine.deleted_at    = datetime.now(timezone.utc)
    log_action('deleted', 'machine', machine.id, label)
    db.session.delete(machine)
    db.session.commit()
    flash(f'Máquina {label} eliminada.', 'warning')
    return redirect(url_for('machines.index'))


@bp.route('/search-json')
@login_required
def search_json():
    q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '')
    query = Machine.query
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(Machine.code.ilike(like), Machine.name.ilike(like))
        )
    if status_filter in _VALID_STATUSES:
        query = query.filter_by(status=status_filter)
    machines = query.order_by(Machine.code).limit(20).all()
    return jsonify([{
        'id': m.id, 'code': m.code, 'name': m.name,
        'status': m.status, 'status_label': m.status_label,
        'category': m.category,
    } for m in machines])
