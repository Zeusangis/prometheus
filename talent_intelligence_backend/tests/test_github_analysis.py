import base64
import io
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.error import HTTPError, URLError

import pytest

from models import Candidate, RepositoryAnalysis, db
from services.ai.gemini import InvalidProviderOutput
from services.github.analyzer import AI_METRICS, METRICS, analyze_github, analyze_repository, metric_config, validate_review, weighted_score
from services.github.client import GitHubClient, GitHubUnavailable, MAX_REQUESTS, MAX_RESPONSE_BYTES, NoRedirect
from services.github.collector import collect_github, score_file
from tasks.resume_tasks import process_resume_task

SHA = "a" * 40
NOW = datetime.now(timezone.utc)


def repository(name="project", **overrides):
    return {"name": name, "private": False, "owner": {"login": "test-user"}, "fork": False,
            "stargazers_count": 4, "default_branch": "main", "language": "Python",
            "pushed_at": NOW.isoformat(), "size": 10, **overrides}


class EvidenceClient:
    def __init__(self, repos=None, profile_count=None, truncated=False):
        self.repos = repos if repos is not None else [repository()]
        self.profile_count = len(self.repos) if profile_count is None else profile_count
        self.truncated = truncated
        self.calls = []

    def get(self, path, params=None, **kwargs):
        self.calls.append((path, params, kwargs))
        if path == "/users/test-user":
            return {"login": "test-user", "public_repos": self.profile_count}, {}
        if path.endswith("/repos"):
            batch = self.repos[:100] if params["page"] == 1 else self.repos[100:200]
            return batch, {"Link": '<https://evil.invalid/next>; rel="next"'} if self.truncated or (params["page"] == 1 and len(self.repos) > 100) else {}
        if path.endswith("/languages"):
            return {"Python": 75, "JavaScript": 25}, {}
        if path.endswith("/commits"):
            assert params["author"] == "test-user" and params["per_page"] == 30
            commit = {"author": {"login": "test-user"}, "sha": SHA, "commit": {"author": {"date": NOW.isoformat()}}}
            unrelated = {**commit, "author": {"login": "another-author"}}
            unlinked = {**commit, "author": None}
            old = {**commit, "commit": {"author": {"date": (NOW - timedelta(days=100)).isoformat()}}}
            return [commit, unrelated, unlinked, old], {"Link": '<https://evil.invalid/next>; rel="next"'}
        if "/git/trees/" in path:
            return {"sha": SHA, "truncated": False, "tree": [
                {"path": "app.py", "sha": SHA, "type": "blob", "mode": "100644", "size": 50},
                {"path": ".env", "sha": SHA, "type": "blob", "mode": "100644", "size": 50},
                {"path": "node_modules/secret.js", "sha": SHA, "type": "blob", "mode": "100644", "size": 50},
                {"path": "alias.py", "sha": SHA, "type": "blob", "mode": "120000", "size": 50},
                {"path": "big.py", "sha": SHA, "type": "blob", "mode": "100644", "size": 50001},
            ]}, {}
        if "/git/blobs/" in path:
            content = b"def api(): return 'Python evidence'\n"
            return {"encoding": "base64", "size": len(content), "content": base64.b64encode(content).decode()}, {}
        raise AssertionError(path)


@pytest.fixture
def job():
    return SimpleNamespace(title="Python API Engineer", description="Build tested APIs",
                           requirements={"languages": ["Python"], "frameworks": ["Flask"]},
                           scraper_config={"scraperMetrics": {}, "scraperInstructions": "Verify auth evidence"})


@pytest.fixture
def review():
    return {"dimensions": {key: {"score": 80, "reasoning": "Sampled evidence in app.py", "evidence_paths": ["app.py"]} for key in AI_METRICS},
            "strengths": ["Readable sampled function"], "red_flags": [],
            "recruiter_summary": "Limited public sample; verify candidate authorship."}


