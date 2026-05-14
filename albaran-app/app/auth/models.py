"""
Modelos de autenticación, permisos y auditoría.
Separados de models.py para mantener cohesión; ambos archivos son detectados
por Flask-Migrate a través de la importación en app/__init__.py.
"""
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import _now


# ── User ──────────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name     = db.Column(db.String(150), nullable=False)
    # role: 'jefe' tiene acceso total; 'worker' solo lo que se le conceda
    role          = db.Column(db.String(10), nullable=False, default='worker')
    delegacion    = db.Column(db.String(30), nullable=True)   # delegación del trabajador
    is_active     = db.Column(db.Boolean, nullable=False, default=True)
    # Forzar cambio de contraseña si es True (ej. usuario recién creado por el jefe)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
    created_at    = db.Column(db.DateTime(timezone=True), default=_now)

    permissions   = db.relationship('UserPermission', foreign_keys='UserPermission.user_id',
                                    backref='user', lazy='dynamic',
                                    cascade='all, delete-orphan')
    audit_entries = db.relationship('AuditLog', backref='user', lazy='dynamic')

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_jefe(self) -> bool:
        return self.role == 'jefe'

    def _active_permissions_cache(self):
        """Carga (una sola vez por instancia) un dict {permission: UserPermission}
        con todos los permisos activos. Evita ejecutar una query por cada
        has_permission() durante el render de una página."""
        cache = getattr(self, '_perm_cache', None)
        if cache is None:
            cache = {p.permission: p for p in
                     self.permissions.filter_by(revoked_at=None).all()}
            self._perm_cache = cache
        return cache

    def has_permission(self, perm_name: str) -> bool:
        """Devuelve True si el permiso está activo (no revocado)."""
        if self.is_jefe:
            return True
        return perm_name in self._active_permissions_cache()

    def get_active_permission(self, perm_name: str):
        """Devuelve el objeto UserPermission activo o None."""
        return self._active_permissions_cache().get(perm_name)

    def invalidate_permission_cache(self):
        """Llamar tras grant/revoke para refrescar."""
        if hasattr(self, '_perm_cache'):
            del self._perm_cache

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


# ── UserPermission ────────────────────────────────────────────────────────────

# Permisos granulares que el jefe puede conceder a workers:
#   ver_historial_global   → ve el audit_log de TODOS
#   ver_historial_parcial  → ve solo los de ciertos users (ver UserPermissionTarget)
#   conceder_permisos      → puede acceder a /admin/usuarios y gestionar permisos

class UserPermission(db.Model):
    __tablename__ = 'user_permissions'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    permission = db.Column(db.String(40), nullable=False)
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    granted_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)  # None = activo

    grantor = db.relationship('User', foreign_keys=[granted_by])
    targets = db.relationship('UserPermissionTarget', backref='permission_record',
                              lazy='dynamic', cascade='all, delete-orphan')

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None

    def revoke(self) -> None:
        self.revoked_at = datetime.now(timezone.utc)

    def __repr__(self):
        status = 'activo' if self.is_active else 'revocado'
        return f'<UserPermission {self.permission} → user#{self.user_id} [{status}]>'


# ── UserPermissionTarget ──────────────────────────────────────────────────────

class UserPermissionTarget(db.Model):
    """
    Para permisos con scope específico:
    - ver_historial_parcial: target_user_id apunta al usuario cuyo historial puede verse
    - ver_albaranes_delegacion: target_delegacion apunta a la delegación accesible
    """
    __tablename__ = 'user_permission_targets'

    id                 = db.Column(db.Integer, primary_key=True)
    permission_id      = db.Column(db.Integer, db.ForeignKey('user_permissions.id'), nullable=False, index=True)
    target_user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    target_delegacion  = db.Column(db.String(30), nullable=True)

    target_user = db.relationship('User', foreign_keys=[target_user_id])


# ── AuditLog ──────────────────────────────────────────────────────────────────

# Valores válidos de action y entity se validan en la capa de aplicación,
# no con constraints de BD para mantener compatibilidad con SQLite.

class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action       = db.Column(db.String(30), nullable=False, index=True)
    # action ∈ {created, updated, deleted, login, logout,
    #            permission_granted, permission_revoked}
    entity       = db.Column(db.String(30), nullable=False, index=True)
    # entity ∈ {delivery_note, machine, client, user, permission}
    entity_id    = db.Column(db.Integer, nullable=True)
    entity_label = db.Column(db.String(200), nullable=True)  # texto legible
    diff         = db.Column(db.Text, nullable=True)          # JSON serializado
    ip_address   = db.Column(db.String(45), nullable=True)    # IPv4 o IPv6
    timestamp    = db.Column(db.DateTime(timezone=True), default=_now, nullable=False, index=True)

    def __repr__(self):
        return f'<AuditLog {self.action} {self.entity}#{self.entity_id} by user#{self.user_id}>'
