import os
import uuid

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from models import Candidate, Job, MeetingSummary, db
from models.candidate import STATUS_FLOW
from tasks.resume_tasks import process_resume_task

application_bp = Blueprint("application", __name__)

ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_form_value(*keys):
    for key in keys:
        value = request.form.get(key)
        if value and str(value).strip():
            return str(value).strip()
    return ""


def _normalize_github_username(value):
    raw = str(value or "").strip()
    raw = raw.replace("https://github.com/", "")
    raw = raw.replace("http://github.com/", "")
    raw = raw.replace("github.com/", "")
    return raw.strip("/") if raw else ""


def _parse_job_id(raw_job_id):
    if isinstance(raw_job_id, int):
        return raw_job_id
    raw = str(raw_job_id or "").strip()
    if raw.startswith("job_"):
        raw = raw[4:]
    return int(raw) if raw.isdigit() else None


def _resolve_job_id(job_id):
    form_job_id = _parse_job_id(_get_form_value("jobId", "job_id"))
    return job_id or form_job_id


@application_bp.route("/api/jobs/<int:job_id>/apply", methods=["POST"])
def apply_for_job(job_id):
    job_id = _resolve_job_id(job_id)

    # ✅ 1. validate job exists (IMPORTANT)
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    # GET not needed anymore but safe if you want
    if request.method == "GET":
        return jsonify({"message": "Use POST"}), 200

    # ✅ file check
    file = request.files.get("resume")
    if not file:
        return jsonify({"error": "Resume required"}), 400

    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Only PDF allowed"}), 400

    # form data
    full_name = _get_form_value("full_name", "fullName", "name")
    email = _get_form_value("email")
    github_username = _normalize_github_username(
        _get_form_value("github_username", "githubUsername", "github")
    )

    if not full_name or not email:
        return jsonify({"error": "Full name and email required"}), 400

    try:
        # save file
        safe_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}-{safe_filename}"
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(save_path)

        # create candidate
        candidate = Candidate(
            full_name=full_name,
            email=email,
            github_username=github_username or None,
            original_filename=file.filename,
            file_path=save_path,
            status="queued",  # 👈 IMPORTANT START STATE
            job_id=job_id,
        )

        db.session.add(candidate)
        db.session.commit()

        # ✅ enqueue celery safely
        task = process_resume_task.delay(candidate.id)

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Application received",
                    "candidateId": candidate.id,
                    "jobId": job_id,
                    "taskId": task.id,
                    "status": candidate.status,
                }
            ),
            200,
        )

    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


@application_bp.route(
    "/api/jobs/<int:job_id>/candidates/<int:candidate_id>/next-step", methods=["POST"]
)
@application_bp.route("/api/candidates/<int:candidate_id>/next-step", methods=["POST"])
def move_to_next_step(candidate_id, job_id=None):
    payload = request.get_json(silent=True) or {}
    next_status = payload.get("next_status") or payload.get("status")
    if not next_status:
        return jsonify({"error": "next_status is required"}), 400
    if next_status not in STATUS_FLOW:
        return (
            jsonify(
                {
                    "error": f"Invalid next_status. Must be one of: {', '.join(STATUS_FLOW)}"
                }
            ),
            400,
        )

    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404

    if job_id is not None and candidate.job_id != job_id:
        return (
            jsonify({"error": "Candidate does not belong to the provided job"}),
            400,
        )

    create_meeting_id = uuid.uuid4().hex
    if next_status == "interview_scheduled":
        candidate.meeting_id = create_meeting_id
        db.session.add(
            MeetingSummary(candidate_id=candidate.id, meeting_id=create_meeting_id)
        )
    candidate.status = next_status

    try:
        db.session.commit()
        return (
            jsonify(
                {
                    "success": True,
                    "candidateId": candidate.id,
                    "jobId": candidate.job_id,
                    "status": candidate.status,
                    "meeting_id": candidate.meeting_id,
                }
            ),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500