def test_author_filtered_sample_and_file_provenance():
    client = EvidenceClient()
    evidence = collect_github("test-user", client)
    assert evidence["total_public_repos"] == 1
    assert evidence["total_stars"] == 4
    assert evidence["candidate_attributed_commits"] == 1
    repo = evidence["repositories"][0]
    assert [file["path"] for file in repo["files"]] == ["app.py"]
    assert repo["evidence_metadata"]["files"][0]["sha"] == SHA
    assert repo["evidence_metadata"]["commit_sample_truncated"] is True
    assert "not lifetime" in repo["evidence_metadata"]["commit_scope"]
    assert all(path.startswith(("/users/test-user", "/repos/test-user/")) for path, _, _ in client.calls)
    assert not any("evil" in path for path, _, _ in client.calls)
    assert len(client.calls) == 6


def test_pagination_repo_cap_and_unknown_aggregate_stars():
    client = EvidenceClient([repository(f"project-{i}") for i in range(250)], profile_count=250, truncated=True)
    evidence = collect_github("test-user", client)
    assert evidence["summary"]["listed_repos"] == 200
    assert len(evidence["repositories"]) == 3
    assert evidence["summary"]["repository_listing_truncated"] is True
    assert evidence["summary"]["repository_analysis_sampled"] is True
    assert evidence["total_stars"] is None
    assert evidence["summary"]["sample_stars"] == 800
    # The same commit present in several repositories/forks must not inflate activity.
    assert evidence["candidate_attributed_commits"] == 1
    assert len(client.calls) == 15


def test_forks_private_and_outside_owner_are_not_authorship_proof():
    client = EvidenceClient([repository("fork", fork=True), repository("original"),
                             repository("private", private=True), repository("outside", owner={"login": "other"})])
    evidence = collect_github("test-user", client)
    assert [r["repo_name"] for r in evidence["repositories"]] == ["test-user/original", "test-user/fork"]
    assert evidence["repositories"][1]["fork"] is True
    assert "not proof" in evidence["repositories"][1]["evidence_metadata"]["authorship_caveat"]
    assert evidence["total_stars"] is None


def test_repository_failure_retains_other_evidence():
    class PartialClient(EvidenceClient):
        def get(self, path, *args, **kwargs):
            if "/bad/" in path:
                raise GitHubUnavailable("GitHub access or rate limit prevented analysis. Retry later.")
            return super().get(path, *args, **kwargs)
    evidence = collect_github("test-user", PartialClient([repository("bad"), repository("good")]))
    assert len(evidence["repositories"]) == 1
    assert evidence["candidate_attributed_commits"] is None
    assert len(evidence["summary"]["errors"]) == 1


@pytest.mark.parametrize("username", ["../etc", "https://evil.invalid", "bad/name", "", "-bad", None])
def test_invalid_username_makes_no_requests(username):
    client = EvidenceClient()
    with pytest.raises(GitHubUnavailable):
        collect_github(username, client)
    assert client.calls == []


def test_empty_account_and_empty_repo():
    evidence = collect_github("test-user", EvidenceClient([]))
    assert evidence["total_stars"] == evidence["candidate_attributed_commits"] == 0
    assert evidence["repositories"] == []
    client = EvidenceClient([repository(size=0)])
    evidence = collect_github("test-user", client)
    assert evidence["repositories"][0]["files"] == []
    assert not any("/git/" in path for path, _, _ in client.calls)


def test_file_ranking_filters_sensitive_and_generated_paths():
    assert score_file("app.py") > score_file("util.py") > 0
    for path in (".env", "secrets.py", "node_modules/app.js", "../app.py", "assets/logo.png", "generated/api.py"):
        assert score_file(path) < 0


def test_job_metric_weights_and_disabled_outputs(job, review, monkeypatch):
    job.scraper_config["scraperMetrics"] = {key: {"enabled": False, "weight": 50} for key in METRICS}
    job.scraper_config["scraperMetrics"].update(languageMatch={"enabled": True, "weight": 25}, codeQuality={"enabled": True, "weight": 75})
    prompts = []
    def generate(prompt, schema):
        prompts.append(prompt)
        return review, "mock-review-model"
    monkeypatch.setattr("services.github.analyzer.generate_json", generate)
    repo = collect_github("test-user", EvidenceClient())["repositories"][0]
    result = analyze_repository(repo, job, metric_config(job))
    assert result["score"] == 78.75  # 75 language * .25 + 80 quality * .75
    assert result["metrics"]["aggregation"]["weight_coverage"] == 1
    assert result["metrics"]["dimensions"]["codeSecurity"]["score"] is None
    assert result["evidence_metadata"]["model_name"] == "mock-review-model"
    assert "Python API Engineer" in prompts[0] and "Verify auth evidence" in prompts[0]
    assert "not proof" in prompts[0] and "untrusted data" in prompts[0]
    assert "secret" not in prompts[0]


