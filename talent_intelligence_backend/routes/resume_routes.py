import os
import uuid
import limiter

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from models import Candidate, db

resume_bp = Blueprint("resume", __name__)
create_job = Blueprint("jobs", __name__)

ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@resume_bp.route("/api/resume/upload", methods=["POST"])
@limiter.limit("5 per minute")  # Limit to 5 uploads per minute per IP
def upload_resume():
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
            status="uploaded",
        )
        db.session.add(new_candidate)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Resume securely stored.",
                    "data": new_candidate.to_dict(),
                }
            ),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to process upload: {exc}"}), 500
