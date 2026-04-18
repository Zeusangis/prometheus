from datetime import datetime, timezone
from models import db


class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False, unique=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=True)
    job = db.relationship("Job", back_populates="applicants")
    raw_text = db.Column(db.Text, nullable=True)
    # Tracks where the file is in the pipeline
    status = db.Column(db.String(50), default="uploaded")

    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.original_filename,
            "status": self.status,
            "uploaded_at": self.uploaded_at.isoformat(),
            "job_id": self.job_id,
        }
