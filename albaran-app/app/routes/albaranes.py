import secrets
from datetime import date, datetime, timezone, timedelta
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, send_file, abort, jsonify)
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from app import db
from app.constants import DELEGACIONES, ALBARAN_STATUSES
from app.models import (DeliveryNote, DeliveryNoteMachine, Machine,
                        Client, MachineStatusLog,
                        next_albaran_number, next_invoice_number)
from app.pdf_generator import generate_albaran_pdf
from app.invoice_generator import generate_invoice_pdf
from app.auth.helpers import log_action, make_diff
from app.auth.decorators import (allowed_delegaciones, require_albaran_view,
                                 can_view_albaran)
import io

bp = Blueprint('albaranes', __name__)

VALID_STATUSES = {s for s, _ in ALBARAN_STATUSES}


def _can_modify(user, note=None):
    """
    Cualquier usuario autenticado puede crear albaranes. Para editar/cerrar/
    cancelar uno existente, además debe tener acceso a su delegación.
    """
    if not user.is_authenticated:
        return False
    if note is None:
        return True
    return can_view_albaran(user, note)


def _ensure_can_modify(note=None):
    if not _can_modify(current_user, note):
        abort(403)


# ── Listado ──────────────────────────────────────────────────────────────────

@bp.route('/')
@login_required
def index():
    search       = request.args.get('q', '').strip()
    status_f     = request.args.get('status', '')
    client_f     = request.args.get('client_id', '')
    date_from    = request.args.get('date_from', '')
    date_to      = request.args.get('date_to', '')
    delegacion_f = request.args.get('delegacion', '')
    page         = request.args.get('page', 1, type=int)

    q = DeliveryNote.query

    # Access control por delegación
    allowed = allowed_delegaciones(current_user)
    if allowed is not None:
        # NULL en delegacion → visible siempre (compat. histórica de albaranes legacy)
        q = q.filter(
            db.or_(
                DeliveryNote.delegacion.is_(None),
                DeliveryNote.delegacion.in_(list(allowed) or ['__none__']),
            )
        )

    if search:
        like = f'%{search}%'
        q = q.filter(
            db.or_(
                DeliveryNote.albaran_number.ilike(like),
                DeliveryNote.location.ilike(like),
                DeliveryNote.created_by.ilike(like),
            )
        )
    if status_f in VALID_STATUSES:
        q = q.filter_by(status=status_f)
    if client_f and client_f.isdigit():
        q = q.filter_by(client_id=int(client_f))
    if date_from:
        q = q.filter(DeliveryNote.rental_start >= date_from)
    if date_to:
        q = q.filter(DeliveryNote.rental_start <= date_to)
    if delegacion_f in DELEGACIONES:
        q = q.filter_by(delegacion=delegacion_f)

    # Eager-load el cliente (joinedload). machines es lazy='dynamic' y no
    # soporta selectinload — lo cargamos en batch más abajo.
    q = q.options(joinedload(DeliveryNote.client))

    pagination = (q.order_by(DeliveryNote.created_at.desc())
                   .paginate(page=page, per_page=50, error_out=False))

    # Pre-fetch en batch de las máquinas de los albaranes visibles, evitando N+1.
    note_ids = [n.id for n in pagination.items]
    machines_by_note = {nid: [] for nid in note_ids}
    if note_ids:
        rows = (DeliveryNoteMachine.query
                .filter(DeliveryNoteMachine.delivery_note_id.in_(note_ids))
                .options(joinedload(DeliveryNoteMachine.machine))
                .all())
        for dnm in rows:
            machines_by_note[dnm.delivery_note_id].append(dnm)

    clients = Client.query.order_by(Client.company_name).all()
    return render_template('albaranes/index.html',
                           notes=pagination.items, pagination=pagination,
                           machines_by_note=machines_by_note,
                           clients=clients,
                           search=search, status_f=status_f,
                           client_f=client_f, date_from=date_from, date_to=date_to,
                           delegacion_f=delegacion_f, delegaciones=DELEGACIONES)


