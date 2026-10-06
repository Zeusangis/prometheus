"""Provider failures must reach the recruiter as actionable, safe messages."""

import json
from types import SimpleNamespace

import pytest

from models import Candidate, db
from services.ai.gemini import (
    InvalidProviderOutput,
    ProviderUnavailable,
    classify_provider_error,
    generate_json,
)
from tasks.resume_tasks import process_resume_task


def provider_error(code, message="provider error", module="google.genai.errors"):
    """Build an exception whose module and status mimic the real SDK error."""
    error_class = type("ClientError", (Exception,), {})
    error_class.__module__ = module
    error = error_class(message)
    error.code = code
    return error


@pytest.mark.parametrize("code,message,expected", [
    (400, "API key not valid. API_KEY_INVALID", "GEMINI_API_KEY"),
    (401, "unauthorized", "GEMINI_API_KEY"),
    (403, "permission denied", "GEMINI_API_KEY"),
    (404, "model not found", "GEMINI_MODEL"),
    (429, "RESOURCE_EXHAUSTED", "quota"),
    (500, "internal error", "temporarily unavailable"),
    (503, "upstream failure", "temporarily unavailable"),
    (400, "malformed request", "rejected the request"),
    (302, "unexpected status", "request failed"),
])
def test_sdk_errors_map_to_actionable_messages(code, message, expected):
    mapped = classify_provider_error(provider_error(code, message))
    assert isinstance(mapped, ProviderUnavailable)
    assert expected in str(mapped)
    # Never echo the raw provider payload back into the application.
    assert message not in str(mapped)


def test_transport_errors_are_reported_as_network_failures():
    mapped = classify_provider_error(provider_error(0, "connection refused", module="httpx._exceptions"))
    assert isinstance(mapped, ProviderUnavailable)
    assert "could not be reached" in str(mapped)


def test_unknown_errors_are_not_masked():
    # A bug in our own call must surface as a bug, not as a provider outage.
    assert classify_provider_error(TypeError("bad call")) is None


@pytest.fixture
def no_sleep(monkeypatch):
    """Replace the backoff sleep with a recorder so retry tests stay instant."""
    recorded = []
    monkeypatch.setattr(
        "services.ai.gemini.time",
        SimpleNamespace(sleep=lambda seconds: recorded.append(seconds)),
    )
    return recorded


def client_returning(monkeypatch, outcomes):
    """Patch genai.Client so generate_content yields outcomes in order, counting calls."""
    from google import genai

    calls = {"n": 0}

    def generate(**_):
        outcome = outcomes[min(calls["n"], len(outcomes) - 1)]
        calls["n"] += 1
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(text=outcome)

    class Context:
        def __enter__(self):
            return SimpleNamespace(models=SimpleNamespace(generate_content=generate))

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(genai, "Client", lambda **_: Context())
    return calls


def test_transient_error_is_retried_and_succeeds(monkeypatch, no_sleep):
    from services.ai.gemini import generate_json

    monkeypatch.setenv("GEMINI_API_KEY", "test-only-placeholder")
    calls = client_returning(
        monkeypatch, [provider_error(503, "high demand"), json.dumps({"ok": True})]
    )
    value, model = generate_json("prompt", {})
    assert value == {"ok": True}
    assert model == "gemini-flash-lite-latest"
    assert calls["n"] == 2
    assert no_sleep == [1.0]


def test_transient_error_gives_up_after_bounded_attempts(monkeypatch, no_sleep):
    from services.ai.gemini import generate_json

    monkeypatch.setenv("GEMINI_API_KEY", "test-only-placeholder")
    monkeypatch.setenv("GEMINI_RETRY_ATTEMPTS", "3")
    calls = client_returning(monkeypatch, [provider_error(503, "high demand")])
    with pytest.raises(ProviderUnavailable, match="temporarily unavailable"):
        generate_json("prompt", {})
    assert calls["n"] == 3
    assert no_sleep == [1.0, 2.0]


