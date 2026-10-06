from datetime import datetime, timezone

from sqlalchemy import event

from models import db

# Event types written to the audit trail. Both are recorded by services/audit.py only.
STAGE_CHANGED = "stage_changed"
ANALYSIS_RETRIED = "analysis_retried"
EVENT_TYPES = (STAGE_CHANGED, ANALYSIS_RETRIED)


class ImmutableAuditRecord(RuntimeError):
    """Raised when something tries to update or delete a recorded audit event."""


def now():
    return datetime.now(timezone.utc)


class StageEvent(db.Model):
    """An immutable record of a recruiting stage change or an analysis retry.

    Rows are append-only: the mapper guards below refuse every UPDATE and DELETE, so
    a recorded event cannot be rewritten or removed to match a later narrative. The
    actor email is stored alongside the user id so the record stays readable even if
    the account is later renamed or deactivated.
    """

    __tablename__ = "stage_events"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)
    from_stage = db.Column(db.String(50), nullable=True)
    to_stage = db.Column(db.String(50), nullable=True)
    previous_analysis_status = db.Column(db.String(50), nullable=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    actor_email = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=now)

    candidate = db.relationship("Candidate", back_populates="stage_events")

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "previous_analysis_status": self.previous_analysis_status,
            "actor_email": self.actor_email,
            "created_at": self.created_at.isoformat(),
        }


@event.listens_for(StageEvent, "before_update")
def _reject_update(mapper, connection, target):
    raise ImmutableAuditRecord(
        "Audit events are append-only; an existing stage event cannot be updated."
    )


@event.listens_for(StageEvent, "before_delete")
def _reject_delete(mapper, connection, target):
    raise ImmutableAuditRecord(
        "Audit events are append-only; an existing stage event cannot be deleted."
    )
