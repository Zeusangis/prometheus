from urllib.parse import urlparse

from flask import Blueprint, jsonify, request


check_portfolio_bp = Blueprint("check_portfolio", __name__)


def _get_payload_value(payload, *keys):
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _normalize_github_url(value):
    raw = str(value or "").strip()
    if not raw:
        return ""

    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"

    parsed = urlparse(raw)
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return ""

    if not parsed.path or parsed.path == "/":
        return ""

    return f"https://github.com{parsed.path.rstrip('/')}"


@check_portfolio_bp.route("/api/check-portfolio", methods=["POST"])
def check_portfolio_links():
    """Accept GitHub links from frontend without persisting to database."""
    payload = request.get_json(silent=True) or {}
    data = (
        payload.get("portfolio")
        if isinstance(payload.get("portfolio"), dict)
        else payload
    )

    resume_github = _normalize_github_url(
        _get_payload_value(data, "resumeGithub", "resume_github", "github")
    )
    fav_repo_1 = _normalize_github_url(
        _get_payload_value(
            data,
            "favoriteRepo1",
            "favorite_repo_1",
            "favRepo1",
            "repo1",
        )
    )
    fav_repo_2 = _normalize_github_url(
        _get_payload_value(
            data,
            "favoriteRepo2",
            "favorite_repo_2",
            "favRepo2",
            "repo2",
        )
    )

    if not resume_github or not fav_repo_1 or not fav_repo_2:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Please provide valid GitHub links for resumeGithub, favoriteRepo1 and favoriteRepo2.",
                }
            ),
            400,
        )

    return (
        jsonify(
            {
                "success": True,
                "message": "GitHub links received from frontend.",
                "data": {
                    "resumeGithub": resume_github,
                    "favoriteRepo1": fav_repo_1,
                    "favoriteRepo2": fav_repo_2,
                },
            }
        ),
        200,
    )
