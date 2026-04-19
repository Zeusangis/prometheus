from flask import Blueprint, jsonify


github_bp = Blueprint("github", __name__)


@github_bp.route("/api/github/health", methods=["GET"])
def github_health():
    """Lightweight endpoint so app boot does not fail when GitHub routes are absent."""
    return jsonify({"status": "ok", "service": "github"}), 200
