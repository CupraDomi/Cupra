from datetime import datetime, date, timezone
from app import db


def _now():
    """Timestamp UTC aware. Usar en todos los defaults de columnas DateTime."""
    return datetime.now(timezone.utc)


# ── Machine ──────────────────────────────────────────────────────────────────

class Machine(db.Model):
    __tablename__ = 'machines'

    id         = db.Column(db.Integer, primary_key=True)
    code       = db.Column(db.String(30), unique=True, nullable=False)
    name       = db.Column(db.String(120), nullable=False)
    category   = db.Column(db.String(10), nullable=False, index=True)
    variant    = db.Column(db.String(20))
    specs      = db.Column(db.Text)
    status              = db.Column(db.String(10), nullable=False, default='free', index=True)
    current_delegacion  = db.Column(db.String(30), nullable=True)
    notes        = db.Column(db.Text)
    repair_notes = db.Column(db.Text, nullable=True)   # descripción del problema en reparación
    created_at   = db.Column(db.DateTime(timezone=True), default=_now)

    # ── Auditoría con FK (nullable — null para registros anteriores al sistema de users) ──
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at    = db.Column(db.DateTime(timezone=True), nullable=True)
    deleted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    deleted_at    = db.Column(db.DateTime(timezone=True), nullable=True)

    created_by_user = db.relationship('User', foreign_keys=[created_by_id])
    updated_by_user = db.relationship('User', foreign_keys=[updated_by_id])
    deleted_by_user = db.relationship('User', foreign_keys=[deleted_by_id])

    status_logs    = db.relationship('MachineStatusLog', backref='machine', lazy='dynamic')
    delivery_items = db.relationship('DeliveryNoteMachine', backref='machine', lazy='dynamic')

    @property
    def status_label(self):
        return {'free': 'Libre', 'occupied': 'Ocupada', 'reserved': 'Reservada',
                'repair': 'En reparación'}.get(self.status, self.status)

    @property
    def status_color(self):
        return {'free': 'green', 'occupied': 'red', 'reserved': 'blue',
                'repair': 'orange'}.get(self.status, 'grey')

    def __repr__(self):
        return f'<Machine {self.code}>'


# ── Machine status log ────────────────────────────────────────────────────────

class MachineStatusLog(db.Model):
    __tablename__ = 'machine_status_log'

    id               = db.Column(db.Integer, primary_key=True)
    machine_id       = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=False, index=True)
    old_status       = db.Column(db.String(10))
    new_status       = db.Column(db.String(10), nullable=False)
    delivery_note_id = db.Column(db.Integer, db.ForeignKey('delivery_notes.id'), index=True)
    changed_at       = db.Column(db.DateTime(timezone=True), default=_now)
    changed_by       = db.Column(db.String(80))   # legacy VARCHAR — no eliminar


# ── Client ────────────────────────────────────────────────────────────────────

class Client(db.Model):
    __tablename__ = 'clients'

    id           = db.Column(db.Integer, primary_key=True)
    client_code  = db.Column(db.String(30), unique=True, nullable=False)
    client_type  = db.Column(db.String(10), nullable=False, default='company')
    company_name = db.Column(db.String(150), nullable=False)
    tax_id       = db.Column(db.String(20))
    address      = db.Column(db.String(250))
    phone        = db.Column(db.String(30))
    email        = db.Column(db.String(120))
    notes        = db.Column(db.Text)
    created_at   = db.Column(db.DateTime(timezone=True), default=_now)

    # ── Auditoría con FK ──
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at    = db.Column(db.DateTime(timezone=True), nullable=True)
    deleted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    deleted_at    = db.Column(db.DateTime(timezone=True), nullable=True)

    created_by_user = db.relationship('User', foreign_keys=[created_by_id])
    updated_by_user = db.relationship('User', foreign_keys=[updated_by_id])
    deleted_by_user = db.relationship('User', foreign_keys=[deleted_by_id])

    contacts       = db.relationship('ClientContact', backref='client', lazy='dynamic',
                                     cascade='all, delete-orphan')
    delivery_notes = db.relationship('DeliveryNote', backref='client', lazy='dynamic')

    @property
    def active_rentals_count(self):
        return self.delivery_notes.filter_by(status='active').count()

    def __repr__(self):
        return f'<Client {self.client_code} {self.company_name}>'


# ── Client contacts ───────────────────────────────────────────────────────────

class ClientContact(db.Model):
    __tablename__ = 'client_contacts'

    id        = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, index=True)
    name      = db.Column(db.String(120), nullable=False)
    role      = db.Column(db.String(80))
    phone     = db.Column(db.String(30))
    email     = db.Column(db.String(120))


# ── Delivery note (albarán) ───────────────────────────────────────────────────