def test_long_window_quota_is_not_retried(monkeypatch, no_sleep):
    """A daily free-tier quota must fail fast, not burn three requests of a tiny budget."""
    from services.ai.gemini import generate_json

    monkeypatch.setenv("GEMINI_API_KEY", "test-only-placeholder")
    error = provider_error(429, "RESOURCE_EXHAUSTED")
    error.details = {"error": {"details": [
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "21198s"},
    ]}}
    calls = client_returning(monkeypatch, [error])
    with pytest.raises(ProviderUnavailable, match="quota"):
        generate_json("prompt", {})
    assert calls["n"] == 1
    assert no_sleep == []


def test_short_server_retry_delay_is_honoured(monkeypatch, no_sleep):
    from services.ai.gemini import generate_json

    monkeypatch.setenv("GEMINI_API_KEY", "test-only-placeholder")
    error = provider_error(429, "RESOURCE_EXHAUSTED")
    error.details = {"error": {"details": [
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "2s"},
    ]}}
    calls = client_returning(monkeypatch, [error, json.dumps({"ok": True})])
    assert generate_json("prompt", {})[0] == {"ok": True}
    assert calls["n"] == 2
    assert no_sleep == [2.0]


def test_permanent_error_is_not_retried(monkeypatch, no_sleep):
    from services.ai.gemini import generate_json

    monkeypatch.setenv("GEMINI_API_KEY", "test-only-placeholder")
    calls = client_returning(monkeypatch, [provider_error(404, "model not found")])
    with pytest.raises(ProviderUnavailable, match="GEMINI_MODEL"):
        generate_json("prompt", {})
    assert calls["n"] == 1
    assert no_sleep == []


def test_generate_json_raises_mapped_error(monkeypatch, no_sleep):
    from google import genai

    monkeypatch.setenv("GEMINI_API_KEY", "test-only-placeholder")
    error = provider_error(429, "RESOURCE_EXHAUSTED")

    class Context:
        def __enter__(self):
            return SimpleNamespace(models=SimpleNamespace(generate_content=lambda **_: (_ for _ in ()).throw(error)))

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(genai, "Client", lambda **_: Context())
    with pytest.raises(ProviderUnavailable, match="quota"):
        generate_json("prompt", {})


def test_generate_json_does_not_mask_programming_errors(monkeypatch):
    from google import genai

    monkeypatch.setenv("GEMINI_API_KEY", "test-only-placeholder")

    class Context:
        def __enter__(self):
            return SimpleNamespace(models=SimpleNamespace(generate_content=lambda **_: (_ for _ in ()).throw(TypeError("bad call"))))

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(genai, "Client", lambda **_: Context())
    with pytest.raises(TypeError):
        generate_json("prompt", {})


def test_empty_provider_response_is_invalid_output(monkeypatch):
    from google import genai

    monkeypatch.setenv("GEMINI_API_KEY", "test-only-placeholder")
    client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **_: SimpleNamespace(text="")))

    class Context:
        def __enter__(self):
            return client

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(genai, "Client", lambda **_: Context())
    with pytest.raises(InvalidProviderOutput, match="no structured data"):
        generate_json("prompt", {})


def test_pipeline_persists_the_actionable_credentials_message(apply, app, monkeypatch):
    candidate_id = apply().json["candidateId"]
    monkeypatch.setattr(
        "services.resume.analyzer.generate_json",
        lambda *_: (_ for _ in ()).throw(
            ProviderUnavailable(
                "AI provider rejected the credentials. Set a valid GEMINI_API_KEY in the backend .env and retry."
            )
        ),
    )
    monkeypatch.setattr("tasks.resume_tasks._extract_pdf_text", lambda _: "Some resume text")
    with app.app_context():
        assert process_resume_task.run(candidate_id)["status"] == "failed"
        candidate = db.session.get(Candidate, candidate_id)
        resume = candidate.resume_analysis
        assert resume.status == "failed"
        assert "GEMINI_API_KEY" in resume.error_message
        assert resume.ats_score is None
        assert candidate.ats_score is None
