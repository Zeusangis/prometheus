from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, request
from utils.api_errors import api_error

from models import Job, db
from services.auth import owned_job, owned_jobs


STATUS_OPTIONS = {"open", "closed", "draft"}
jobs_bp = Blueprint("jobs", __name__)

def _parse_job_id(raw_job_id):
    """Support both numeric IDs (123) and prefixed IDs (job_123)."""
    if isinstance(raw_job_id, int):
        return raw_job_id

    raw = str(raw_job_id or "").strip()
    if raw.startswith("job_"):
        raw = raw[4:]

    if raw.isdigit():
        return int(raw)
    return None


def _isoformat_z(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_created_job_response(job):
    public_path = f"/apply/{job.id}"
    return {
        "id": f"job_{job.id}",
        "publicApplicationPath": public_path,
        "applicationLink": public_path,  # Temporary compatibility; never a backend-host URL.
        "createdAt": _isoformat_z(job.posted_date),
    }


@jobs_bp.route("/api/jobs", methods=["POST"])
@jobs_bp.route("/api/jobs/create", methods=["POST"])
def create_job_route():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict) or not isinstance(data.get("job", {}), dict):
        return api_error("job_payload_invalid", "A job object is required.", 400)
    job_payload = data.get("job") or {}

    title = job_payload.get("title")
    job_type = job_payload.get("jobType")
    description = job_payload.get("description")

    if not title or not job_type or not description:
        return api_error("job_fields_required", "Title, job type, and description are required.", 400)

    status = data.get("status", "open")
    if status not in STATUS_OPTIONS:
        return api_error("job_status_invalid", "Status must be open, closed, or draft.", 400)


    try:
        new_job = Job.from_frontend_payload(
            data,
            company=g.organization.name,
            recruiter_data=None,
        )
        new_job.organization_id = g.organization.id
        new_job.created_by_user_id = g.user.id
        new_job.posted_date = datetime.now(timezone.utc)
        db.session.add(new_job)
        db.session.commit()
        return jsonify(build_created_job_response(new_job)), 201
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Job creation failed")
        return api_error("job_create_failed", "Job could not be created.", 500)


