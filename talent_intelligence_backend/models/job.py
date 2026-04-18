from models import db


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.JSON, nullable=True)  # Store requirements as JSON
    status = db.Column(db.String(20), nullable=False, default="open")
    posted_date = db.Column(db.DateTime, nullable=True, default=db.func.now())

    def __repr__(self):
        return f"<Job {self.title} at {self.company}>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "requirements": self.requirements,
            "status": self.status,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
        }
