from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from models import Job, db


STATUS_OPTIONS = {"open", "closed", "draft"}
jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("/api/jobs/create", methods=["POST"])
def create_job_route():
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    description = data.get("description")
    company = data.get("company")
    location = data.get("location")
    requirements = data.get("requirements")
    status = data.get("status", "open")

    if status not in STATUS_OPTIONS:
        return (
            jsonify({"error": "Invalid status. Must be one of: open, closed, draft"}),
            400,
        )

    if not title or not description or not company:
        return jsonify({"error": "Title, description, and company are required"}), 400

    try:
        new_job = Job(
            title=title,
            description=description,
            company=company,
            location=location,
            requirements=requirements,
            status=status,
            posted_date=datetime.now(timezone.utc),
        )
        db.session.add(new_job)
        db.session.commit()
        return (
            jsonify({"message": "Job created successfully", "job": new_job.to_dict()}),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return (
            jsonify({"error": f"Failed to create job: {exc}"}),
            500,
        )


# route for getting all applicants for a job
@jobs_bp.route("/api/jobs/<int:job_id>/applicants", methods=["GET"])
def get_job_applicants(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    applicants = [candidate.to_dict() for candidate in job.applicants]
    return jsonify({"success": True, "applicants": applicants})
