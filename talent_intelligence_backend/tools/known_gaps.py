"""Machine-checkable backing for the "not built yet" claims in docs/project-context.md.

Sections 7 (deliberately not built yet) and 8 (suggested next steps) are hand-written
prose, so they can silently drift out of date. Every such claim carries a marker:

    <!-- claim: no-audit-trail -->

``tests/test_project_context.py`` requires a registered check for every marker, runs it,
and fails when the code no longer matches the claim. Implementing one of these features
therefore breaks the test suite until the document, the marker and the entry here are
updated together. That is the point: these sections cannot quietly become false.

Add a check here before adding a marker to the document, and delete both when the claim
stops being true.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "talent_intelligence_backend"
FRONTEND_SRC = REPO_ROOT / "frontend_hackathon_1" / "src"

CLAIM_MARKER = re.compile(r"<!--\s*claim:\s*([a-z0-9][a-z0-9-]*)\s*-->")

# Directories scanned for backend implementation code. tests/ and tools/ are excluded so
# that this registry and the tests describing a gap are not mistaken for the gap closing.
BACKEND_SOURCE_DIRS = ("config", "models", "routes", "services", "tasks", "utils")


def claim_ids(document_text):
    """Claim ids referenced by the document, in order of first appearance."""
    seen = []
    for match in CLAIM_MARKER.finditer(document_text):
        if match.group(1) not in seen:
            seen.append(match.group(1))
    return seen


def _read(path):
    return Path(path).read_text(encoding="utf-8")


def _backend_sources():
    for name in BACKEND_SOURCE_DIRS:
        root = BACKEND_ROOT / name
        if root.exists():
            for path in root.rglob("*.py"):
                if "__pycache__" not in path.parts:
                    yield path


def _table_names():
    from models import db

    return set(db.metadata.tables)


def _assert_no_table(*patterns):
    hits = sorted(name for name in _table_names() if any(re.search(p, name, re.I) for p in patterns))
    assert not hits, f"tables now exist for a claim that says the feature is unbuilt: {hits}"


def _assert_source_free_of(pattern, description):
    hits = [str(path.relative_to(REPO_ROOT)) for path in _backend_sources() if re.search(pattern, _read(path))]
    assert not hits, f"{description} now implemented in {hits}"


def _interviews_are_mocked(app):
    page = _read(FRONTEND_SRC / "pages" / "dashboard" / "InterviewSummaryPage.tsx")
    assert "const interviewSummary = {" in page, (
        "the interview summary is no longer a hard-coded demo dataset"
    )
    _assert_no_table(r"interview", r"session")


def _no_concurrency_hardening(app):
    _assert_no_table(r"lease", r"outbox", r"version")
    _assert_source_free_of(r"\blease\b|\boutbox\b", "worker leases or an enqueue outbox")


def _no_rate_limiting(app):
    requirements = _read(BACKEND_ROOT / "requirements.txt").lower()
    for dependency in ("flask-limiter", "flask_limiter", "slowapi", "limits=="):
        assert dependency not in requirements, f"{dependency} is now a declared dependency"
    _assert_source_free_of(r"\bLimiter\(", "rate limiting")


def _no_object_storage_or_deployment_config(app):
    requirements = _read(BACKEND_ROOT / "requirements.txt").lower()
    for dependency in ("boto3", "google-cloud-storage", "minio"):
        assert dependency not in requirements, f"{dependency} is now a declared dependency"
    for name in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        assert not (REPO_ROOT / name).exists(), f"{name} now exists at the repository root"


def _ci_never_calls_live_providers(app):
    conftest = _read(BACKEND_ROOT / "tests" / "conftest.py")
    assert 'setenv("GEMINI_API_KEY", "")' in conftest, "the suite no longer blanks the Gemini key"
    assert 'setenv("GITHUB_TOKEN", "")' in conftest, "the suite no longer blanks the GitHub token"


def _prototype_residue_is_present(app):
    residue = BACKEND_ROOT / "models" / "github_ats.py"
    assert residue.exists(), "models/github_ats.py was removed; update the document"
    for path in _backend_sources():
        if path.name == "github_ats.py":
            continue
        text = _read(path)
        assert not re.search(r"^\s*(?:from|import)\s+main1\b", text, re.M), f"{path} imports main1"
        assert "github_ats" not in text, f"{path} imports the unused models/github_ats.py"


def _single_organization_ui(app):
    switches = [str(rule) for rule in app.url_map.iter_rules() if "switch" in str(rule).lower()]
    assert not switches, f"an organization-switch route now exists: {switches}"
    for path in FRONTEND_SRC.rglob("*.tsx"):
        assert not re.search(r"switch[ _-]?organization", _read(path), re.I), (
            f"{path} adds an organization switcher"
        )


# id -> (one-line description shown in failures, check run against the code)
CLAIM_CHECKS = {
    "interviews-mocked": (
        "interview summaries are still demo data and live interviews are disabled",
        _interviews_are_mocked,
    ),
    "no-concurrency-hardening": (
        "there are no worker leases, dead-worker recovery, enqueue outbox or versioned analysis history",
        _no_concurrency_hardening,
    ),
    "no-rate-limiting": (
        "authentication and the public apply endpoint are not rate limited",
        _no_rate_limiting,
    ),
    "no-object-storage-or-compose": (
        "there is no object storage, retention policy or deployment configuration",
        _no_object_storage_or_deployment_config,
    ),
    "ci-never-calls-live-providers": (
        "the automated suite blanks provider credentials and never reaches a live provider",
        _ci_never_calls_live_providers,
    ),
    "prototype-residue-present": (
        "main1/ and models/github_ats.py remain as prototype residue",
        _prototype_residue_is_present,
    ),
    "single-organization-ui": (
        "a user belongs to one organization in the UI and there is no organization switcher",
        _single_organization_ui,
    ),
}
