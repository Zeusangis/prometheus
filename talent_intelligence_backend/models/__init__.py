from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

# Import models so Flask-Migrate can discover them.
from models.analysis import ResumeAnalysis, GitHubAnalysis, RepositoryAnalysis  # noqa: E402,F401
from models.auth import User, Organization, OrganizationMembership  # noqa: E402,F401
from models.candidate import Candidate  # noqa: E402,F401
from models.job import Job  # noqa: E402,F401
from models.meeting_summary import MeetingSummary  # noqa: E402,F401
