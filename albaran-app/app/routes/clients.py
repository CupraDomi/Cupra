import re
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import Client, ClientContact, DeliveryNote, next_client_code, suggest_client_abbrev
from app.auth.helpers import log_action, make_diff

bp = Blueprint('clients', __name__)

# Validaciones ligeras
_ABBREV_RE = re.compile(r'^[A-Z0-9]{2,8}$')
_EMAIL_RE  = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_PHONE_RE  = re.compile(r'^[\d\s+\-()]{6,30}$')
_TAX_RE    = re.compile(r'^[A-Z0-9\-]{6,20}$')


def _validate_client_fields(form):
    """Devuelve lista de errores (vacía si todo OK)."""
    errors = []
    name = form.get('company_name', '').strip()
    if not name:
        errors.append('El nombre de la empresa es obligatorio.')
    email = form.get('email', '').strip()
    if email and not _EMAIL_RE.match(email):
        errors.append('El email no tiene formato válido.')
    phone = form.get('phone', '').strip()
    if phone and not _PHONE_RE.match(phone):
        errors.append('El teléfono solo puede contener dígitos, espacios, + - ( ).')
    tax_id = form.get('tax_id', '').strip().upper()
    if tax_id and not _TAX_RE.match(tax_id):
        errors.append('El CIF/NIF tiene caracteres no válidos.')
    return errors


@bp.route('/')
@login_required
def index():
    search = request.args.get('q', '').strip()
    page   = request.args.get('page', 1, type=int)
    q = Client.query
    if search:
        like = f'%{search}%'
        q = q.filter(
            db.or_(
                Client.company_name.ilike(like),
                Client.client_code.ilike(like),
                Client.tax_id.ilike(like),
            )
        )
    pagination = (q.order_by(Client.company_name)
                   .paginate(page=page, per_page=50, error_out=False))

    # Pre-cargar conteos de albaranes activos por cliente (una sola query)
    visible_ids = [c.id for c in pagination.items]
    active_counts = {}
    if visible_ids:
        rows = (db.session.query(DeliveryNote.client_id, func.count(DeliveryNote.id))
                .filter(DeliveryNote.client_id.in_(visible_ids),
                        DeliveryNote.status == 'active')
                .group_by(DeliveryNote.client_id).all())
        active_counts = dict(rows)

    return render_template('clients/index.html',
                           clients=pagination.items,
                           pagination=pagination, search=search,
                           active_counts=active_counts)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        errors = _validate_client_fields(request.form)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('clients/form.html', client=None, contacts=[])

        abbrev = request.form.get('abbrev', '').strip().upper()
        if not abbrev:
            abbrev = suggest_client_abbrev(request.form.get('company_name', ''))
        if not _ABBREV_RE.match(abbrev):
            flash('La abreviatura debe ser 2-8 letras/dígitos en mayúsculas.', 'danger')
            return render_template('clients/form.html', client=None, contacts=[])
        code = next_client_code(abbrev)

        client = Client(
            client_code   = code,
            client_type   = request.form.get('client_type', 'company'),
            company_name  = request.form['company_name'].strip(),
            tax_id        = request.form.get('tax_id', '').strip().upper() or None,
            address       = request.form.get('address', '').strip() or None,
            phone         = request.form.get('phone', '').strip() or None,
            email         = request.form.get('email', '').strip() or None,
            notes         = request.form.get('notes', '').strip() or None,
            created_by_id = current_user.id,
        )
        db.session.add(client)
        db.session.flush()

        _save_contacts(client.id, request.form)
        log_action('created', 'client', client.id, f'{client.client_code} {client.company_name}')
        try:
            db.session.commit()
            flash(f'Cliente {client.client_code} creado.', 'success')
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url + f'?client_id={client.id}')
            return redirect(url_for('clients.detail', client_id=client.id))
        except Exception:
            db.session.rollback()
            flash('Error al guardar el cliente.', 'danger')

    return render_template('clients/form.html', client=None, contacts=[])


