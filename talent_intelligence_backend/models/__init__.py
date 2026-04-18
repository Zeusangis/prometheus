from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

# Import models so Flask-Migrate can discover them.
from models.candidate import Candidate  # noqa: E402,F401
from models.job import Job  # noqa: E402,F401
