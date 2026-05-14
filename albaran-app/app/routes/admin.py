import json
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func, case
from app import db
from app.constants import DELEGACIONES
from app.auth.models import User, UserPermission, UserPermissionTarget, AuditLog
from app.auth.decorators import jefe_required, permission_required
from app.auth.helpers import log_action

bp = Blueprint('admin', __name__, url_prefix='/admin')

PERMISSIONS = [
    ('ver_historial_global',      'Ver historial de todos los usuarios'),
    ('ver_historial_parcial',     'Ver historial de usuarios seleccionados'),
    ('conceder_permisos',         'Gestionar permisos de trabajadores'),
    ('ver_albaranes_todas',       'Ver albaranes de todas las delegaciones'),
    ('ver_albaranes_delegacion',  'Ver albaranes de delegaciones específicas'),
    ('ver_estadisticas',          'Ver estadísticas de la empresa'),
]

# Permisos que requieren un permiso especial para concederse (no escalables)
# Solo el jefe puede otorgar estos permisos, aunque haya delegado conceder_permisos.
HIGH_PRIVILEGE_PERMS = {
    'ver_historial_global',
    'conceder_permisos',
    'ver_albaranes_todas',
    'ver_estadisticas',
}


# ── Historial global ──────────────────────────────────────────────────────────

@bp.route('/historial')
@login_required
def historial():
    if not (current_user.is_jefe or current_user.has_permission('ver_historial_global')):
        # ver_historial_parcial: limitado a sus targets
        perm = current_user.get_active_permission('ver_historial_parcial')
        if not perm:
            abort(403)
        allowed_ids = [t.target_user_id for t in perm.targets.all()] + [current_user.id]
        base_query = AuditLog.query.filter(AuditLog.user_id.in_(allowed_ids))
    else:
        base_query = AuditLog.query

    # Filtros
    user_f   = request.args.get('user_id', '', type=str)
    action_f = request.args.get('action', '')
    entity_f = request.args.get('entity', '')

    if user_f:
        base_query = base_query.filter_by(user_id=int(user_f))
    if action_f:
        base_query = base_query.filter_by(action=action_f)
    if entity_f:
        base_query = base_query.filter_by(entity=entity_f)

    page = request.args.get('page', 1, type=int)
    pagination = (base_query
                  .order_by(AuditLog.timestamp.desc())
                  .paginate(page=page, per_page=25, error_out=False))

    entries = []
    for e in pagination.items:
        diff_data = None
        if e.diff:
            try:
                diff_data = json.loads(e.diff)
            except Exception:
                diff_data = e.diff
        entries.append((e, diff_data))

    users = User.query.order_by(User.username).all()
    return render_template('admin/historial.html',
                           pagination=pagination,
                           entries=entries,
                           users=users,
                           user_f=user_f,
                           action_f=action_f,
                           entity_f=entity_f)


# ── Usuarios ──────────────────────────────────────────────────────────────────

@bp.route('/permisos')
@login_required
@jefe_required
def permisos():
    """Panel de solo lectura: permisos actuales de cada trabajador."""
    workers = User.query.filter_by(role='worker').order_by(User.username).all()
    return render_template('admin/permisos.html',
                           workers=workers,
                           delegaciones=DELEGACIONES)


@bp.route('/usuarios')
@login_required
@permission_required('conceder_permisos')
def usuarios():
    users = User.query.order_by(User.username).all()
    all_users = users  # para el selector de targets
    return render_template('admin/usuarios.html',
                           users=users,
                           all_users=all_users,
                           permissions=PERMISSIONS,
                           delegaciones=DELEGACIONES,
                           high_privilege_perms=HIGH_PRIVILEGE_PERMS,
                           is_jefe=current_user.is_jefe)


