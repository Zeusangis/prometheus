import os
import uuid

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

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
