from models import db


class MeetingSummary(db.Model):
    __tablename__ = "meeting_summaries"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=True)
    meeting_id = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    candidate = db.relationship("Candidate", back_populates="meeting_summaries")
    job = db.relationship("Job", back_populates="meeting_summaries")

    def to_dict(self):
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "meeting_id": self.meeting_id,
            "created_at": self.created_at.isoformat(),
        }
