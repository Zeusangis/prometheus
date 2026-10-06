from datetime import datetime, timezone
from models import db

from services.candidate_stage import allowed_actions


class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    github_username = db.Column(db.String(255), nullable=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False, unique=True)
    meeting_id = db.Column(db.String(255), nullable=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=True)
    job = db.relationship("Job", back_populates="applicants")
    meeting_summaries = db.relationship(
        "MeetingSummary", back_populates="candidate", lazy=True
    )
    resume_analysis = db.relationship("ResumeAnalysis", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    github_analysis = db.relationship("GitHubAnalysis", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    raw_text = db.Column(db.Text, nullable=True)
    ats_score = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="screening")
    analysis_status = db.Column(db.String(50), nullable=False, default="queued")
    analysis_error = db.Column(db.Text, nullable=True)

    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name or "",
            "email": self.email or "",
            "github_username": self.github_username,
            "filename": self.original_filename,
            "status": self.status,
            "analysis_status": self.analysis_status,
            "analysis_error": self.analysis_error,
            "ats_score": self.ats_score,
            "allowed_actions": allowed_actions(self.status),
            "uploaded_at": self.uploaded_at.isoformat(),
            "job_id": self.job_id,
        }
