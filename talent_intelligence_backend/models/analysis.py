from datetime import datetime, timezone

from models import db


def now():
    return datetime.now(timezone.utc)


class ResumeAnalysis(db.Model):
    __tablename__ = "resume_analyses"
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    ats_score = db.Column(db.Float)
    breakdown = db.Column(db.JSON)
    missing_keywords = db.Column(db.JSON)
    weak_areas = db.Column(db.JSON)
    top_improvements = db.Column(db.JSON)
    projects = db.Column(db.JSON)
    final_verdict = db.Column(db.Text)
    model_name = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    updated_at = db.Column(db.DateTime, nullable=False, default=now, onupdate=now)
    candidate = db.relationship("Candidate", back_populates="resume_analysis")

    def to_dict(self):
        fields = ("status", "ats_score", "breakdown", "missing_keywords", "weak_areas", "top_improvements", "projects", "final_verdict", "model_name", "error_message")
        return {**{key: getattr(self, key) for key in fields}, "updated_at": self.updated_at.isoformat()}


class GitHubAnalysis(db.Model):
    __tablename__ = "github_analyses"
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    username = db.Column(db.String(255))
    total_public_repos = db.Column(db.Integer)
    total_stars = db.Column(db.Integer)
    candidate_attributed_commits = db.Column(db.Integer)
    summary = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    updated_at = db.Column(db.DateTime, nullable=False, default=now, onupdate=now)
    candidate = db.relationship("Candidate", back_populates="github_analysis")
    repositories = db.relationship("RepositoryAnalysis", back_populates="github_analysis", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "status": self.status, "username": self.username,
            "total_public_repos": self.total_public_repos, "total_stars": self.total_stars,
            "candidate_attributed_commits": self.candidate_attributed_commits,
            "summary": self.summary, "error_message": self.error_message,
            "repositories": [repo.to_dict() for repo in self.repositories],
            "updated_at": self.updated_at.isoformat(),
        }


class RepositoryAnalysis(db.Model):
    __tablename__ = "repository_analyses"
    id = db.Column(db.Integer, primary_key=True)
    github_analysis_id = db.Column(db.Integer, db.ForeignKey("github_analyses.id"), nullable=False)
    repo_name = db.Column(db.String(255), nullable=False)
    repo_url = db.Column(db.String(500), nullable=False)
    primary_language = db.Column(db.String(100))
    pushed_at = db.Column(db.DateTime)
    score = db.Column(db.Float)
    metrics = db.Column(db.JSON)
    strengths = db.Column(db.JSON)
    red_flags = db.Column(db.JSON)
    recruiter_summary = db.Column(db.Text)
    evidence_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    github_analysis = db.relationship("GitHubAnalysis", back_populates="repositories")
    __table_args__ = (db.UniqueConstraint("github_analysis_id", "repo_name", name="uq_analysis_repository"),)

    def to_dict(self):
        return {key: getattr(self, key) for key in (
            "repo_name", "repo_url", "primary_language", "score", "metrics", "strengths", "red_flags", "recruiter_summary", "evidence_metadata"
        )}
