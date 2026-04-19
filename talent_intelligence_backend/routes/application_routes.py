import os
import uuid

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename
from tasks.resume_tasks import process_resume_task


from models import Candidate, Job, db

ALLOWED_EXTENSIONS = {"pdf"}
application_bp = Blueprint("application", __name__)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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


@application_bp.route("/api/apply/<int:job_id>", methods=["GET", "POST"])
def apply_for_job(job_id):

    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if request.method == "GET":
        return (
            jsonify(
                {
                    "message": "Application endpoint is available. Submit a POST multipart/form-data request with full_name, email, github_username, and a 'resume' PDF file.",
                    "jobId": job_id,
                    "jobTitle": job.title,
                    "method": "POST",
                    "contentType": "multipart/form-data",
                    "requiredFields": [
                        "full_name",
                        "email",
                        "github_username",
                        "resume",
                    ],
                }
            ),
            200,
        )

    full_name = (request.form.get("full_name") or "").strip()
    email = (request.form.get("email") or "").strip()
    github_username = (request.form.get("github_username") or "").strip()

    if not full_name or not email or not github_username:
        return (
            jsonify(
                {
                    "error": "full_name, email, and github_username are required in form-data"
                }
            ),
            400,
        )

    if "resume" not in request.files:
        return jsonify({"error": "No file key 'resume' found in request"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    try:
        safe_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}-{safe_filename}"
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(save_path)

        new_candidate = Candidate(
            full_name=full_name,
            email=email,
            github_username=github_username,
            original_filename=file.filename,
            file_path=save_path,
            status="applied",
            job_id=job_id,
        )
        db.session.add(new_candidate)
        db.session.commit()

        process_resume_task.delay(new_candidate.id)
        # ==========================================
        return (
            jsonify(
                {
                    "message": "Application successful.",
                    "data": new_candidate.to_dict(),
                }
            ),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to process application: {exc}"}), 500


# routes/application_routes.py
# (Keep your existing imports and upload route)


@application_bp.route("/api/candidates/<int:candidate_id>", methods=["GET"])
def get_candidate(candidate_id):
    candidate = Candidate.query.get(candidate_id)

    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404

    # Build the response payload
    response_data = candidate.to_dict()

    # Add the raw text to the response so we can inspect it
    response_data["raw_text"] = candidate.raw_text

    return (
        jsonify({"message": "Candidate retrieved successfully", "data": response_data}),
        200,
    )


@application_bp.route("/api/jobs/<job_id>/candidates", methods=["GET"])
@application_bp.route("/api/jobs/<job_id>/candidates/", methods=["GET"])
def get_all_candidates(job_id):
    parsed_job_id = _parse_job_id(job_id)
    if parsed_job_id is None:
        return jsonify({"error": "Invalid job id"}), 400

    job = Job.query.get(parsed_job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    candidates = Candidate.query.filter_by(job_id=parsed_job_id).all()
    candidates_data = [candidate.to_dict() for candidate in candidates]
    return (
        jsonify(
            {
                "success": True,
                "jobId": parsed_job_id,
                "count": len(candidates_data),
                "applicants": candidates_data,
            }
        ),
        200,
    )
