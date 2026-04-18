from flask import Blueprint, jsonify

from services.github_intelligence import (
    build_compact_github_profile,
    fetch_github_profile,
)

github_bp = Blueprint("github", __name__)


@github_bp.route("/")
def index():
    return jsonify(
        {
            "success": True,
            "message": "AI Talent Intelligence API",
            "endpoints": [
                "/api/github/<username> [GET]",
                "/api/github/compact/<username> [GET]",
                "/github/<username> [GET]",
            ],
        }
    )


@github_bp.route("/api/github/<username>", methods=["GET"])
def github_profile(username):
    data, err = fetch_github_profile(username)
    if err:
        return jsonify({"success": False, "error": err}), 404
    return jsonify({"success": True, **data})


@github_bp.route("/api/github/compact/<username>", methods=["GET"])
def github_profile_compact(username):
    data, err = fetch_github_profile(username)
    if err:
        return jsonify({"success": False, "error": err}), 404
    compact_profile = build_compact_github_profile(data)
    return jsonify({"success": True, **compact_profile})


@github_bp.route("/github/<username>", methods=["GET"])
@github_bp.route("/github/<username>/", methods=["GET"])
def github_profile_legacy(username):
    data, err = fetch_github_profile(username)
    if err:
        return jsonify({"success": False, "error": err}), 404
    return jsonify({"success": True, **data})
