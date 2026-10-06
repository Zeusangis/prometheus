import json
from types import SimpleNamespace

import pytest

from services.ai.gemini import InvalidProviderOutput, ProviderUnavailable, generate_json
from services.resume.analyzer import CATEGORY_LIMITS, build_prompt, validate_result


@pytest.fixture
def valid_result():
    return {
        "ats_score": 100, "breakdown": dict(CATEGORY_LIMITS),
        "missing_keywords": [], "weak_areas": [], "top_improvements": [], "projects": [],
        "final_verdict": "Evidence supports relevant skills; verify with the applicant.",
    }


@pytest.mark.parametrize("mutation", [
    lambda r: r.pop("projects"),
    lambda r: r.update(ats_score=True),
    lambda r: r.update(ats_score=float("nan")),
    lambda r: r.update(ats_score=float("inf")),
    lambda r: r.update(ats_score=99),
    lambda r: r["breakdown"].update(keyword_match=26),
    lambda r: r["breakdown"].pop("education"),
    lambda r: r.update(breakdown=[]),
    lambda r: r.update(projects=[42]),
    lambda r: r.update(projects=["x"] * 101),
    lambda r: r.update(projects=["x" * 5001]),
    lambda r: r.update(final_verdict=" "),
    lambda r: r.update(final_verdict="x" * 20001),
])
def test_rejects_invalid_provider_output(valid_result, mutation):
    mutation(valid_result)
    with pytest.raises(InvalidProviderOutput):
        validate_result(valid_result)


def test_validation_removes_unexpected_fields(valid_result):
    valid_result["hire"] = True
    valid_result["breakdown"]["secret"] = "unsafe extra"
    validated = validate_result(valid_result)
    assert "hire" not in validated
    assert "secret" not in validated["breakdown"]
    assert validated["ats_score"] == 100


def test_prompt_is_job_aware_and_resume_is_bounded():
    job = SimpleNamespace(title="Backend Engineer", description="Build secure APIs",
                          requirements={"languages": ["Python"], "frameworks": ["Flask"]},
                          scraper_config={"scraperInstructions": "Focus on API testing"})
    prompt = build_prompt("a" * 60000 + "TRUNCATED_MARKER", job)
    assert "Backend Engineer" in prompt
    assert "Focus on API testing" in prompt
    assert "TRUNCATED_MARKER" not in prompt
    assert "untrusted data" in prompt
    assert "not a hiring decision" in prompt
    assert "protected traits" in prompt


def test_missing_key_never_initializes_sdk(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    from google import genai
    def forbidden(**_):
        raise AssertionError("SDK must not initialize without a key")
    monkeypatch.setattr(genai, "Client", forbidden)
    with pytest.raises(ProviderUnavailable, match="no GEMINI_API_KEY is configured"):
        generate_json("prompt", {})


@pytest.mark.parametrize("response_text", ["invalid json", "[]", "null", None])
def test_sdk_adapter_rejects_nonobject_json(monkeypatch, response_text):
    from google import genai
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-placeholder")
    client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **_: SimpleNamespace(text=response_text)))
    class Context:
        def __enter__(self):
            return client
        def __exit__(self, *_):
            return False
    monkeypatch.setattr(genai, "Client", lambda **_: Context())
    with pytest.raises(InvalidProviderOutput):
        generate_json("prompt", {})


def test_sdk_adapter_uses_configured_model_schema_and_timeout(monkeypatch):
    from google import genai
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-placeholder")
    monkeypatch.setenv("GEMINI_MODEL", "configured-test-model")
    calls = {}
    def generate(**kwargs):
        calls.update(kwargs)
        return SimpleNamespace(text=json.dumps({"ok": True}))
    class Context:
        def __enter__(self):
            return SimpleNamespace(models=SimpleNamespace(generate_content=generate))
        def __exit__(self, *_):
            return False
    def factory(**kwargs):
        assert kwargs["api_key"] == "test-only-placeholder"
        assert kwargs["http_options"].timeout == 60000
        return Context()
    monkeypatch.setattr(genai, "Client", factory)
    schema = {"type": "object"}
    assert generate_json("role evidence", schema) == ({"ok": True}, "configured-test-model")
    assert calls["model"] == "configured-test-model"
    assert calls["contents"] == "role evidence"
    assert calls["config"].response_json_schema == schema
    assert calls["config"].response_mime_type == "application/json"
