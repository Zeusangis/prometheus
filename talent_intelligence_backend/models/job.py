from models import db


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.JSON, nullable=True)
    scraper_config = db.Column(db.JSON, nullable=True)  # new
    interview_config = db.Column(db.JSON, nullable=True)  # new
    recruiter_data = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="open")
    posted_date = db.Column(db.DateTime, nullable=True, default=db.func.now())
    applicants = db.relationship("Candidate", back_populates="job", lazy=True)

    def __repr__(self):
        return f"<Job {self.title} at {self.company}>"

    def to_dict(self):
        company_data = self._extract_company_data()
        req = self.requirements or {}
        scraper = self.scraper_config or {}
        interview = self.interview_config or {}
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "company_data": company_data,
            "location": self.location,
            "description": self.description,
            "jobType": req.get("jobType"),
            "languages": req.get("languages", []),
            "frameworks": req.get("frameworks", []),
            "scraperMetrics": scraper.get("scraperMetrics", {}),
            "scraperInstructions": scraper.get("scraperInstructions", ""),
            "interviewTone": interview.get("interviewTone", ""),
            "interviewFocus": interview.get("interviewFocus", []),
            "customQuestions": interview.get("customQuestions", []),
            "interviewLength": interview.get("interviewLength"),
            "interviewInstructions": interview.get("interviewInstructions", ""),
            "requirements": req,
            "scraper_config": scraper,
            "interview_config": interview,
            "recruiter_data": self.recruiter_data,
            "status": self.status,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
        }

    @classmethod
    def from_frontend_payload(cls, payload, *, company, recruiter_data=None):
        payload = payload or {}
        job = payload.get("job") or {}
        scraper = payload.get("scraper") or {}
        interview = payload.get("interview") or {}

        requirements = {
            "jobType": job.get("jobType") or "",
            "languages": list(job.get("languages") or []),
            "frameworks": list(job.get("frameworks") or []),
        }
        scraper_config = {
            "scraperMetrics": scraper.get("scraperMetrics") or {},
            "scraperInstructions": scraper.get("scraperInstructions") or "",
        }
        interview_config = {
            "interviewTone": interview.get("interviewTone") or "",
            "interviewFocus": list(interview.get("interviewFocus") or []),
            "customQuestions": list(interview.get("customQuestions") or []),
            "interviewLength": interview.get("interviewLength"),
            "interviewInstructions": interview.get("interviewInstructions") or "",
        }

        return cls(
            title=job.get("title") or "",
            company=company or "",
            location=job.get("location"),
            description=job.get("description") or "",
            requirements=requirements,
            scraper_config=scraper_config,
            interview_config=interview_config,
            recruiter_data=recruiter_data,
            status=payload.get("status") or "open",
        )

    def _extract_company_data(self):
        recruiter = self.recruiter_data or {}
        company_data = recruiter.get("company_data")
        if isinstance(company_data, dict):
            return company_data
        company = recruiter.get("company")
        if isinstance(company, dict):
            return company
        if isinstance(company, str) and company:
            return {"name": company}
        company_name = recruiter.get("company_name")
        if isinstance(company_name, str) and company_name:
            return {"name": company_name}
        return None
