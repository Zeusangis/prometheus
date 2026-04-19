from models import db


class Summary(db.Model):
    __tablename__ = "summaries"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    github_summary = db.Column(db.JSON, nullable=True)
    ats_summary = db.Column(db.JSON, nullable=True)  # New column for ATS summary
    created_at = db.Column(db.DateTime, default=db.func.now())
    candidate = db.relationship("Candidate", back_populates="meeting_summaries")

    def to_dict(self):
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "github_summary": self.github_summary,
            "ats_summary": self.ats_summary,
            "created_at": self.created_at.isoformat(),
        }