@jobs_bp.route("/api/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    if str(job_id).strip().lower() == "my-company":
        return get_my_company_jobs()

    parsed_job_id = _parse_job_id(job_id)
    if parsed_job_id is None:
        return api_error("job_id_invalid", "Invalid job id.", 400)

    job = owned_job(parsed_job_id)
    if not job:
        return api_error("job_not_found", "Job not found.", 404)

    return jsonify({"success": True, "job": job.to_dict()})


@jobs_bp.get("/api/public/jobs/<int:job_id>")
def get_public_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return api_error("job_not_found", "Job not found.", 404)
    if job.status != "open":
        return api_error("job_closed", "This job is not accepting applications.", 409)
    data = job.to_dict()
    return jsonify({"success": True, "job": {
        "id": job.id, "title": job.title, "company": job.company,
        "location": job.location, "jobType": data["jobType"],
        "description": job.description, "languages": data["languages"],
        "frameworks": data["frameworks"], "status": job.status,
    }})


@jobs_bp.route("/api/jobs/<job_id>/info", methods=["GET"])
def get_job_info(job_id):
    parsed_job_id = _parse_job_id(job_id)
    if parsed_job_id is None:
        return api_error("job_id_invalid", "Invalid job id.", 400)

    job = owned_job(parsed_job_id)
    if not job:
        return api_error("job_not_found", "Job not found.", 404)

    job_data = job.to_dict()
    return (
        jsonify(
            {
                "id": f"job_{job.id}",
                "title": job_data.get("title"),
                "type": job_data.get("jobType") or job_data.get("location") or "Remote",
                "description": job_data.get("description") or "",
            }
        ),
        200,
    )


@jobs_bp.route("/api/jobs/my-company", methods=["GET"])
@jobs_bp.route("/api/jobs/my-company/", methods=["GET"])
def get_my_company_jobs():
    # Temporary alias for existing clients; SQL-scoped, not static JSON filtering.
    return list_jobs()


@jobs_bp.route("/api/jobs/<job_id>", methods=["PATCH", "PUT", "POST"])
@jobs_bp.route("/api/jobs/<job_id>/update", methods=["PATCH", "PUT", "POST"])
def update_job(job_id):
    parsed_job_id = _parse_job_id(job_id)
    if parsed_job_id is None:
        return api_error("job_id_invalid", "Invalid job id.", 400)

    job = owned_job(parsed_job_id)
    if not job:
        return api_error("job_not_found", "Job not found.", 404)

    data = request.get_json(silent=True) or {}
    if "status" in data and data.get("status") not in STATUS_OPTIONS:
        return api_error("job_status_invalid", "Status must be open, closed, or draft.", 400)

    try:
        job.update_from_frontend_payload(data)
        job.company = g.organization.name
        job.recruiter_data = None
        db.session.commit()
        return jsonify({"success": True, "job": job.to_dict()}), 200
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Job update failed")
        return api_error("job_update_failed", "Job could not be updated.", 500)


@jobs_bp.route("/api/jobs/<job_id>/applicants", methods=["GET"])
def get_job_applicants(job_id):
    parsed_job_id = _parse_job_id(job_id)
    if parsed_job_id is None:
        return api_error("job_id_invalid", "Invalid job id.", 400)

    job = owned_job(parsed_job_id)
    if not job:
        return api_error("job_not_found", "Job not found.", 404)

    applicants = [candidate.to_dict() for candidate in job.applicants]
    return jsonify({"success": True, "applicants": applicants})


@jobs_bp.route("/api/jobs/<job_id>/scraper", methods=["POST"])
def update_job_scraper(job_id):
    parsed_job_id = _parse_job_id(job_id)
    if parsed_job_id is None:
        return api_error("job_id_invalid", "Invalid job id.", 400)

    job = owned_job(parsed_job_id)
    if not job:
        return api_error("job_not_found", "Job not found.", 404)

    data = request.get_json(silent=True) or {}
    job.scraper_config = {
        "scraperMetrics": data.get("scraperMetrics") or {},
        "scraperInstructions": data.get("scraperInstructions") or "",
    }

    try:
        db.session.commit()
        return jsonify({"success": True, "job": job.to_dict()}), 200
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Scraper config update failed")
        return api_error("job_update_failed", "Job configuration could not be updated.", 500)


@jobs_bp.route("/api/jobs/<job_id>/interview", methods=["POST"])
def update_job_interview(job_id):
    parsed_job_id = _parse_job_id(job_id)
    if parsed_job_id is None:
        return api_error("job_id_invalid", "Invalid job id.", 400)

    job = owned_job(parsed_job_id)
    if not job:
        return api_error("job_not_found", "Job not found.", 404)

    data = request.get_json(silent=True) or {}
    job.interview_config = {
        "interviewTone": data.get("interviewTone") or "",
        "interviewFocus": list(data.get("interviewFocus") or []),
        "customQuestions": list(data.get("customQuestions") or []),
        "interviewLength": data.get("interviewLength"),
        "interviewInstructions": data.get("interviewInstructions") or "",
    }

    try:
        db.session.commit()
        return jsonify({"success": True, "job": job.to_dict()}), 200
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Interview config update failed")
        return api_error("job_update_failed", "Interview configuration could not be updated.", 500)


@jobs_bp.route("/api/jobs/<job_id>/status", methods=["POST"])
def update_job_status(job_id):
    parsed_job_id = _parse_job_id(job_id)
    if parsed_job_id is None:
        return api_error("job_id_invalid", "Invalid job id.", 400)

    job = owned_job(parsed_job_id)
    if not job:
        return api_error("job_not_found", "Job not found.", 404)

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in STATUS_OPTIONS:
        return api_error("job_status_invalid", "Status must be open, closed, or draft.", 400)

    try:
        job.status = status
        db.session.commit()
        return jsonify({"success": True, "job": job.to_dict()}), 200
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Job status update failed")
        return api_error("job_update_failed", "Job status could not be updated.", 500)


@jobs_bp.route("/api/jobs", methods=["GET"])
@jobs_bp.route("/api/jobs/", methods=["GET"])
def list_jobs():
    jobs = db.session.scalars(owned_jobs().order_by(Job.posted_date.desc())).all()
    summaries = []
    for job in jobs:
        job_data = job.to_dict()
        summaries.append(
            {
                "id": f"job_{job.id}",
                "title": job_data.get("title"),
                "description": job_data.get("description"),
                "jobType": job_data.get("jobType"),
                "languages": job_data.get("languages", []),
                "frameworks": job_data.get("frameworks", []),
                "status": job_data.get("status"),
                "company": job_data.get("company"),
                "location": job_data.get("location"),
                "posted_date": job_data.get("posted_date"),
                "total_applicants": len(job.applicants),
            }
        )

    return jsonify({"success": True, "jobs": summaries})
