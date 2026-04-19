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

    def update_from_frontend_payload(self, payload):
        payload = payload or {}

        job = payload.get("job") if isinstance(payload.get("job"), dict) else {}
        scraper = (
            payload.get("scraper") if isinstance(payload.get("scraper"), dict) else {}
        )
        interview = (
            payload.get("interview")
            if isinstance(payload.get("interview"), dict)
            else {}
        )

        # Core job fields
        if "title" in job:
            self.title = job.get("title") or ""
        elif "title" in payload:
            self.title = payload.get("title") or ""

        if "company" in job:
            self.company = job.get("company") or self.company
        elif "company" in payload:
            self.company = payload.get("company") or self.company

        if "location" in job:
            self.location = job.get("location")
        elif "location" in payload:
            self.location = payload.get("location")

        if "description" in job:
            self.description = job.get("description") or ""
        elif "description" in payload:
            self.description = payload.get("description") or ""

        if "status" in payload:
            self.status = payload.get("status") or self.status

        # Requirements
        requirements = dict(self.requirements or {})
        if "jobType" in job:
            requirements["jobType"] = job.get("jobType") or ""
        elif "jobType" in payload:
            requirements["jobType"] = payload.get("jobType") or ""

        if "languages" in job:
            requirements["languages"] = list(job.get("languages") or [])
        elif "languages" in payload:
            requirements["languages"] = list(payload.get("languages") or [])

        if "frameworks" in job:
            requirements["frameworks"] = list(job.get("frameworks") or [])
        elif "frameworks" in payload:
            requirements["frameworks"] = list(payload.get("frameworks") or [])

        if "requirements" in payload and isinstance(payload.get("requirements"), dict):
            requirements.update(payload.get("requirements") or {})
        self.requirements = requirements

        # Scraper config
        scraper_config = dict(self.scraper_config or {})
        if "scraperMetrics" in scraper:
            scraper_config["scraperMetrics"] = scraper.get("scraperMetrics") or {}
        elif "scraperMetrics" in payload:
            scraper_config["scraperMetrics"] = payload.get("scraperMetrics") or {}

        if "scraperInstructions" in scraper:
            scraper_config["scraperInstructions"] = (
                scraper.get("scraperInstructions") or ""
            )
        elif "scraperInstructions" in payload:
            scraper_config["scraperInstructions"] = (
                payload.get("scraperInstructions") or ""
            )

        if "scraper_config" in payload and isinstance(
            payload.get("scraper_config"), dict
        ):
            scraper_config.update(payload.get("scraper_config") or {})
        self.scraper_config = scraper_config

        # Interview config
        interview_config = dict(self.interview_config or {})
        if "interviewTone" in interview:
            interview_config["interviewTone"] = interview.get("interviewTone") or ""
        elif "interviewTone" in payload:
            interview_config["interviewTone"] = payload.get("interviewTone") or ""

        if "interviewFocus" in interview:
            interview_config["interviewFocus"] = list(
                interview.get("interviewFocus") or []
            )
        elif "interviewFocus" in payload:
            interview_config["interviewFocus"] = list(
                payload.get("interviewFocus") or []
            )

        if "customQuestions" in interview:
            interview_config["customQuestions"] = list(
                interview.get("customQuestions") or []
            )
        elif "customQuestions" in payload:
            interview_config["customQuestions"] = list(
                payload.get("customQuestions") or []
            )

        if "interviewLength" in interview:
            interview_config["interviewLength"] = interview.get("interviewLength")
        elif "interviewLength" in payload:
            interview_config["interviewLength"] = payload.get("interviewLength")

        if "interviewInstructions" in interview:
            interview_config["interviewInstructions"] = (
                interview.get("interviewInstructions") or ""
            )
        elif "interviewInstructions" in payload:
            interview_config["interviewInstructions"] = (
                payload.get("interviewInstructions") or ""
            )

        if "interview_config" in payload and isinstance(
            payload.get("interview_config"), dict
        ):
            interview_config.update(payload.get("interview_config") or {})
        self.interview_config = interview_config

        # Optional recruiter object replacement
        if "recruiter_data" in payload and isinstance(
            payload.get("recruiter_data"), dict
        ):
            self.recruiter_data = payload.get("recruiter_data")

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
