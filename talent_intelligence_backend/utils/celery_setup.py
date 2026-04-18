# utils/celery_setup.py
from celery import Celery


def celery_init_app(app):
    class FlaskTask(Celery.Task):
        def __call__(self, *args, **kwargs):
            # This ensures your background tasks can talk to the database!
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
