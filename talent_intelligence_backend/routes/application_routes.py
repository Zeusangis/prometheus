import os
import uuid

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename
from tasks.resume_tasks import process_resume_task


from models import Candidate, db

ALLOWED_EXTENSIONS = {"pdf"}
application_bp = Blueprint("application", __name__)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@application_bp.route("/api/apply/<int:job_id>", methods=["POST"])
def apply_for_job(job_id):

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
