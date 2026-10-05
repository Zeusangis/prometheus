import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_ROOT.parent / ".env")
# Compatibility for the existing non-Docker setup; existing environment wins.
load_dotenv(BACKEND_ROOT / ".env")


class DevelopmentConfig:
    DEBUG = False
    TESTING = False
    SECRET_KEY = "dev-secret-key"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    # Allow bounded multipart overhead; enforce the exact PDF size in the route.
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024 + 64 * 1024


class TestConfig(DevelopmentConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CELERY = {"broker_url": "memory://", "result_backend": "cache+memory://"}


class ProductionConfig(DevelopmentConfig):
    SECRET_KEY = None
    SESSION_COOKIE_SECURE = True


def configure_app(app, overrides=None):
    environment = os.environ.get("FLASK_ENV", "development")
    configs = {
        "development": DevelopmentConfig,
        "test": TestConfig,
        "production": ProductionConfig,
    }
    if environment not in configs:
        raise ValueError("FLASK_ENV must be development, test, or production")
    app.config.from_object(configs[environment])
    database_url = os.environ.get("DATABASE_URL") or app.config.get(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///talent_intelligence.db"
    )
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or app.config["SECRET_KEY"],
        SQLALCHEMY_DATABASE_URI=database_url,
        UPLOAD_FOLDER=os.environ.get("UPLOAD_FOLDER") or str(BACKEND_ROOT / "uploads"),
        FRONTEND_ORIGIN=os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173"),
        CELERY={
            "broker_url": os.environ.get("CELERY_BROKER_URL") or app.config.get("CELERY", {}).get(
                "broker_url", "redis://localhost:6379/0"
            ),
            "result_backend": os.environ.get("CELERY_RESULT_BACKEND") or app.config.get("CELERY", {}).get(
                "result_backend", "redis://localhost:6379/0"
            ),
            "task_ignore_result": True,
            "task_publish_retry": False,
            "broker_connection_timeout": 3,
            "imports": ("tasks.resume_tasks",),
        },
    )
    if overrides:
        app.config.update(overrides)
    if environment == "production":
        secret = app.config.get("SECRET_KEY")
        if not secret or secret == "dev-secret-key" or len(secret) < 32:
            raise ValueError("Production requires an explicit SECRET_KEY of at least 32 characters")
        if not os.environ.get("DATABASE_URL"):
            raise ValueError("Production requires DATABASE_URL")
