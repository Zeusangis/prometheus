from datetime import datetime, timezone
from models import db

STATUS_FLOW = [
    "uploaded",
    "ats_scored",
    "interview_scheduled",
    "interview_completed",
    "offer_made",
    "hired",
    "rejected",
]


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
    raw_text = db.Column(db.Text, nullable=True)
    # Tracks where the file is in the pipeline
    ats_score = db.Column(db.Float, nullable=True)  # Score from 0.0 to 100.0
    status = db.Column(db.String(50), default="uploaded")

    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name or "",
            "email": self.email or "",
            "github_username": self.github_username,
            "filename": self.original_filename,
            "status": self.status,
            "raw_text": self.raw_text,
            "uploaded_at": self.uploaded_at.isoformat(),
            "job_id": self.job_id,
        }
