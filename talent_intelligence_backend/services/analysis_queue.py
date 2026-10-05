from flask import current_app

from models import db
from tasks.resume_tasks import process_resume_task


def enqueue_analysis(candidate):
    try:
        task = process_resume_task.delay(candidate.id)
        return task.id
    except Exception:
        current_app.logger.exception("Analysis enqueue failed candidate_id=%s", candidate.id)
        # The worker never ran. Preserve the application and expose a safe retry state.
        candidate.analysis_status = "enqueue_failed"
        candidate.analysis_error = "Analysis could not be queued. A recruiter can retry."
        db.session.commit()
        return None