@bp.route('/<int:client_id>')
@login_required
def detail(client_id):
    client = Client.query.get_or_404(client_id)
    contacts = client.contacts.all()
    notes = (client.delivery_notes
             .order_by(DeliveryNote.created_at.desc())
             .all())
    return render_template('clients/detail.html',
                           client=client, contacts=contacts, notes=notes)


@bp.route('/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        errors = _validate_client_fields(request.form)
        if errors:
            for e in errors:
                flash(e, 'danger')
            contacts = client.contacts.all()
            return render_template('clients/form.html', client=client, contacts=contacts)

        old = {
            'company_name': client.company_name,
            'client_type':  client.client_type,
            'tax_id':       client.tax_id,
            'address':      client.address,
            'phone':        client.phone,
            'email':        client.email,
            'notes':        client.notes,
        }
        client.client_type  = request.form.get('client_type', 'company')
        client.company_name = request.form['company_name'].strip()
        client.tax_id       = request.form.get('tax_id', '').strip().upper() or None
        client.address      = request.form.get('address', '').strip() or None
        client.phone        = request.form.get('phone', '').strip() or None
        client.email        = request.form.get('email', '').strip() or None
        client.notes        = request.form.get('notes', '').strip() or None
        client.updated_by_id = current_user.id
        client.updated_at    = datetime.now(timezone.utc)

        ClientContact.query.filter_by(client_id=client.id).delete()
        _save_contacts(client.id, request.form)

        new = {
            'company_name': client.company_name,
            'client_type':  client.client_type,
            'tax_id':       client.tax_id,
            'address':      client.address,
            'phone':        client.phone,
            'email':        client.email,
            'notes':        client.notes,
        }
        log_action('updated', 'client', client.id,
                   f'{client.client_code} {client.company_name}',
                   diff=make_diff(old, new))
        try:
            db.session.commit()
            flash('Cliente actualizado.', 'success')
            return redirect(url_for('clients.detail', client_id=client.id))
        except Exception:
            db.session.rollback()
            flash('Error al guardar.', 'danger')

    contacts = client.contacts.all()
    return render_template('clients/form.html', client=client, contacts=contacts)


@bp.route('/<int:client_id>/delete', methods=['POST'])
@login_required
def delete(client_id):
    client = Client.query.get_or_404(client_id)
    # No permitir borrar clientes con albaranes
    if client.delivery_notes.count() > 0:
        flash('No se puede eliminar un cliente con albaranes asociados.', 'danger')
        return redirect(url_for('clients.detail', client_id=client_id))

    label = f'{client.client_code} {client.company_name}'
    client.deleted_by_id = current_user.id
    client.deleted_at    = datetime.now(timezone.utc)
    log_action('deleted', 'client', client.id, label)
    db.session.delete(client)
    db.session.commit()
    flash(f'Cliente {client.client_code} eliminado.', 'warning')
    return redirect(url_for('clients.index'))


@bp.route('/suggest-abbrev')
@login_required
def suggest_abbrev():
    name = request.args.get('name', '')
    return jsonify({'abbrev': suggest_client_abbrev(name)})


@bp.route('/search-json')
@login_required
def search_json():
    q = request.args.get('q', '').strip()
    query = Client.query
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                Client.company_name.ilike(like),
                Client.client_code.ilike(like),
                Client.tax_id.ilike(like),
            )
        )
    clients = query.order_by(Client.company_name).limit(20).all()
    return jsonify([{
        'id': c.id,
        'client_code': c.client_code,
        'company_name': c.company_name,
        'tax_id': c.tax_id or '',
        'phone': c.phone or '',
    } for c in clients])


def _save_contacts(client_id, form):
    names  = form.getlist('contact_name[]')
    roles  = form.getlist('contact_role[]')
    phones = form.getlist('contact_phone[]')
    emails = form.getlist('contact_email[]')
    for i, name in enumerate(names):
        if not name.strip():
            continue
        db.session.add(ClientContact(
            client_id = client_id,
            name  = name.strip(),
            role  = (roles[i].strip()  if i < len(roles)  else '') or None,
            phone = (phones[i].strip() if i < len(phones) else '') or None,
            email = (emails[i].strip() if i < len(emails) else '') or None,
        ))
