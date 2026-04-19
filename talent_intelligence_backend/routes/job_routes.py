from datetime import datetime, timezone
import json
from pathlib import Path

from flask import Blueprint, jsonify, request

from models import Job, db


STATUS_OPTIONS = {"open", "closed", "draft"}
jobs_bp = Blueprint("jobs", __name__)

_RECRUITER_FILE = Path(__file__).resolve().parent.parent / "static" / "recruiter.json"


def extract_company_data(recruiter_data):
    recruiter_data = recruiter_data or {}
    company_data = recruiter_data.get("company_data")

    if isinstance(company_data, dict):
        return company_data

    company = recruiter_data.get("company")
    if isinstance(company, dict):
        return company

    if isinstance(company, str) and company:
        return {"name": company}

    company_name = recruiter_data.get("company_name")
    if isinstance(company_name, str) and company_name:
        return {"name": company_name}

    return None


def load_default_recruiter_data():
    try:
        raw = _RECRUITER_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception:
        return {}

    recruiters = data.get("recruiters") or []
    if not recruiters:
        return {}
    return recruiters[0] if isinstance(recruiters[0], dict) else {}


def resolve_recruiter_data(data):
    recruiter_data = data.get("recruiter") or data.get("recruiter_data") or {}
    if recruiter_data:
        return recruiter_data
    return load_default_recruiter_data()


def _norm(value):
    if value is None:
        return ""
    return str(value).strip().lower()


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
    application_link = f"{request.host_url.rstrip('/')}/api/apply/{job.id}"
    return {
        "id": f"job_{job.id}",
        "applicationLink": application_link,
        "createdAt": _isoformat_z(job.posted_date),
    }


@jobs_bp.route("/api/jobs", methods=["POST"])
@jobs_bp.route("/api/jobs/create", methods=["POST"])
def create_job_route():
    data = request.get_json(silent=True) or {}
    job_payload = data.get("job") or {}

    title = job_payload.get("title")
    job_type = job_payload.get("jobType")
    description = job_payload.get("description")

    if not title or not job_type or not description:
        return jsonify({"error": "Title, job type, and description are required"}), 400

    status = data.get("status", "open")
    if status not in STATUS_OPTIONS:
        return (
            jsonify({"error": "Invalid status. Must be one of: open, closed, draft"}),
            400,
        )

    recruiter_data = resolve_recruiter_data(data)
    company_data = extract_company_data(recruiter_data)
    company = job_payload.get("company") or data.get("company")
    if not company and company_data:
        company = company_data.get("name")
    if not company:
        company = "Unknown Company"

    try:
        new_job = Job.from_frontend_payload(
            data,
            company=company,
            recruiter_data=recruiter_data or None,
        )
        new_job.posted_date = datetime.now(timezone.utc)
        db.session.add(new_job)
        db.session.commit()
        return jsonify(build_created_job_response(new_job)), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to create job: {exc}"}), 500


@jobs_bp.route("/api/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    if str(job_id).strip().lower() == "my-company":
        return get_my_company_jobs()

    parsed_job_id = _parse_job_id(job_id)
    if parsed_job_id is None:
        return jsonify({"error": "Invalid job id"}), 400

    job = Job.query.get(parsed_job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({"success": True, "job": job.to_dict()})


@jobs_bp.route("/api/jobs/my-company", methods=["GET"])
@jobs_bp.route("/api/jobs/my-company/", methods=["GET"])
def get_my_company_jobs():
    recruiter_data = load_default_recruiter_data() or {}
    target_id = recruiter_data.get("id")
    target_email = _norm(recruiter_data.get("email"))
    target_name = _norm(recruiter_data.get("name"))
    target_phone = _norm(recruiter_data.get("phone"))
    target_company = _norm(recruiter_data.get("company"))

    matched_jobs = []
    for job in Job.query.all():
        recruiter = job.recruiter_data or {}

        id_match = target_id is not None and recruiter.get("id") == target_id
        email_match = (
            bool(target_email) and _norm(recruiter.get("email")) == target_email
        )
        name_match = bool(target_name) and _norm(recruiter.get("name")) == target_name
        phone_match = (
            bool(target_phone) and _norm(recruiter.get("phone")) == target_phone
        )
        company_match = (
            bool(target_company) and _norm(recruiter.get("company")) == target_company
        )

        # Require recruiter identity match (id/email/name/phone), with company fallback.
        if id_match or email_match or name_match or phone_match or company_match:
            job_data = job.to_dict()
            matched_jobs.append(
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
                }
            )

    return jsonify(
        {
            "jobs": matched_jobs,
        }
    )


@jobs_bp.route("/api/jobs/<job_id>/applicants", methods=["GET"])
def get_job_applicants(job_id):
    parsed_job_id = _parse_job_id(job_id)
    if parsed_job_id is None:
        return jsonify({"error": "Invalid job id"}), 400

    job = Job.query.get(parsed_job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    applicants = [candidate.to_dict() for candidate in job.applicants]
    return jsonify({"success": True, "applicants": applicants})


@jobs_bp.route("/api/jobs/<job_id>/scraper", methods=["POST"])
def update_job_scraper(job_id):
    parsed_job_id = _parse_job_id(job_id)
    if parsed_job_id is None:
        return jsonify({"error": "Invalid job id"}), 400

    job = Job.query.get(parsed_job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    data = request.get_json(silent=True) or {}
    job.scraper_config = {
        "scraperMetrics": data.get("scraperMetrics") or {},
        "scraperInstructions": data.get("scraperInstructions") or "",
    }

    try:
        db.session.commit()
        return jsonify({"success": True, "job": job.to_dict()}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to update scraper config: {exc}"}), 500


@jobs_bp.route("/api/jobs/<job_id>/interview", methods=["POST"])
def update_job_interview(job_id):
    parsed_job_id = _parse_job_id(job_id)
    if parsed_job_id is None:
        return jsonify({"error": "Invalid job id"}), 400

    job = Job.query.get(parsed_job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

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
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to update interview config: {exc}"}), 500


@jobs_bp.route("/api/jobs/<job_id>/status", methods=["POST"])
def update_job_status(job_id):
    parsed_job_id = _parse_job_id(job_id)
    if parsed_job_id is None:
        return jsonify({"error": "Invalid job id"}), 400

    job = Job.query.get(parsed_job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in STATUS_OPTIONS:
        return (
            jsonify({"error": "Invalid status. Must be one of: open, closed, draft"}),
            400,
        )

    try:
        job.status = status
        db.session.commit()
        return jsonify({"success": True, "job": job.to_dict()}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to update status: {exc}"}), 500


@jobs_bp.route("/api/jobs", methods=["GET"])
@jobs_bp.route("/api/jobs/", methods=["GET"])
def list_jobs():
    jobs = Job.query.all()
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
            }
        )

    return jsonify({"success": True, "jobs": summaries})
