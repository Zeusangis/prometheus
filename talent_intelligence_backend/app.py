import os

from flask import Flask
from flask_migrate import Migrate

from config import Config
from models import db
from routes.create_jobs_routes import jobs_bp
from routes.github_routes import github_bp
from routes.resume_routes import resume_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    Migrate(app, db)

    app.register_blueprint(github_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(jobs_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