def test_all_disabled_does_not_call_ai(job, monkeypatch):
    job.scraper_config["scraperMetrics"] = {key: {"enabled": False, "weight": 50} for key in METRICS}
    def forbidden(*_):
        raise AssertionError("Disabled metrics must not call provider")
    monkeypatch.setattr("services.github.analyzer.generate_json", forbidden)
    repo = collect_github("test-user", EvidenceClient())["repositories"][0]
    result = analyze_repository(repo, job, metric_config(job))
    assert result["score"] is None
    assert result["metrics"]["aggregation"]["weight_coverage"] is None


def test_unknown_metrics_excluded_from_denominator(job):
    config = metric_config(job)
    dimensions = {key: {"score": None} for key in METRICS}
    dimensions["languageMatch"]["score"] = 75
    assert weighted_score(dimensions, config) == {"score": 75, "available_weight": 50, "enabled_weight": 350, "weight_coverage": 0.1429}


@pytest.mark.parametrize("setting", [{"enabled": "false", "weight": 50}, {"enabled": True, "weight": -1}, {"enabled": True, "weight": float("nan")}, {"enabled": True, "weight": True}, {"enabled": True, "weight": 101}])
def test_invalid_metric_settings_rejected(job, setting):
    job.scraper_config["scraperMetrics"] = {"languageMatch": setting}
    with pytest.raises(GitHubUnavailable):
        metric_config(job)


@pytest.mark.parametrize("mutation", [
    lambda r: r["dimensions"]["codeQuality"].update(score=101),
    lambda r: r["dimensions"]["codeQuality"].update(score=True),
    lambda r: r["dimensions"]["codeQuality"].update(score=float("nan")),
    lambda r: r["dimensions"]["codeQuality"].update(evidence_paths=["invented.py"]),
    lambda r: r["dimensions"]["codeQuality"].update(evidence_paths=[]),
    lambda r: r.update(strengths=[42]),
    lambda r: r.update(recruiter_summary=""),
    lambda r: r.pop("dimensions"),
])
def test_repository_provider_validation(review, mutation):
    mutation(review)
    with pytest.raises(InvalidProviderOutput):
        validate_review(review, [{"path": "app.py"}])


def test_provider_failure_keeps_measured_evidence_partial(job, monkeypatch):
    monkeypatch.setattr("services.github.analyzer.collect_github", lambda _: collect_github("test-user", EvidenceClient()))
    def fail(*_):
        raise RuntimeError("secret-key private provider URL")
    monkeypatch.setattr("services.github.analyzer.generate_json", fail)
    result = analyze_github("test-user", job)
    assert result["status"] == "partial"
    assert result["repositories"][0]["metrics"]["dimensions"]["languageMatch"]["score"] == 75
    assert result["repositories"][0]["metrics"]["dimensions"]["codeQuality"]["score"] is None
    assert "secret-key" not in str(result)
    assert result["repositories"][0]["score"] is not None


def test_no_successful_repository_evidence_is_failed(job, monkeypatch):
    evidence = collect_github("test-user", EvidenceClient())
    evidence["repositories"] = []
    evidence["summary"]["errors"] = [{"repo_name": "project", "message": "Rate limit"}]
    monkeypatch.setattr("services.github.analyzer.collect_github", lambda _: evidence)
    assert analyze_github("test-user", job)["status"] == "failed"


