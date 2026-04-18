# config.py
import os


class Config:
    # ... your existing configs ...

    # Add Celery & Redis configs
    CELERY = {
        "broker_url": os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        "result_backend": os.getenv(
            "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
        ),
        "task_ignore_result": True,
    }
