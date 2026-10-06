import os
import re
import uuid

from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.utils import secure_filename

from models import Candidate, Job, MeetingSummary, db
from services.analysis_queue import enqueue_analysis
from services.audit import events_for_candidate, record_analysis_retry, record_stage_change
from services.auth import owned_candidate, owned_job
from services.candidate_stage import (
    ANALYSIS_STATUSES, InvalidTransition, RETRYABLE_ANALYSIS, STAGES, transition_candidate,
)
from services.candidate_analysis import ensure_records, prepare_retry
from utils.api_errors import api_error

application_bp = Blueprint("application", __name__)
MAX_RESUME_BYTES = 5 * 1024 * 1024
# Pagination replaces a blunt row cap: a request can only ever return page_size rows.
DEFAULT_QUEUE_PAGE_SIZE = 10
MAX_QUEUE_PAGE_SIZE = 100
QUEUE_FILTERS = {
    "attention": tuple(RETRYABLE_ANALYSIS),
    "running": ("queued", "running"),
}


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


def _parse_positive_int(raw, default, maximum=None):
    """Return a positive integer, the default when absent, or None when invalid."""
    text = str(raw or "").strip()
    if not text:
        return default
    if not text.isdigit():
        return None
    value = int(text)
    if value < 1 or (maximum is not None and value > maximum):
        return None
    return value


def _queue_summary():
    """Organization-wide counts, independent of the current page and filters.

    The dashboard's metric cards and pipeline distribution must not change when a
    recruiter narrows or pages the queue, so they are computed from the whole
    organization rather than from the rows in one response.
    """
    def grouped_counts(column):
        rows = db.session.execute(
            db.select(column, db.func.count())
            .select_from(Candidate)
            .join(Job, Candidate.job_id == Job.id)
            .where(Job.organization_id == g.organization.id)
            .group_by(column)
        ).all()
        return {key: total for key, total in rows}

    stage_counts = grouped_counts(Candidate.status)
    return {
        "total_applicants": sum(stage_counts.values()),
        "stage_counts": stage_counts,
        "analysis_counts": grouped_counts(Candidate.analysis_status),
    }


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
        ensure_records(candidate)
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
    candidate = owned_candidate(candidate_id)
    if not candidate:
        return api_error("candidate_not_found", "Candidate not found.", 404)
    if effective_job_id is not None and candidate.job_id != effective_job_id:
        return api_error("candidate_job_mismatch", "Candidate does not belong to this job.", 404)
    from_stage = candidate.status
    try:
        transition_candidate(candidate, next_status)
    except InvalidTransition as error:
        # A refused transition records nothing: the trail holds only real changes.
        return api_error("candidate_transition_invalid", str(error), 409)
    # Compatibility until Interview replaces MeetingSummary in the interview phase.
    if next_status == "interview_scheduled":
        candidate.meeting_id = uuid.uuid4().hex
        db.session.add(MeetingSummary(
            candidate_id=candidate.id, job_id=candidate.job_id, meeting_id=candidate.meeting_id
        ))
    record_stage_change(candidate, from_stage, next_status, g.user)
    db.session.commit()
    return jsonify({
        "success": True,
        "candidateId": candidate.id,
        "jobId": candidate.job_id,
        "status": candidate.status,
        "meeting_id": candidate.meeting_id,
        "allowed_actions": candidate.to_dict()["allowed_actions"],
    })