def test_resume_failure_does_not_block_github_persistence_or_retry(apply, app, client, monkeypatch):
    candidate_id = apply().json["candidateId"]
    monkeypatch.setattr("services.github.analyzer.collect_github", lambda _: collect_github("test-user", EvidenceClient()))
    monkeypatch.setattr("tasks.resume_tasks._extract_pdf_text", lambda _: "Readable text")
    with app.app_context():
        candidate = db.session.get(Candidate, candidate_id)
        candidate.job.scraper_config = {"scraperMetrics": {key: {"enabled": key == "languageMatch", "weight": 50} for key in METRICS}}
        db.session.commit()
        assert process_resume_task.run(candidate_id)["status"] == "partial"
        assert candidate.resume_analysis.status == "failed"
        assert candidate.github_analysis.status == "complete"
        assert RepositoryAnalysis.query.count() == 1
        assert candidate.status == "screening"
    result = client.get(f"/api/candidates/{candidate_id}/analysis").json
    assert result["github"]["repositories"][0]["score"] == 75
    assert result["github"]["repositories"][0]["pushed_at"] is not None
    assert result["github"]["summary"]["sample_mean_score"] == 75
    assert result["github"]["candidate_attributed_commits"] == 1
    assert "content" not in result["github"]["repositories"][0]["evidence_metadata"]["files"][0]
    assert client.post(f"/api/candidates/{candidate_id}/analysis/retry").status_code == 202
    def forbidden(*_):
        raise AssertionError("A complete component must survive retry")
    monkeypatch.setattr("services.candidate_analysis.analyze_github", forbidden)
    with app.app_context():
        assert process_resume_task.run(candidate_id)["status"] == "partial"
        assert RepositoryAnalysis.query.count() == 1
        assert db.session.get(Candidate, candidate_id).github_analysis.status == "complete"


def test_failed_github_retry_clears_stale_repository_outputs(apply, app, client, monkeypatch):
    candidate_id = apply().json["candidateId"]
    with app.app_context():
        candidate = db.session.get(Candidate, candidate_id)
        candidate.analysis_status = "partial"
        candidate.resume_analysis.status = "complete"
        candidate.github_analysis.status = "partial"
        candidate.github_analysis.total_stars = 999
        candidate.github_analysis.repositories.append(RepositoryAnalysis(repo_name="test-user/project", repo_url="https://github.com/test-user/project", score=100))
        db.session.commit()
    def fail(*_):
        raise RuntimeError("secret-key /private/path")
    monkeypatch.setattr("services.candidate_analysis.analyze_github", fail)
    assert client.post(f"/api/candidates/{candidate_id}/analysis/retry").status_code == 202
    with app.app_context():
        assert process_resume_task.run(candidate_id)["status"] == "partial"
        candidate = db.session.get(Candidate, candidate_id)
        assert candidate.github_analysis.status == "failed"
        assert candidate.github_analysis.total_stars is None
        assert RepositoryAnalysis.query.count() == 0
    result = client.get(f"/api/candidates/{candidate_id}/analysis").json
    assert "secret-key" not in str(result) and "/private/path" not in str(result)


def test_partial_github_retry_replaces_rows_and_preserves_resume(apply, app, client, monkeypatch):
    candidate_id = apply().json["candidateId"]
    with app.app_context():
        candidate = db.session.get(Candidate, candidate_id)
        candidate.analysis_status = "partial"
        candidate.resume_analysis.status = "complete"
        candidate.resume_analysis.ats_score = candidate.ats_score = 70
        candidate.github_analysis.status = "partial"
        candidate.github_analysis.repositories.append(RepositoryAnalysis(repo_name="test-user/project", repo_url="https://github.com/test-user/project"))
        candidate.job.scraper_config = {"scraperMetrics": {key: {"enabled": False, "weight": 50} for key in METRICS}}
        db.session.commit()
    monkeypatch.setattr("services.github.analyzer.collect_github", lambda _: collect_github("test-user", EvidenceClient()))
    assert client.post(f"/api/candidates/{candidate_id}/analysis/retry").status_code == 202
    with app.app_context():
        assert process_resume_task.run(candidate_id)["status"] == "complete"
        assert RepositoryAnalysis.query.count() == 1
        candidate = db.session.get(Candidate, candidate_id)
        assert candidate.ats_score == 70 and candidate.status == "screening"


class Response(io.BytesIO):
    headers = {}


def make_client(monkeypatch, payload=b'{}'):
    monkeypatch.setenv("GITHUB_TOKEN", "test-only-private-token")
    client = GitHubClient()
    calls = []
    def open_request(request, timeout):
        calls.append((request, timeout))
        return Response(payload)
    client.opener = SimpleNamespace(open=open_request)
    return client, calls