@bp.route('/usuarios/new', methods=['GET', 'POST'])
@login_required
@jefe_required
def nuevo_usuario():
    if request.method == 'POST':
        username   = request.form['username'].strip()
        full_name  = request.form['full_name'].strip()
        password   = request.form['password']
        role       = request.form.get('role', 'worker')
        delegacion = request.form.get('delegacion') or None

        if not username or not full_name or not password:
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('admin/nuevo_usuario.html', delegaciones=DELEGACIONES)

        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
            return render_template('admin/nuevo_usuario.html', delegaciones=DELEGACIONES)

        if User.query.filter_by(username=username).first():
            flash(f'El usuario "{username}" ya existe.', 'danger')
            return render_template('admin/nuevo_usuario.html', delegaciones=DELEGACIONES)

        user = User(
            username=username,
            full_name=full_name,
            role=role,
            delegacion=delegacion,
            must_change_password=True,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        log_action('created', 'user', user.id, user.username)
        db.session.commit()
        flash(f'Usuario {username} creado. Deberá cambiar su contraseña al entrar.', 'success')
        return redirect(url_for('admin.usuarios'))

    return render_template('admin/nuevo_usuario.html', delegaciones=DELEGACIONES)


@bp.route('/usuarios/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@jefe_required
def toggle_active(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        flash('No puedes desactivar tu propia cuenta.', 'danger')
        return redirect(url_for('admin.usuarios'))
    old_active = user.is_active
    user.is_active = not old_active
    log_action('updated', 'user', user.id, user.username,
               diff={'is_active': [old_active, user.is_active]})
    db.session.commit()
    estado = 'activado' if user.is_active else 'desactivado'
    flash(f'Usuario {user.username} {estado}.', 'success')
    return redirect(url_for('admin.usuarios'))


@bp.route('/usuarios/<int:user_id>/grant-permission', methods=['POST'])
@login_required
@permission_required('conceder_permisos')
def grant_permission(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if not user.is_active:
        flash('No se pueden conceder permisos a usuarios desactivados.', 'danger')
        return redirect(url_for('admin.usuarios'))
    if user.is_jefe:
        flash('Los jefes ya tienen todos los permisos.', 'warning')
        return redirect(url_for('admin.usuarios'))

    perm_name = request.form.get('permission', '')
    valid_perms = {p[0] for p in PERMISSIONS}
    if perm_name not in valid_perms:
        abort(400)

    # Anti-escalada: solo el jefe puede otorgar permisos de alto privilegio.
    if perm_name in HIGH_PRIVILEGE_PERMS and not current_user.is_jefe:
        flash('Solo el jefe puede otorgar este permiso.', 'danger')
        return redirect(url_for('admin.usuarios'))

    # No permitir auto-concesión (ni siquiera al jefe — usa role en su lugar)
    if user.id == current_user.id:
        flash('No puedes concederte permisos a ti mismo.', 'danger')
        return redirect(url_for('admin.usuarios'))

    existing = user.get_active_permission(perm_name)
    if existing:
        flash(f'El usuario ya tiene el permiso "{perm_name}".', 'warning')
        return redirect(url_for('admin.usuarios'))

    perm = UserPermission(
        user_id=user.id,
        permission=perm_name,
        granted_by=current_user.id,
    )
    db.session.add(perm)
    db.session.flush()

    if perm_name == 'ver_historial_parcial':
        target_ids = request.form.getlist('targets[]')
        for tid in target_ids:
            if tid.isdigit():
                db.session.add(UserPermissionTarget(
                    permission_id=perm.id,
                    target_user_id=int(tid),
                ))

    if perm_name == 'ver_albaranes_delegacion':
        target_delegaciones = request.form.getlist('delegaciones[]')
        for d in target_delegaciones:
            if d in DELEGACIONES:
                db.session.add(UserPermissionTarget(
                    permission_id=perm.id,
                    target_delegacion=d,
                ))

    log_action('permission_granted', 'permission', perm.id,
               f'{perm_name} → {user.username}')
    user.invalidate_permission_cache()
    db.session.commit()
    flash(f'Permiso "{perm_name}" concedido a {user.username}.', 'success')
    return redirect(url_for('admin.usuarios'))


@bp.route('/usuarios/<int:user_id>/revoke-permission/<int:perm_id>', methods=['POST'])
@login_required
@permission_required('conceder_permisos')
def revoke_permission(user_id, perm_id):
    perm = db.session.get(UserPermission, perm_id)
    if not perm or perm.user_id != user_id:
        abort(404)
    # Anti-escalada: solo el jefe puede revocar permisos de alto privilegio.
    if perm.permission in HIGH_PRIVILEGE_PERMS and not current_user.is_jefe:
        abort(403)

    perm.revoke()
    log_action('permission_revoked', 'permission', perm.id,
               f'{perm.permission} → {perm.user.username}')
    perm.user.invalidate_permission_cache()
    db.session.commit()
    flash(f'Permiso "{perm.permission}" revocado.', 'warning')
    return redirect(url_for('admin.usuarios'))


# ── Estadísticas ──────────────────────────────────────────────────────────────

@bp.route('/estadisticas')
@login_required
@permission_required('ver_estadisticas')
def estadisticas():
    from app.models import Machine, DeliveryNote, DeliveryNoteMachine, Client
    from app.constants import MACHINE_CATEGORIES

    # ── KPIs globales (una sola query por tipo para evitar N+1) ───────────────
    note_counts = dict(
        db.session.query(DeliveryNote.status, func.count(DeliveryNote.id))
        .group_by(DeliveryNote.status).all()
    )
    total_machines  = db.session.query(func.count(Machine.id)).scalar() or 0
    total_clients   = db.session.query(func.count(Client.id)).scalar() or 0
    total_albaranes = sum(note_counts.values())
    active_albaranes = note_counts.get('active', 0)
    closed_albaranes = note_counts.get('closed', 0)
    total_revenue   = db.session.query(
        func.sum(DeliveryNote.total_price)
    ).filter(DeliveryNote.status == 'closed').scalar() or 0.0

    # ── Estado de la flota ────────────────────────────────────────────────────
    fleet_by_status = db.session.query(
        Machine.status, func.count(Machine.id)
    ).group_by(Machine.status).all()
    fleet_status_map = {row[0]: row[1] for row in fleet_by_status}

    cat_labels_map = dict(MACHINE_CATEGORIES)

    fleet_by_cat = db.session.query(
        Machine.category,
        func.count(Machine.id).label('total'),
        func.sum(case((Machine.status == 'occupied', 1), else_=0)).label('occupied'),
        func.sum(case((Machine.status == 'repair',   1), else_=0)).label('repair'),
        func.sum(case((Machine.status == 'free',     1), else_=0)).label('free'),
    ).group_by(Machine.category).order_by(Machine.category).all()

    cat_stats = []
    for row in fleet_by_cat:
        total_cat = row.total or 0
        occ = row.occupied or 0
        cat_stats.append({
            'code':  row.category,
            'label': cat_labels_map.get(row.category, row.category),
            'total': total_cat,
            'occupied': occ,
            'repair': row.repair or 0,
            'free': row.free or 0,
            'pct_occupied': round(occ / total_cat * 100) if total_cat else 0,
        })

    # ── Máquinas más alquiladas ────────────────────────────────────────────────
    top_machines = db.session.query(
        Machine.code,
        Machine.name,
        Machine.category,
        Machine.status,
        func.count(DeliveryNoteMachine.id).label('rentals'),
    ).join(DeliveryNoteMachine, Machine.id == DeliveryNoteMachine.machine_id
    ).group_by(Machine.id
    ).order_by(func.count(DeliveryNoteMachine.id).desc()
    ).limit(10).all()

    # ── Clientes con más contratos ─────────────────────────────────────────────
    top_clients_contracts = db.session.query(
        Client.client_code,
        Client.company_name,
        func.count(DeliveryNote.id).label('contracts'),
        func.sum(case((DeliveryNote.status == 'active', 1), else_=0)).label('active'),
    ).join(DeliveryNote, Client.id == DeliveryNote.client_id
    ).group_by(Client.id
    ).order_by(func.count(DeliveryNote.id).desc()
    ).limit(10).all()

    # ── Clientes que más facturan ──────────────────────────────────────────────
    top_clients_revenue = db.session.query(
        Client.client_code,
        Client.company_name,
        func.sum(DeliveryNote.total_price).label('revenue'),
        func.count(DeliveryNote.id).label('contracts'),
    ).join(DeliveryNote, Client.id == DeliveryNote.client_id
    ).filter(DeliveryNote.status == 'closed'
    ).group_by(Client.id
    ).order_by(func.sum(DeliveryNote.total_price).desc()
    ).limit(10).all()

    # ── Máquinas con menor tasa de alquiler ───────────────────────────────────
    low_rate_machines = db.session.query(
        Machine.code,
        Machine.name,
        Machine.category,
        Machine.status,
        func.count(DeliveryNoteMachine.id).label('rentals'),
    ).join(DeliveryNoteMachine, Machine.id == DeliveryNoteMachine.machine_id
    ).group_by(Machine.id
    ).order_by(func.count(DeliveryNoteMachine.id).asc()
    ).limit(10).all()

    # ── Rendimiento por delegación ─────────────────────────────────────────────
    deleg_stats = db.session.query(
        DeliveryNote.delegacion,
        func.count(DeliveryNote.id).label('total'),
        func.sum(case((DeliveryNote.status == 'active', 1), else_=0)).label('active'),
        func.sum(case((DeliveryNote.status == 'closed', 1), else_=0)).label('closed'),
        func.sum(DeliveryNote.total_price).label('revenue'),
    ).filter(DeliveryNote.delegacion.isnot(None)
    ).group_by(DeliveryNote.delegacion
    ).order_by(func.count(DeliveryNote.id).desc()
    ).all()

    # ── Tendencia mensual de ingresos ──────────────────────────────────────────
    monthly_revenue = db.session.query(
        func.strftime('%Y-%m', DeliveryNote.rental_end).label('month'),
        func.sum(DeliveryNote.total_price).label('revenue'),
        func.count(DeliveryNote.id).label('count'),
    ).filter(
        DeliveryNote.status == 'closed',
        DeliveryNote.rental_end.isnot(None),
    ).group_by('month').order_by('month').limit(24).all()

    # Filter out None months and format
    monthly_revenue = [(r.month, r.revenue or 0, r.count) for r in monthly_revenue if r.month]

    return render_template('admin/estadisticas.html',
        # KPIs
        total_machines=total_machines,
        total_clients=total_clients,
        total_albaranes=total_albaranes,
        active_albaranes=active_albaranes,
        closed_albaranes=closed_albaranes,
        total_revenue=total_revenue,
        # Fleet
        fleet_status_map=fleet_status_map,
        cat_stats=cat_stats,
        # Rankings
        top_machines=top_machines,
        top_clients_contracts=top_clients_contracts,
        top_clients_revenue=top_clients_revenue,
        low_rate_machines=low_rate_machines,
        # Delegation
        deleg_stats=deleg_stats,
        delegaciones=DELEGACIONES,
        # Trend
        monthly_revenue=monthly_revenue,
        cat_labels_map=cat_labels_map,
    )
