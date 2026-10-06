# Analysis states are tracked separately from recruiting stages; never conflate them.
ANALYSIS_STATUSES = (
    "queued",
    "running",
    "complete",
    "partial",
    "failed",
    "enqueue_failed",
)
RETRYABLE_ANALYSIS = ("failed", "enqueue_failed", "partial")

STAGES = (
    "screening",
    "interview_scheduled",
    "interview_completed",
    "offer_made",
    "hired",
    "rejected",
)
TRANSITIONS = {
    "screening": ("interview_scheduled", "rejected"),
    "interview_scheduled": ("interview_completed", "rejected"),
    "interview_completed": ("offer_made", "rejected"),
    "offer_made": ("hired", "rejected"),
    "hired": (),
    "rejected": (),
}


class InvalidTransition(ValueError):
    pass


def allowed_actions(stage):
    return list(TRANSITIONS.get(stage, ()))


def can_transition(current_stage, target_stage):
    return target_stage in TRANSITIONS.get(current_stage, ())


def transition_candidate(candidate, target_stage, actor=None):
    # actor is reserved for authenticated audit events in the ownership phase.
    if not can_transition(candidate.status, target_stage):
        raise InvalidTransition(
            f"Candidate cannot move from {candidate.status} to {target_stage}."
        )
    candidate.status = target_stage
    return candidate
