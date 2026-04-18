from models import db

# here i also want to add the recuriter data and get the company data from the recruiter data and then add it to the job data and then return the job data with the company data in the response


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.JSON, nullable=True)  # Store requirements as JSON
    recruiter_data = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="open")
    posted_date = db.Column(db.DateTime, nullable=True, default=db.func.now())
    applicants = db.relationship("Candidate", backref="job", lazy=True)

    def __repr__(self):
        return f"<Job {self.title} at {self.company}>"

    def to_dict(self):
        company_data = self._extract_company_data()
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "company_data": company_data,
            "location": self.location,
            "description": self.description,
            "requirements": self.requirements,
            "recruiter_data": self.recruiter_data,
            "status": self.status,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
        }

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
