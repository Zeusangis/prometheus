import secrets

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from models import OrganizationMembership, User, db
from services.auth import authenticated_user, valid_csrf
from utils.api_errors import api_error

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
DUMMY_HASH = generate_password_hash(secrets.token_urlsafe(32))


@auth_bp.get("/csrf")
def csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return jsonify({"csrf_token": session["csrf_token"]})


def identity(user, membership):
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "organization": {"id": membership.organization.id, "name": membership.organization.name},
        "csrf_token": session["csrf_token"],
    }


@auth_bp.post("/login")
def login():
    if not valid_csrf():
        return api_error("csrf_invalid", "Refresh the sign-in page and try again.", 403)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return api_error("login_invalid", "Email and password are required.", 400)
    email, password = payload.get("email"), payload.get("password")
    if not isinstance(email, str) or not isinstance(password, str) or len(password) > 1024:
        return api_error("login_invalid", "Email and password are required.", 400)
    user = db.session.scalar(db.select(User).where(User.email == email.strip().lower()))
    password_valid = check_password_hash(user.password_hash if user else DUMMY_HASH, password)
    if not user or not user.active or not password_valid:
        return api_error("login_failed", "Email or password is incorrect.", 401)
    memberships = db.session.scalars(db.select(OrganizationMembership).where(
        OrganizationMembership.user_id == user.id,
    ).order_by(OrganizationMembership.id)).all()
    organization_id = payload.get("organization_id")
    membership = next((m for m in memberships if m.organization_id == organization_id), None) if organization_id is not None else (memberships[0] if len(memberships) == 1 else None)
    if not membership:
        return api_error("organization_selection_required", "Select an authorized organization ID.", 403)
    session.clear()
    session.permanent = True
    session.update(user_id=user.id, organization_id=membership.organization_id,
                   session_version=user.session_version, csrf_token=secrets.token_urlsafe(32))
    return jsonify(identity(user, membership))


@auth_bp.get("/me")
def me():
    user = authenticated_user()
    if not user:
        return api_error("authentication_required", "Please sign in.", 401)
    membership = db.session.scalar(db.select(OrganizationMembership).where(
        OrganizationMembership.user_id == user.id,
        OrganizationMembership.organization_id == session.get("organization_id"),
    ))
    if not membership:
        return api_error("organization_forbidden", "Organization access is unavailable.", 403)
    return jsonify(identity(user, membership))


@auth_bp.post("/logout")
def logout():
    user = authenticated_user()
    user.session_version += 1
    db.session.commit()
    session.clear()
    return jsonify({"success": True})
