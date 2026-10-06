import os

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from config import configure_app
from models import db
from utils.celery_setup import celery_init_app
from utils.api_errors import register_error_handlers
from utils.commands import register_commands
from services.auth import register_auth_guard
from services.ai.gemini import provider_status
from routes.auth_routes import auth_bp

from routes.github_routes import github_bp
from routes.job_routes import jobs_bp
from routes.application_routes import application_bp
from routes.check_portfolio_routes import check_portfolio_bp


def create_app(config_overrides=None):
    app = Flask(__name__)
    configure_app(app, config_overrides)

    CORS(app, resources={r"/api/*": {"origins": app.config["FRONTEND_ORIGIN"]}})

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)

    celery_init_app(app)
    register_error_handlers(app)
    register_auth_guard(app)
    register_commands(app)
    app.register_blueprint(auth_bp)

    @app.get("/api/health")
    def health():
        # Readiness only: booleans and a model name, never a credential.
        return {"status": "ok", "service": "TrueHire", **provider_status()}

    # Register blueprints
    app.register_blueprint(github_bp)
    app.register_blueprint(application_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(check_portfolio_bp)

    return app


app = create_app()
celery_app = app.extensions["celery"]

if __name__ == "__main__":
    app.run(port=5000)
