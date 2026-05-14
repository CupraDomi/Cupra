import json
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import bp
from app.auth.models import User, AuditLog
from app import db, limiter


def _log_auth(action, user):
    entry = AuditLog(
        user_id=user.id,
        action=action,
        entity='user',
        entity_id=user.id,
        entity_label=user.username,
        ip_address=request.remote_addr,
    )
    db.session.add(entry)
    db.session.commit()


# ── Setup: create the first jefe account ─────────────────────────────────────

@bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """Only accessible when no users exist yet."""
    if User.query.first():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        full_name = request.form['full_name'].strip()

        if not username or not password or not full_name:
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('auth/setup.html')

        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
            return render_template('auth/setup.html')

        user = User(username=username, full_name=full_name, role='jefe')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        _log_auth('login', user)
        login_user(user)
        flash(f'Bienvenido, {full_name}. Cuenta de administrador creada.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/setup.html')


# ── Login ─────────────────────────────────────────────────────────────────────

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute; 60 per hour', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    # If no users exist yet, go to setup
    if not User.query.first():
        return redirect(url_for('auth.setup'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Usuario o contraseña incorrectos.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Tu cuenta está desactivada. Contacta con el administrador.', 'danger')
            return render_template('auth/login.html')

        login_user(user, remember=remember)
        _log_auth('login', user)

        if user.must_change_password:
            flash('Debes cambiar tu contraseña antes de continuar.', 'warning')
            return redirect(url_for('auth.change_password'))

        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard.index'))

    return render_template('auth/login.html')


# ── Logout ────────────────────────────────────────────────────────────────────

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    _log_auth('logout', current_user)
    logout_user()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('auth.login'))


# ── Change password ───────────────────────────────────────────────────────────

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw = request.form['current_password']
        new_pw = request.form['new_password']
        confirm_pw = request.form['confirm_password']

        if not current_user.check_password(current_pw):
            flash('La contraseña actual es incorrecta.', 'danger')
            return render_template('auth/change_password.html')

        if len(new_pw) < 8:
            flash('La nueva contraseña debe tener al menos 8 caracteres.', 'danger')
            return render_template('auth/change_password.html')

        if new_pw != confirm_pw:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('auth/change_password.html')

        current_user.set_password(new_pw)
        current_user.must_change_password = False
        db.session.commit()
        flash('Contraseña actualizada correctamente.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/change_password.html')


# ── Historial propio ──────────────────────────────────────────────────────────

@bp.route('/historial')
@login_required
def historial():
    page = request.args.get('page', 1, type=int)

    # Usuarios cuyo historial puede ver este user
    # Jefe → todos | ver_historial_global → todos | ver_historial_parcial → targets
    if current_user.is_jefe or current_user.has_permission('ver_historial_global'):
        # El panel /admin/historial muestra el historial global.
        # Aquí mostramos solo el propio para no duplicar.
        query = AuditLog.query.filter_by(user_id=current_user.id)
    else:
        allowed_ids = [current_user.id]
        perm = current_user.get_active_permission('ver_historial_parcial')
        if perm:
            allowed_ids += [t.target_user_id for t in perm.targets.all()]
        query = AuditLog.query.filter(AuditLog.user_id.in_(allowed_ids))

    pagination = (query
                  .order_by(AuditLog.timestamp.desc())
                  .paginate(page=page, per_page=25, error_out=False))

    # Pre-parsear diffs para el template
    entries = []
    for e in pagination.items:
        diff_data = None
        if e.diff:
            try:
                diff_data = json.loads(e.diff)
            except Exception:
                diff_data = e.diff
        entries.append((e, diff_data))

    return render_template('auth/historial.html',
                           pagination=pagination,
                           entries=entries)
