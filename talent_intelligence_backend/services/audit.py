"""Record immutable audit events for stage changes and analysis retries.

Recording an event must never change a stage, alter an analysis status, or fail the
mutation that triggered it. Each event is therefore written through a SAVEPOINT: if the
insert somehow fails, only that savepoint is rolled back and the caller's stage change
or retry still commits. The event itself is never updated or deleted (see
models/stage_event.py).
"""

from flask import current_app

from models import db
from models.stage_event import ANALYSIS_RETRIED, STAGE_CHANGED, StageEvent


def _stage_event(event):
    try:
        # begin_nested() opens a SAVEPOINT immediately, so an insert failure rolls back
        # only the audit row and leaves the surrounding mutation intact.
        with db.session.begin_nested():
            db.session.add(event)
    except Exception:
        current_app.logger.exception(
            "Could not record audit event type=%s candidate_id=%s",
            event.event_type,
            event.candidate_id,
        )


def record_stage_change(candidate, from_stage, to_stage, actor=None):
    """Record a recruiting stage transition for a candidate."""
    _stage_event(StageEvent(
        candidate_id=candidate.id,
        job_id=candidate.job_id,
        event_type=STAGE_CHANGED,
        from_stage=from_stage,
        to_stage=to_stage,
        actor_user_id=getattr(actor, "id", None),
        actor_email=getattr(actor, "email", None),
    ))


def record_analysis_retry(candidate, previous_status, actor=None):
    """Record a recruiter-initiated analysis retry and the status it replaced."""
    _stage_event(StageEvent(
        candidate_id=candidate.id,
        job_id=candidate.job_id,
        event_type=ANALYSIS_RETRIED,
        previous_analysis_status=previous_status,
        actor_user_id=getattr(actor, "id", None),
        actor_email=getattr(actor, "email", None),
    ))


def events_for_candidate(candidate_id):
    """Newest-first audit events for one candidate."""
    return db.session.scalars(
        db.select(StageEvent)
        .where(StageEvent.candidate_id == candidate_id)
        .order_by(StageEvent.created_at.desc(), StageEvent.id.desc())
    ).all()