def test_client_fixed_origin_headers_and_timeout(monkeypatch):
    client, calls = make_client(monkeypatch)
    assert client.get("/users/test-user")[0] == {}
    request, timeout = calls[0]
    assert request.full_url == "https://api.github.com/users/test-user"
    assert request.get_header("Authorization") == "Bearer test-only-private-token"
    assert 0 < timeout <= 5
    assert NoRedirect().redirect_request(None, None, None, None, None, "https://evil.invalid") is None


@pytest.mark.parametrize("path", ["https://evil.invalid", "//evil.invalid", "/users/x?token=secret", "/users/x#fragment"])
def test_client_rejects_external_paths(monkeypatch, path):
    client, calls = make_client(monkeypatch)
    with pytest.raises(GitHubUnavailable):
        client.get(path)
    assert calls == []


def test_client_request_time_and_response_caps(monkeypatch):
    client, calls = make_client(monkeypatch)
    client.requests = MAX_REQUESTS
    with pytest.raises(GitHubUnavailable, match="limit"):
        client.get("/users/test-user")
    assert calls == []
    client.requests = 0
    client.deadline = 0
    with pytest.raises(GitHubUnavailable, match="limit"):
        client.get("/users/test-user")
    assert calls == []
    client, _ = make_client(monkeypatch, b'x' * (MAX_RESPONSE_BYTES + 1))
    with pytest.raises(GitHubUnavailable, match="size limit"):
        client.get("/users/test-user")


@pytest.mark.parametrize("code, message", [(403, "rate limit"), (429, "rate limit"), (404, "not found"), (500, "temporarily unavailable"), (302, "temporarily unavailable")])
def test_client_safe_http_errors(monkeypatch, code, message):
    client, _ = make_client(monkeypatch)
    def fail(*args, **kwargs):
        raise HTTPError("https://secret.invalid", code, "private-token", {}, None)
    client.opener = SimpleNamespace(open=fail)
    with pytest.raises(GitHubUnavailable, match=message) as error:
        client.get("/users/test-user")
    assert "private-token" not in str(error.value)
    if code == 403:
        client.opener = SimpleNamespace(open=lambda *args, **kwargs: (_ for _ in ()).throw(HTTPError("", 409, "", {}, None)))
        assert client.get("/repos/test-user/empty/commits", empty_repo=True)[0] == []


@pytest.mark.parametrize("payload", [b'not json', b'\xff'])
def test_client_invalid_json(monkeypatch, payload):
    client, _ = make_client(monkeypatch, payload)
    with pytest.raises(GitHubUnavailable, match="invalid evidence"):
        client.get("/users/test-user")


def test_client_safe_network_failure(monkeypatch):
    client, _ = make_client(monkeypatch)
    def fail(*args, **kwargs):
        raise URLError("secret-token network path")
    client.opener = SimpleNamespace(open=fail)
    with pytest.raises(GitHubUnavailable, match="could not be reached"):
        client.get("/users/test-user")


def test_malformed_profile_is_not_zero_evidence():
    class BadClient(EvidenceClient):
        def get(self, *args, **kwargs):
            return {"login": "test-user", "public_repos": None}, {}
    with pytest.raises(GitHubUnavailable):
        collect_github("test-user", BadClient())


def test_tree_and_text_truncation_reported():
    class BigClient(EvidenceClient):
        def get(self, path, params=None, **kwargs):
            if "/git/trees/" in path:
                return {"sha": SHA, "truncated": True, "tree": [{"type": "blob", "mode": "100644", "path": f"api-{i}.py", "sha": SHA, "size": 5000} for i in range(3100)]}, {}
            if "/git/blobs/" in path:
                return {"encoding": "base64", "size": 5000, "content": base64.b64encode(b'a' * 5000).decode()}, {}
            return super().get(path, params, **kwargs)
    evidence = collect_github("test-user", BigClient())
    repo = evidence["repositories"][0]
    assert len(repo["files"]) == 3
    assert all(len(f["content"]) == 4000 and f["truncated"] for f in repo["files"])
    assert repo["evidence_metadata"]["tree_truncated"] is True
    # Raw code is only transient prompt input, not persisted provenance.
    assert "content" not in json.dumps(repo["evidence_metadata"])