# ── Step 1: new or existing client? ──────────────────────────────────────────

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_step1():
    _ensure_can_modify()
    client_id = request.args.get('client_id') or request.form.get('client_id')
    if client_id and client_id.isdigit():
        return redirect(url_for('albaranes.new_step2', client_id=client_id))

    if request.method == 'POST':
        choice = request.form.get('client_choice')
        if choice == 'existing':
            cid = request.form.get('existing_client_id')
            if cid and cid.isdigit():
                return redirect(url_for('albaranes.new_step2', client_id=cid))
            flash('Selecciona un cliente existente.', 'warning')
        elif choice == 'new':
            return redirect(url_for('clients.new',
                                    next=url_for('albaranes.new_step1')))

    clients = Client.query.order_by(Client.company_name).all()
    return render_template('albaranes/step1_client.html', clients=clients)


@bp.route('/new/step2')
@login_required
def new_step2():
    _ensure_can_modify()
    client_id = request.args.get('client_id')
    client = Client.query.get_or_404(client_id)
    machines = Machine.query.order_by(Machine.code).all()
    return render_template('albaranes/step2_form.html',
                           client=client,
                           machines=machines,
                           albaran_number=next_albaran_number(),
                           today=date.today().isoformat(),
                           delegaciones=DELEGACIONES,
                           default_delegacion=current_user.delegacion or '')


@bp.route('/new/save', methods=['POST'])
@login_required
def save():
    _ensure_can_modify()
    try:
        client_id    = int(request.form['client_id'])
        pricing_mode = request.form.get('pricing_mode', 'open')
        if pricing_mode not in ('open', 'closed'):
            pricing_mode = 'open'
        machine_ids  = [int(m) for m in request.form.getlist('machine_ids[]') if m.isdigit()]
        rental_end   = request.form.get('rental_end') or None
        rental_start = date.fromisoformat(request.form['rental_start'])
    except (ValueError, KeyError):
        flash('Datos del albarán inválidos.', 'danger')
        return redirect(url_for('albaranes.new_step1'))

    if pricing_mode == 'closed':
        total_price = float(request.form.get('total_price') or 0)
        price_rate  = None
        price_unit  = None
    else:
        total_price = None
        price_rate  = float(request.form.get('price_rate') or 0) or None
        price_unit  = request.form.get('price_unit') or None
        if price_unit not in (None, 'day', 'week', 'month'):
            price_unit = None

    submitted_deleg = request.form.get('delegacion', '')
    delegacion = submitted_deleg if submitted_deleg in DELEGACIONES else (current_user.delegacion or None)

    # Reintentos en caso de colisión de numeración (race condition)
    last_err = None
    for attempt in range(3):
        try:
            note = DeliveryNote(
                albaran_number = next_albaran_number(),
                client_id      = client_id,
                rental_start   = rental_start,
                rental_end     = date.fromisoformat(rental_end) if rental_end else None,
                pricing_mode   = pricing_mode,
                price_rate     = price_rate,
                price_unit     = price_unit,
                total_price    = total_price,
                delegacion     = delegacion,
                location       = request.form.get('location', '').strip(),
                notes          = request.form.get('notes', '').strip(),
                created_by     = current_user.username,   # legacy VARCHAR
                created_by_id  = current_user.id,
                status         = 'active',
            )
            db.session.add(note)
            db.session.flush()

            for mid in machine_ids:
                db.session.add(DeliveryNoteMachine(
                    delivery_note_id=note.id, machine_id=mid
                ))
                machine = db.session.get(Machine, mid)
                if machine:
                    old_status = machine.status
                    machine.status = 'occupied'
                    machine.current_delegacion = delegacion
                    db.session.add(MachineStatusLog(
                        machine_id=mid, old_status=old_status, new_status='occupied',
                        delivery_note_id=note.id,
                        changed_by=current_user.username,
                    ))

            log_action('created', 'delivery_note', note.id, note.albaran_number)
            db.session.commit()
            flash(f'Albarán {note.albaran_number} creado correctamente.', 'success')
            return redirect(url_for('albaranes.detail', note_id=note.id))
        except IntegrityError as e:
            db.session.rollback()
            last_err = e
            continue
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar el albarán: {e}', 'danger')
            return redirect(url_for('albaranes.new_step1'))

    flash(f'No se pudo asignar un número de albarán único: {last_err}', 'danger')
    return redirect(url_for('albaranes.new_step1'))