@application_bp.get("/api/candidates")
def list_candidates():
    """Applicant screening queue, always scoped to the recruiter's organization."""
    conditions = [Job.organization_id == g.organization.id]
    page = _parse_positive_int(request.args.get("page"), 1)
    if page is None:
        return api_error("page_invalid", "Page must be a positive integer.", 400)
    page_size = _parse_positive_int(
        request.args.get("page_size"), DEFAULT_QUEUE_PAGE_SIZE, MAX_QUEUE_PAGE_SIZE
    )
    if page_size is None:
        return api_error(
            "page_size_invalid", f"Page size must be between 1 and {MAX_QUEUE_PAGE_SIZE}.", 400
        )
    stage = request.args.get("stage")
    if stage and stage not in STAGES:
        return api_error("stage_invalid", "Unknown recruiting stage.", 400)
    if stage:
        conditions.append(Candidate.status == stage)
    analysis_status = request.args.get("analysis_status")
    if analysis_status and analysis_status not in ANALYSIS_STATUSES:
        return api_error("analysis_status_invalid", "Unknown analysis status.", 400)
    if analysis_status:
        conditions.append(Candidate.analysis_status == analysis_status)
    # Named groupings keep the client from inventing its own status vocabulary.
    for name, statuses in QUEUE_FILTERS.items():
        if request.args.get(name):
            conditions.append(Candidate.analysis_status.in_(statuses))
    job_id = request.args.get("job_id")
    if job_id:
        parsed_job_id = _parse_job_id(job_id)
        if parsed_job_id is None:
            return api_error("job_id_invalid", "Invalid job id.", 400)
        if not owned_job(parsed_job_id):
            return api_error("job_not_found", "Job not found.", 404)
        conditions.append(Candidate.job_id == parsed_job_id)
    search = (request.args.get("q") or "").strip()
    if search:
        pattern = f"%{search.lower()}%"
        conditions.append(db.or_(
            db.func.lower(Candidate.full_name).like(pattern),
            db.func.lower(Candidate.email).like(pattern),
        ))
    # count(*) over the same join and filters, so the total matches what is listed.
    total = db.session.scalar(
        db.select(db.func.count())
        .select_from(Candidate)
        .join(Job, Candidate.job_id == Job.id)
        .where(*conditions)
    )
    rows = db.session.execute(
        db.select(Candidate, Job.title)
        .join(Job, Candidate.job_id == Job.id)
        .where(*conditions)
        .order_by(Candidate.uploaded_at.desc(), Candidate.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()
    return jsonify({
        "success": True,
        "candidates": [
            {**candidate.to_dict(), "job_title": title} for candidate, title in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "summary": _queue_summary(),
    })


@application_bp.route("/api/candidates/<int:candidate_id>", methods=["GET"])
def get_candidate(candidate_id):
    candidate = owned_candidate(candidate_id)
    if not candidate:
        return api_error("candidate_not_found", "Candidate not found.", 404)
    return jsonify({"success": True, "candidate": candidate.to_dict()}), 200


@application_bp.get("/api/candidates/<int:candidate_id>/stage-events")
def list_stage_events(candidate_id):
    """Read-only, organization-scoped audit trail for one candidate, newest first."""
    candidate = owned_candidate(candidate_id)
    if not candidate:
        return api_error("candidate_not_found", "Candidate not found.", 404)
    return jsonify({
        "success": True,
        "candidateId": candidate.id,
        "events": [event.to_dict() for event in events_for_candidate(candidate.id)],
    })


@application_bp.get("/api/candidates/<int:candidate_id>/analysis")
def get_analysis(candidate_id):
    candidate = owned_candidate(candidate_id)
    if not candidate:
        return api_error("candidate_not_found", "Candidate not found.", 404)
    return jsonify({
        "status": candidate.analysis_status,
        "error_message": candidate.analysis_error,
        # The recruiter owns this application, so the extracted text is visible for review
        # and for diagnosing why an analysis failed.
        "resume_text": candidate.raw_text,
        "resume": candidate.resume_analysis.to_dict() if candidate.resume_analysis else None,
        "github": candidate.github_analysis.to_dict() if candidate.github_analysis else None,
    })


@application_bp.post("/api/candidates/<int:candidate_id>/analysis/retry")
def retry_analysis(candidate_id):
    candidate = owned_candidate(candidate_id)
    if not candidate:
        return api_error("candidate_not_found", "Candidate not found.", 404)
    if candidate.analysis_status not in {"failed", "enqueue_failed", "partial"}:
        return api_error("analysis_retry_invalid", "Analysis is already queued, running, or complete.", 409)
    previous_status = candidate.analysis_status
    prepare_retry(candidate)
    candidate.analysis_status = "queued"
    candidate.analysis_error = None
    record_analysis_retry(candidate, previous_status, g.user)
    db.session.commit()
    task_id = enqueue_analysis(candidate)
    return jsonify({"success": task_id is not None, "analysis_status": candidate.analysis_status}), 202 if task_id else 503
