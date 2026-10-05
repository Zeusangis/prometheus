from types import SimpleNamespace

import pytest

from models import Candidate, MeetingSummary, db
from services.candidate_stage import STAGES, TRANSITIONS, InvalidTransition, can_transition, transition_candidate


@pytest.mark.parametrize("current", STAGES)
@pytest.mark.parametrize("target", STAGES)
def test_stage_matrix(current, target):
    candidate = SimpleNamespace(status=current, analysis_status="failed")
    expected = target in TRANSITIONS[current]
    assert can_transition(current, target) is expected
    if expected:
        transition_candidate(candidate, target)
        assert candidate.status == target
    else:
        with pytest.raises(InvalidTransition):
            transition_candidate(candidate, target)
        assert candidate.status == current
    assert candidate.analysis_status == "failed"


def test_api_rejects_jump_and_keeps_meetings_idempotent(apply, client, app, job_id):
    candidate_id = apply().json["candidateId"]
    endpoint = f"/api/candidates/{candidate_id}/stage"
    rejected = client.post(endpoint, json={"stage": "offer_made"})
    assert rejected.status_code == 409
    assert rejected.json["error"]["code"] == "candidate_transition_invalid"
    result = client.post(f"/api/jobs/{job_id}/candidates/{candidate_id}/next-step", json={"next_status": "interview_scheduled"})
    assert result.status_code == 200
    assert len(result.json["meeting_id"]) == 32
    assert client.post(endpoint, json={"stage": "interview_scheduled"}).status_code == 409
    with app.app_context():
        assert MeetingSummary.query.count() == 1
        assert db.session.get(Candidate, candidate_id).analysis_status == "queued"
    for stage in ["interview_completed", "offer_made", "hired"]:
        assert client.post(endpoint, json={"stage": stage}).status_code == 200
    assert client.post(endpoint, json={"stage": "rejected"}).status_code == 409


def test_rejection_is_terminal(apply, client):
    candidate_id = apply().json["candidateId"]
    endpoint = f"/api/candidates/{candidate_id}/stage"
    assert client.post(endpoint, json={"stage": "rejected"}).status_code == 200
    assert client.post(endpoint, json={"stage": "screening"}).status_code == 409
    assert client.get(f"/api/candidates/{candidate_id}").json["candidate"]["allowed_actions"] == []


def test_wrong_job_scope(apply, client, job_id):
    candidate_id = apply().json["candidateId"]
    assert client.post(f"/api/jobs/{job_id + 1}/candidates/{candidate_id}/next-step", json={"next_status": "rejected"}).status_code == 404
