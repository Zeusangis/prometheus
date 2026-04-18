# config.py
import os


class Config:
    # ... your existing configs ...

    # Add Celery & Redis configs
    CELERY = {
        "broker_url": "redis://localhost:6379/0",
        "result_backend": "redis://localhost:6379/0",
        "task_ignore_result": True,
    }
