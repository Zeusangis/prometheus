import os
import re
import uuid

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from models import Candidate, Job, MeetingSummary, db
from services.analysis_queue import enqueue_analysis
from services.candidate_stage import InvalidTransition, transition_candidate
from utils.api_errors import api_error

application_bp = Blueprint("application", __name__)
MAX_RESUME_BYTES = 5 * 1024 * 1024


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"


def _get_form_value(*keys):
    for key in keys:
        value = request.form.get(key)
        if value and value.strip():
            return value.strip()
    return ""


def _normalize_github_username(value):
    raw = str(value or "").strip()
    for prefix in ("https://github.com/", "http://github.com/", "github.com/"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
            break
    return raw.strip("/")


def _parse_job_id(raw_job_id):
    raw = str(raw_job_id or "").strip().removeprefix("job_")
    return int(raw) if raw.isdigit() else None


@application_bp.route("/api/public/jobs/<int:job_id>/apply", methods=["POST"])
@application_bp.route("/api/jobs/<int:job_id>/apply", methods=["POST"])
def apply_for_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return api_error("job_not_found", "Job not found.", 404)
    if job.status != "open":
        return api_error("job_closed", "This job is not accepting applications.", 409)
    file = request.files.get("resume")
    if not file or not file.filename:
        return api_error("resume_required", "Resume required.", 400)
    if not allowed_file(file.filename) or file.mimetype not in {
        "application/pdf", "application/octet-stream", ""
    }:
        return api_error("resume_invalid", "Only PDF resumes are accepted.", 400)
    content = file.stream.read(MAX_RESUME_BYTES + 1)
    if len(content) > MAX_RESUME_BYTES:
        return api_error("resume_too_large", "Maximum resume size is 5 MB.", 413)
    if not content.startswith(b"%PDF-"):
        return api_error("resume_invalid", "File does not have a valid PDF signature.", 400)
    full_name = _get_form_value("full_name", "fullName", "name")
    email = _get_form_value("email")
    github_username = _normalize_github_username(
        _get_form_value("github_username", "githubUsername", "github")
    )
    if not full_name or len(full_name) > 255 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 255:
        return api_error("applicant_invalid", "Full name and a valid email are required.", 400)
    if github_username and not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", github_username):
        return api_error("github_username_invalid", "Enter a valid GitHub username.", 400)

    safe_filename = secure_filename(file.filename) or "resume.pdf"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{uuid.uuid4()}-{safe_filename}")
    try:
        with open(save_path, "xb") as destination:
            destination.write(content)
        candidate = Candidate(
            full_name=full_name,
            email=email,
            github_username=github_username or None,
            original_filename=safe_filename,
            file_path=save_path,
            status="screening",
            analysis_status="queued",
            job_id=job_id,
        )
        db.session.add(candidate)
        db.session.commit()
    except Exception:
        db.session.rollback()
        if os.path.exists(save_path):
            os.remove(save_path)
        raise

    # Separate from persistence: a broker failure must not report a lost application.
    candidate_id = candidate.id
    try:
        task_id = enqueue_analysis(candidate)
    except Exception:
        # If even recording the broker outage fails, the already-committed application
        # is still valid. Log for operator recovery; never undo it or claim analysis ran.
        db.session.rollback()
        current_app.logger.exception("Could not persist enqueue state candidate_id=%s", candidate_id)
        task_id = None
    return jsonify({
        "success": True,
        "message": "Application received",
        "candidateId": candidate_id,
        "jobId": job_id,
        "taskId": task_id,
        "status": candidate.status,
        "analysis_status": candidate.analysis_status,
    }), 200


@application_bp.route("/api/candidates/<int:candidate_id>/stage", methods=["POST"])
@application_bp.route("/api/jobs/<int:job_id>/candidates/<int:candidate_id>/next-step", methods=["POST"])
@application_bp.route("/api/candidates/<int:candidate_id>/next-step", methods=["POST"])
def move_to_next_step(candidate_id, job_id=None):
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return api_error("request_invalid", "A JSON object is required.", 400)
    effective_job_id = job_id or _parse_job_id(payload.get("job_id") or payload.get("jobId"))
    next_status = payload.get("stage") or payload.get("next_status") or payload.get("status")
    if not isinstance(next_status, str):
        return api_error("stage_required", "A target stage is required.", 400)
    candidate = db.session.get(Candidate, candidate_id)
    if not candidate:
        return api_error("candidate_not_found", "Candidate not found.", 404)
    if effective_job_id is not None and candidate.job_id != effective_job_id:
        return api_error("candidate_job_mismatch", "Candidate does not belong to this job.", 404)
    try:
        transition_candidate(candidate, next_status)
    except InvalidTransition as error:
        return api_error("candidate_transition_invalid", str(error), 409)
    # Compatibility until Interview replaces MeetingSummary in the interview phase.
    if next_status == "interview_scheduled":
        candidate.meeting_id = uuid.uuid4().hex
        db.session.add(MeetingSummary(
            candidate_id=candidate.id, job_id=candidate.job_id, meeting_id=candidate.meeting_id
        ))
    db.session.commit()
    return jsonify({
        "success": True,
        "candidateId": candidate.id,
        "jobId": candidate.job_id,
        "status": candidate.status,
        "meeting_id": candidate.meeting_id,
        "allowed_actions": candidate.to_dict()["allowed_actions"],
    })


@application_bp.route("/api/candidates/<int:candidate_id>", methods=["GET"])
def get_candidate(candidate_id):
    candidate = db.session.get(Candidate, candidate_id)
    if not candidate:
        return api_error("candidate_not_found", "Candidate not found.", 404)
    return jsonify({"success": True, "candidate": candidate.to_dict()}), 200


@application_bp.post("/api/candidates/<int:candidate_id>/analysis/retry")
def retry_analysis(candidate_id):
    candidate = db.session.get(Candidate, candidate_id)
    if not candidate:
        return api_error("candidate_not_found", "Candidate not found.", 404)
    if candidate.analysis_status not in {"failed", "enqueue_failed", "partial"}:
        return api_error("analysis_retry_invalid", "Analysis is already queued, running, or complete.", 409)
    candidate.analysis_status = "queued"
    candidate.analysis_error = None
    db.session.commit()
    task_id = enqueue_analysis(candidate)
    return jsonify({"success": task_id is not None, "analysis_status": candidate.analysis_status}), 202 if task_id else 503