class DeliveryNote(db.Model):
    __tablename__ = 'delivery_notes'

    id             = db.Column(db.Integer, primary_key=True)
    albaran_number = db.Column(db.String(20), unique=True, nullable=False)
    client_id      = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, index=True)

    rental_start   = db.Column(db.Date, nullable=False, index=True)
    rental_end     = db.Column(db.Date)

    pricing_mode   = db.Column(db.String(10), nullable=False, default='open')
    price_rate     = db.Column(db.Float)
    price_unit     = db.Column(db.String(10))
    total_price    = db.Column(db.Float)

    delegacion     = db.Column(db.String(30), nullable=True, index=True)
    location       = db.Column(db.String(250))
    notes          = db.Column(db.Text)
    created_by     = db.Column(db.String(80), nullable=False)  # legacy VARCHAR — no eliminar
    status         = db.Column(db.String(10), nullable=False, default='active', index=True)
    created_at     = db.Column(db.DateTime(timezone=True), default=_now)

    invoice_number       = db.Column(db.String(20), unique=True, nullable=True)
    invoice_generated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # ── Firma digital ──
    signature_token         = db.Column(db.String(64), unique=True, nullable=True)
    signature_token_expires = db.Column(db.DateTime(timezone=True), nullable=True)
    signature_data          = db.Column(db.Text, nullable=True)   # base64 PNG del canvas
    signed_at               = db.Column(db.DateTime(timezone=True), nullable=True)
    signer_name             = db.Column(db.String(120), nullable=True)

    # ── Auditoría con FK ──
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at    = db.Column(db.DateTime(timezone=True), nullable=True)

    created_by_user = db.relationship('User', foreign_keys=[created_by_id])
    updated_by_user = db.relationship('User', foreign_keys=[updated_by_id])

    machines    = db.relationship('DeliveryNoteMachine', backref='delivery_note',
                                  lazy='dynamic', cascade='all, delete-orphan')
    status_logs = db.relationship('MachineStatusLog', backref='delivery_note',
                                  lazy='dynamic')

    @property
    def calculated_total(self):
        if self.pricing_mode == 'closed':
            return self.total_price
        if not (self.price_rate and self.rental_end):
            return None
        days = (self.rental_end - self.rental_start).days or 1
        if self.price_unit == 'day':
            return round(self.price_rate * days, 2)
        elif self.price_unit == 'week':
            return round(self.price_rate * (days / 7), 2)
        elif self.price_unit == 'month':
            return round(self.price_rate * (days / 30), 2)
        return None

    @property
    def display_price(self):
        if self.total_price is not None:
            return f'{self.total_price:,.2f} €'
        if self.price_rate:
            unit_map = {'day': 'día', 'week': 'semana', 'month': 'mes'}
            return f'{self.price_rate:,.2f} € / {unit_map.get(self.price_unit, self.price_unit)}'
        return '—'

    def __repr__(self):
        return f'<DeliveryNote {self.albaran_number}>'


# ── Junction: delivery note ↔ machine ────────────────────────────────────────

class DeliveryNoteMachine(db.Model):
    __tablename__ = 'delivery_note_machines'

    id               = db.Column(db.Integer, primary_key=True)
    delivery_note_id = db.Column(db.Integer, db.ForeignKey('delivery_notes.id'), nullable=False, index=True)
    machine_id       = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=False, index=True)


# ── Repair orders ────────────────────────────────────────────────────────────

class RepairOrder(db.Model):
    __tablename__ = 'repair_orders'

    id               = db.Column(db.Integer, primary_key=True)
    machine_id       = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=False, index=True)
    delegacion       = db.Column(db.String(30), nullable=True)
    description      = db.Column(db.Text, nullable=True)
    estimated_days   = db.Column(db.Integer, nullable=True)
    cost             = db.Column(db.Float, nullable=True)
    status           = db.Column(db.String(10), nullable=False, default='open', index=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    created_at       = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    created_by_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    closed_at        = db.Column(db.DateTime(timezone=True), nullable=True)
    closed_by_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    machine    = db.relationship('Machine',  foreign_keys=[machine_id], backref='repair_orders')
    created_by = db.relationship('User',     foreign_keys=[created_by_id])
    closed_by  = db.relationship('User',     foreign_keys=[closed_by_id])
    comments   = db.relationship('RepairComment', backref='repair_order',
                                 lazy='dynamic', cascade='all, delete-orphan',
                                 order_by='RepairComment.created_at')


class RepairComment(db.Model):
    __tablename__ = 'repair_comments'

    id              = db.Column(db.Integer, primary_key=True)
    repair_order_id = db.Column(db.Integer, db.ForeignKey('repair_orders.id'), nullable=False, index=True)
    text            = db.Column(db.Text, nullable=False)
    created_at      = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    created_by_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_by = db.relationship('User', foreign_keys=[created_by_id])


# ── Helpers ───────────────────────────────────────────────────────────────────

def next_invoice_number():
    year = datetime.now(timezone.utc).year
    prefix = f'FAC-{year}-'
    last = (DeliveryNote.query
            .filter(DeliveryNote.invoice_number.like(f'{prefix}%'))
            .order_by(DeliveryNote.id.desc())
            .first())
    seq = int(last.invoice_number.split('-')[-1]) + 1 if last else 1
    return f'{prefix}{seq:04d}'


def next_albaran_number():
    year = datetime.now(timezone.utc).year
    prefix = f'ALB-{year}-'
    last = (DeliveryNote.query
            .filter(DeliveryNote.albaran_number.like(f'{prefix}%'))
            .order_by(DeliveryNote.id.desc())
            .first())
    seq = int(last.albaran_number.split('-')[-1]) + 1 if last else 1
    return f'{prefix}{seq:04d}'


def next_client_code(abbrev):
    prefix = f'C-{abbrev.upper()}-'
    last = (Client.query
            .filter(Client.client_code.like(f'{prefix}%'))
            .order_by(Client.id.desc())
            .first())
    seq = int(last.client_code.split('-')[-1]) + 1 if last else 1
    return f'{prefix}{seq:03d}'


def suggest_client_abbrev(name: str) -> str:
    import re
    stopwords = {'sl', 'sa', 'slu', 'sll', 'slp', 'sc', 'cb', 'de', 'la', 'el',
                 'los', 'las', 'y', 'e', 'obras', 'construcciones', 'grupo', 'servicios'}
    words = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s]', '', name).split()
    tokens = [w.upper() for w in words if w.lower() not in stopwords and len(w) > 1]
    if not tokens:
        tokens = [name.upper().replace(' ', '')]
    return tokens[0][:6]
