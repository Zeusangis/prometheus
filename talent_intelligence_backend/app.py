import os

from flask import Flask
from flask_migrate import Migrate
from config import Config
from models import db
from utils.celery_setup import celery_init_app

from routes.github_routes import github_bp
from routes.job_routes import jobs_bp
from routes.application_routes import application_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # It's usually better to put these inside your config.py,
    # but defining them here works perfectly fine for now!
    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)

    # Initialize Celery
    # Register blueprints
    app.register_blueprint(github_bp)
    app.register_blueprint(application_bp)
    app.register_blueprint(jobs_bp)

    return app


app = create_app()
celery_app = celery_init_app(app)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