# ── Detail ────────────────────────────────────────────────────────────────────

@bp.route('/<int:note_id>')
@login_required
def detail(note_id):
    note = DeliveryNote.query.get_or_404(note_id)
    require_albaran_view(note)
    machines = [dnm.machine for dnm in note.machines.all()]
    return render_template('albaranes/detail.html', note=note, machines=machines,
                           can_modify=_can_modify(current_user),
                           delegaciones=DELEGACIONES)


# ── Edit ──────────────────────────────────────────────────────────────────────

@bp.route('/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(note_id):
    note = DeliveryNote.query.get_or_404(note_id)
    _ensure_can_modify(note)
    if note.status != 'active':
        flash('Solo se pueden editar albaranes activos.', 'warning')
        return redirect(url_for('albaranes.detail', note_id=note_id))

    if request.method == 'POST':
        old = {
            'rental_start': str(note.rental_start),
            'rental_end':   str(note.rental_end),
            'location':     note.location,
            'notes':        note.notes,
            'pricing_mode': note.pricing_mode,
            'price_rate':   note.price_rate,
            'price_unit':   note.price_unit,
            'total_price':  note.total_price,
            'delegacion':   note.delegacion,
        }
        try:
            note.rental_start = date.fromisoformat(request.form['rental_start'])
        except (KeyError, ValueError):
            flash('Fecha de inicio inválida.', 'danger')
            return redirect(url_for('albaranes.edit', note_id=note_id))

        rental_end = request.form.get('rental_end') or None
        note.rental_end     = date.fromisoformat(rental_end) if rental_end else None
        note.location       = request.form.get('location', '').strip()
        note.notes          = request.form.get('notes', '').strip()
        new_mode            = request.form.get('pricing_mode', note.pricing_mode)
        if new_mode not in ('open', 'closed'):
            new_mode = note.pricing_mode
        note.pricing_mode = new_mode

        submitted_deleg = request.form.get('delegacion', '')
        if submitted_deleg in DELEGACIONES:
            note.delegacion = submitted_deleg
        elif submitted_deleg == '':
            note.delegacion = None

        if note.pricing_mode == 'closed':
            note.total_price = float(request.form.get('total_price') or 0)
            note.price_rate  = None
            note.price_unit  = None
        else:
            new_rate = float(request.form.get('price_rate') or 0) or None
            new_unit = request.form.get('price_unit') or None
            if new_unit not in (None, 'day', 'week', 'month'):
                new_unit = None
            note.price_rate  = new_rate
            note.price_unit  = new_unit
            # No borramos total_price si ya estaba calculado y no hay tarifa nueva.
            # Solo se recalcula al cerrar el albarán.
            if new_rate is not None:
                note.total_price = None

        note.updated_by_id = current_user.id
        note.updated_at    = datetime.now(timezone.utc)

        new = {
            'rental_start': str(note.rental_start),
            'rental_end':   str(note.rental_end),
            'location':     note.location,
            'notes':        note.notes,
            'pricing_mode': note.pricing_mode,
            'price_rate':   note.price_rate,
            'price_unit':   note.price_unit,
            'total_price':  note.total_price,
            'delegacion':   note.delegacion,
        }
        log_action('updated', 'delivery_note', note.id, note.albaran_number,
                   diff=make_diff(old, new))
        try:
            db.session.commit()
            flash('Albarán actualizado.', 'success')
            return redirect(url_for('albaranes.detail', note_id=note_id))
        except Exception:
            db.session.rollback()
            flash('Error al guardar.', 'danger')

    machines = [dnm.machine for dnm in note.machines.all()]
    return render_template('albaranes/edit.html', note=note, machines=machines,
                           delegaciones=DELEGACIONES)


# ── Close ─────────────────────────────────────────────────────────────────────

@bp.route('/<int:note_id>/close', methods=['POST'])
@login_required
def close(note_id):
    note = DeliveryNote.query.get_or_404(note_id)
    _ensure_can_modify(note)
    if note.status != 'active':
        flash('Solo se pueden cerrar albaranes activos.', 'warning')
        return redirect(url_for('albaranes.detail', note_id=note_id))

    end_date = request.form.get('rental_end')
    if end_date:
        try:
            note.rental_end = date.fromisoformat(end_date)
        except ValueError:
            flash('Fecha de fin inválida.', 'danger')
            return redirect(url_for('albaranes.detail', note_id=note_id))

    if note.pricing_mode == 'open':
        override = request.form.get('total_price_override')
        try:
            override_val = float(override) if override else None
        except ValueError:
            override_val = None
        computed = note.calculated_total
        note.total_price = override_val if override_val is not None else computed

    # Guardia contra TypeError al formatear el flash
    if note.total_price is None:
        db.session.rollback()
        flash('No se pudo calcular el total: indica un precio o fecha de fin válidos.', 'danger')
        return redirect(url_for('albaranes.detail', note_id=note_id))

    note.status        = 'closed'
    note.updated_by_id = current_user.id
    note.updated_at    = datetime.now(timezone.utc)

    return_delegacion = request.form.get('return_delegacion', '').strip()
    if return_delegacion not in DELEGACIONES:
        return_delegacion = note.delegacion  # fallback a la delegación del albarán

    for dnm in note.machines.all():
        m = dnm.machine
        old_status = m.status
        m.status = 'free'
        if return_delegacion:
            m.current_delegacion = return_delegacion
        db.session.add(MachineStatusLog(
            machine_id=m.id, old_status=old_status, new_status='free',
            delivery_note_id=note.id,
            changed_by=current_user.username,
        ))

    log_action('updated', 'delivery_note', note.id, note.albaran_number,
               diff={'status': ['active', 'closed'], 'total_price': [None, note.total_price]})
    db.session.commit()
    flash(f'Albarán {note.albaran_number} cerrado. Total: {note.total_price:,.2f} €', 'success')
    return redirect(url_for('albaranes.detail', note_id=note_id))


# ── Cancel ────────────────────────────────────────────────────────────────────

@bp.route('/<int:note_id>/cancel', methods=['POST'])
@login_required
def cancel(note_id):
    note = DeliveryNote.query.get_or_404(note_id)
    _ensure_can_modify(note)
    if note.status != 'active':
        flash('Solo se pueden cancelar albaranes activos.', 'warning')
        return redirect(url_for('albaranes.detail', note_id=note_id))

    note.status        = 'cancelled'
    note.updated_by_id = current_user.id
    note.updated_at    = datetime.now(timezone.utc)

    for dnm in note.machines.all():
        m = dnm.machine
        old_status = m.status
        m.status = 'free'
        db.session.add(MachineStatusLog(
            machine_id=m.id, old_status=old_status, new_status='free',
            delivery_note_id=note.id, changed_by=current_user.username,
        ))

    log_action('updated', 'delivery_note', note.id, note.albaran_number,
               diff={'status': ['active', 'cancelled']})
    db.session.commit()
    flash(f'Albarán {note.albaran_number} cancelado.', 'warning')
    return redirect(url_for('albaranes.detail', note_id=note_id))


# ── Firma digital ────────────────────────────────────────────────────────────

@bp.route('/<int:note_id>/firma/solicitar', methods=['POST'])
@login_required
def solicitar_firma(note_id):
    note = DeliveryNote.query.get_or_404(note_id)
    _ensure_can_modify(note)

    if note.status != 'active':
        return jsonify({'error': 'Solo se puede firmar un albarán activo'}), 400

    token = secrets.token_urlsafe(32)
    note.signature_token         = token
    note.signature_token_expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    note.signature_data          = None
    note.signed_at               = None
    note.signer_name             = None
    db.session.commit()

    sign_url = url_for('firma.sign', token=token, _external=True)
    return jsonify({'url': sign_url})


@bp.route('/<int:note_id>/firma/estado')
@login_required
def firma_estado(note_id):
    note = DeliveryNote.query.get_or_404(note_id)
    require_albaran_view(note)
    return jsonify({
        'signed':      note.signed_at is not None,
        'signer_name': note.signer_name,
        'signed_at':   note.signed_at.strftime('%d/%m/%Y %H:%M') if note.signed_at else None,
    })


# ── PDF export (albarán) ──────────────────────────────────────────────────────

@bp.route('/<int:note_id>/pdf')
@login_required
def pdf(note_id):
    note = DeliveryNote.query.get_or_404(note_id)
    require_albaran_view(note)
    machines = [dnm.machine for dnm in note.machines.all()]
    buf = generate_albaran_pdf(note, machines)
    return send_file(
        io.BytesIO(buf),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{note.albaran_number}.pdf',
    )


# ── Factura: previsualización ─────────────────────────────────────────────────

def _assign_invoice_number(note):
    """Asigna un número de factura único con reintentos por race condition."""
    for attempt in range(3):
        try:
            note.invoice_number       = next_invoice_number()
            note.invoice_generated_at = datetime.now(timezone.utc)
            log_action('created', 'invoice', note.id,
                       f'Factura {note.invoice_number}')
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            note.invoice_number = None
            continue
    return False


@bp.route('/<int:note_id>/invoice/preview')
@login_required
def invoice_preview(note_id):
    note = DeliveryNote.query.get_or_404(note_id)
    require_albaran_view(note)

    if note.status != 'closed':
        flash('Solo se pueden facturar albaranes cerrados.', 'warning')
        return redirect(url_for('albaranes.detail', note_id=note_id))

    lang = request.args.get('lang', 'es')
    if lang not in ('es', 'en'):
        lang = 'es'

    if not note.invoice_number:
        if not _assign_invoice_number(note):
            flash('No se pudo asignar un número de factura.', 'danger')
            return redirect(url_for('albaranes.detail', note_id=note_id))

    return render_template('albaranes/invoice_preview.html',
                           note=note, lang=lang)


# ── Factura: PDF (inline o descarga) ─────────────────────────────────────────

@bp.route('/<int:note_id>/invoice')
@login_required
def invoice(note_id):
    note = DeliveryNote.query.get_or_404(note_id)
    require_albaran_view(note)

    if note.status != 'closed':
        flash('Solo se pueden facturar albaranes cerrados.', 'warning')
        return redirect(url_for('albaranes.detail', note_id=note_id))

    lang = request.args.get('lang', 'es')
    if lang not in ('es', 'en'):
        lang = 'es'

    if not note.invoice_number:
        if not _assign_invoice_number(note):
            flash('No se pudo asignar un número de factura.', 'danger')
            return redirect(url_for('albaranes.detail', note_id=note_id))

    machines = [dnm.machine for dnm in note.machines.all()]
    buf = generate_invoice_pdf(note, machines, lang=lang)
    as_attachment = request.args.get('download') == '1'

    return send_file(
        io.BytesIO(buf),
        mimetype='application/pdf',
        as_attachment=as_attachment,
        download_name=f'{note.invoice_number}.pdf',
    )
