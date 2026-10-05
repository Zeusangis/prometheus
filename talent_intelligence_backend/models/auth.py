from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from models import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(500), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    session_version = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        if len(password) < 12:
            raise ValueError("Password must contain at least 12 characters.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Organization(db.Model):
    __tablename__ = "organizations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class OrganizationMembership(db.Model):
    __tablename__ = "organization_memberships"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False, index=True)
    role = db.Column(db.String(30), nullable=False, default="recruiter")
    user = db.relationship("User")
    organization = db.relationship("Organization")
    __table_args__ = (db.UniqueConstraint("user_id", "organization_id", name="uq_membership_user_org"),)
