import hmac
from datetime import timedelta

from flask import g, request, session

from models import Candidate, Job, OrganizationMembership, User, db
from utils.api_errors import api_error


def register_auth_guard(app):
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

    @app.before_request
    def recruiter_guard():
        if request.method == "OPTIONS" or not request.path.startswith("/api/"):
            return None
        if request.path.startswith("/api/public/") or request.path in {
            "/api/health", "/api/github/health", "/api/auth/login", "/api/auth/me", "/api/auth/csrf"
        }:
            return None
        # Preserve only the public submission alias; all other legacy endpoints are protected.
        if request.endpoint == "application.apply_for_job":
            return None
        user = authenticated_user()
        if not user:
            return api_error("authentication_required", "Please sign in.", 401)
        membership = db.session.scalar(db.select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == session.get("organization_id"),
        ))
        if not membership:
            return api_error("organization_forbidden", "Organization access is unavailable.", 403)
        g.user = user
        g.organization = membership.organization
        if request.method not in {"GET", "HEAD"} and not valid_csrf():
            return api_error("csrf_invalid", "Security token is invalid. Refresh and try again.", 403)
        return None


def authenticated_user():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if isinstance(user_id, int) else None
    if not user or not user.active or session.get("session_version") != user.session_version:
        return None
    return user


def valid_csrf():
    expected = session.get("csrf_token")
    actual = request.headers.get("X-CSRF-Token")
    return bool(expected and actual and hmac.compare_digest(expected, actual))


def owned_jobs():
    return db.select(Job).where(Job.organization_id == g.organization.id)


def owned_job(job_id):
    return db.session.scalar(owned_jobs().where(Job.id == job_id))


def owned_candidate(candidate_id):
    return db.session.scalar(db.select(Candidate).join(Job).where(
        Candidate.id == candidate_id, Job.organization_id == g.organization.id,
    ))
