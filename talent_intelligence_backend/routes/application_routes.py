import os
import uuid

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from models import Candidate, db

application_bp = Blueprint("resume", __name__)
create_job = Blueprint("jobs", __name__)

ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@application_bp.route("/api/apply/<int:job_id>", methods=["POST"])
def apply_for_job(job_id):
    """
    Apply for a job by uploading a resume
    This endpoint accepts a PDF file and associates it with the specified job.
    ---
    tags:
      - Resumes
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        description: The ID of the job to apply for.
      - name: resume
        in: formData
        type: file
        required: true
        description: The PDF resume file to upload.
    responses:
      200:
        description: Application successful.
      400:
        description: Invalid request (missing file, wrong format, or invalid job ID).
    """
    # For simplicity, we're not actually checking if the job_id exists here.
    # In a real application, you'd want to validate that the job exists before accepting applications.

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
            original_filename=file.filename,
            file_path=save_path,
            status="applied",
            job_id=job_id,
        )
        db.session.add(new_candidate)
        db.session.commit()

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
