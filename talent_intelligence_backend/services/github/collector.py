import base64
import binascii
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from services.github.client import (
    GitHubClient, GitHubUnavailable, REPO_NAME, USERNAME,
    nonnegative_int, require_dict, require_list,
)

MAX_REPO_PAGES = 2
REPOS_PER_PAGE = 100
MAX_ANALYZED_REPOS = 3
MAX_COMMITS = 30
MAX_TREE_ENTRIES = 3000
MAX_FILES = 3
MAX_FILE_BYTES = 50000
MAX_FILE_CHARS = 4000
LOOKBACK_DAYS = 90
SOURCE_EXTENSIONS = (".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb", ".php", ".cs", ".rs", ".cpp", ".c", ".kt", ".swift", ".sql")


def score_file(path, size=0):
    """Adapted from main1 RepoAnalyzer; ranking is selection, not a candidate score."""
    lower = path.lower()
    if len(path) > 500 or any(part in {"..", "."} for part in path.split("/")):
        return -1
    if any(junk in lower for junk in ("node_modules/", "dist/", "build/", ".next/", "coverage/", "__pycache__/", "vendor/", "generated/", ".min.", "lock.json", ".env", "secret", "credential", "private_key")):
        return -1
    name = lower.rsplit("/", 1)[-1]
    score = 0
    if name in {"main.py", "app.py", "server.py", "index.js", "index.ts", "main.go", "program.cs"}:
        score += 100
    if name in {"package.json", "requirements.txt", "pyproject.toml", "dockerfile", "compose.yml"} or lower.startswith(".github/workflows/"):
        score += 80
    if any(word in lower for word in ("auth", "model", "api", "route", "service", "middleware", "schema")):
        score += 55
    if "test" in lower or "spec" in lower:
        score += 40
    if name.endswith(SOURCE_EXTENSIONS):
        score += 20
    return score + min(size // 250, 30) if score else -1


def parse_time(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (AttributeError, ValueError, TypeError):
        return None


def collect_repository(client, repo, username, since):
    name = repo.get("name", "")
    if not isinstance(name, str) or not REPO_NAME.fullmatch(name) or name in {".", ".."}:
        raise GitHubUnavailable("GitHub returned an invalid repository name.")
    base = f"/repos/{username}/{quote(name, safe='')}"
    languages = require_dict(client.get(base + "/languages")[0])
    languages = {str(key)[:100]: nonnegative_int(value) for key, value in languages.items()}
    commits, headers = client.get(base + "/commits", {"author": username, "since": since.isoformat(), "per_page": MAX_COMMITS}, empty_repo=True)
    commits = require_list(commits)
    attributed, seen_commits = [], set()
    for item in commits[:MAX_COMMITS]:
        # Never substitute committer, raw author name/email or repository-wide history.
        author = item.get("author") or {}
        if not isinstance(author, dict) or str(author.get("login", "")).lower() != username.lower():
            continue
        sha = item.get("sha", "")
        details = item.get("commit") or {}
        if not isinstance(details, dict):
            raise GitHubUnavailable("GitHub returned invalid commit evidence.")
        commit_author = details.get("author") or {}
        if not isinstance(commit_author, dict):
            raise GitHubUnavailable("GitHub returned invalid commit evidence.")
        date = parse_time(commit_author.get("date"))
        if isinstance(sha, str) and re.fullmatch(r"[a-fA-F0-9]{40,64}", sha) and sha not in seen_commits and date and since <= date <= datetime.now(timezone.utc):
            seen_commits.add(sha)
            attributed.append({"sha": sha, "date": date.isoformat(), "url": f"https://github.com/{username}/{name}/commit/{sha}"})
    tree = {"tree": [], "truncated": False}
    if repo.get("size", 0) != 0:
        branch = repo.get("default_branch")
        if not isinstance(branch, str) or not branch or len(branch) > 255:
            raise GitHubUnavailable("GitHub returned invalid branch evidence.")
        tree = require_dict(client.get(base + "/git/trees/" + quote(branch, safe=""), {"recursive": "1"})[0])
    entries = require_list(tree.get("tree", []))
    selected = []
    for item in entries[:MAX_TREE_ENTRIES]:
        path, sha, size = item.get("path"), item.get("sha"), item.get("size", 0)
        if item.get("type") != "blob" or item.get("mode") == "120000" or not isinstance(path, str):
            continue
        size = nonnegative_int(size)
        if size > MAX_FILE_BYTES or not isinstance(sha, str) or not re.fullmatch(r"[a-fA-F0-9]{40,64}", sha):
            continue
        priority = score_file(path, size)
        if priority > 0:
            selected.append((priority, path, sha, size))
    selected.sort(key=lambda item: (-item[0], item[1]))
    files = []
    for _, path, sha, size in selected[:MAX_FILES]:
        blob = require_dict(client.get(base + "/git/blobs/" + sha)[0])
        if blob.get("encoding") != "base64" or nonnegative_int(blob.get("size")) > MAX_FILE_BYTES:
            continue
        try:
            encoded = blob.get("content", "")
            if not isinstance(encoded, str) or len(encoded) > MAX_FILE_BYTES * 2:
                raise ValueError("Oversize encoded file")
            raw = base64.b64decode(encoded.replace("\n", ""), validate=True)
            if len(raw) > MAX_FILE_BYTES or b"\x00" in raw:
                continue
            text = raw.decode("utf-8")
        except (ValueError, UnicodeError, binascii.Error):
            continue
        files.append({"path": path, "sha": sha, "size": size, "content": text[:MAX_FILE_CHARS], "truncated": len(text) > MAX_FILE_CHARS})
    provenance = {
        "source": "GitHub public REST API", "repo_url": f"https://github.com/{username}/{name}",
        "tree_sha": tree.get("sha"), "tree_truncated": bool(tree.get("truncated")) or len(entries) > MAX_TREE_ENTRIES,
        "files": [{k: f[k] for k in ("path", "sha", "size", "truncated")} for f in files],
        "commits": attributed, "commit_sample_truncated": 'rel="next"' in headers.get("Link", ""),
        "commit_scope": f"Candidate-attributed default-branch sample since {since.isoformat()}; not lifetime or cross-repository contributions.",
        "authorship_caveat": "GitHub account association is not identity verification; repository code is not proof of individual authorship.",
    }
    return {
        "repo_name": f"{username}/{name}", "repo_url": provenance["repo_url"],
        "primary_language": repo.get("language"), "pushed_at": parse_time(repo.get("pushed_at")),
        "fork": bool(repo.get("fork")), "stars": nonnegative_int(repo.get("stargazers_count", 0)),
        "languages": languages, "files": files, "evidence_metadata": provenance,
    }


def collect_github(username, client=None):
    if not isinstance(username, str) or not USERNAME.fullmatch(username):
        raise GitHubUnavailable("A valid GitHub username is required.")
    client = client or GitHubClient()
    profile = require_dict(client.get(f"/users/{username}")[0])
    login = profile.get("login")
    if not isinstance(login, str) or login.lower() != username.lower():
        raise GitHubUnavailable("GitHub profile identity did not match the requested account.")
    total = nonnegative_int(profile.get("public_repos"))
    repos, seen, listing_truncated = [], set(), False
    for page in range(1, MAX_REPO_PAGES + 1):
        batch, headers = client.get(f"/users/{username}/repos", {"per_page": REPOS_PER_PAGE, "page": page, "sort": "pushed", "type": "owner"})
        batch = require_list(batch)
        for repo in batch[:REPOS_PER_PAGE]:
            owner = repo.get("owner") or {}
            name = repo.get("name")
            if repo.get("private") is not False or not isinstance(owner, dict) or str(owner.get("login", "")).lower() != username.lower():
                continue
            if isinstance(name, str) and name.lower() not in seen:
                seen.add(name.lower())
                repos.append(repo)
        has_next = 'rel="next"' in headers.get("Link", "")
        listing_truncated = has_next or len(batch) > REPOS_PER_PAGE
        if not has_next:
            break
    listing_truncated = listing_truncated or len(repos) != total
    # Prefer recent original projects, but retain a fork as evidence when no originals exist.
    repos.sort(key=lambda r: (bool(r.get("fork")), str(r.get("pushed_at") or "") == ""))
    since = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    results, errors = [], []
    for repo in repos[:MAX_ANALYZED_REPOS]:
        try:
            results.append(collect_repository(client, repo, username, since))
        except GitHubUnavailable as error:
            errors.append({"repo_name": str(repo.get("name", ""))[:100], "message": str(error)})
    return {
        "username": login, "total_public_repos": total,
        "total_stars": None if listing_truncated else sum(nonnegative_int(r.get("stargazers_count", 0)) for r in repos),
        "candidate_attributed_commits": len({c["sha"] for r in results for c in r["evidence_metadata"]["commits"]}) if not errors else None,
        "repositories": results,
        "summary": {"collected_at": datetime.now(timezone.utc).isoformat(), "listed_repos": len(repos),
                    "analyzed_repos": len(results), "repository_listing_truncated": listing_truncated,
                    "repository_analysis_sampled": len(repos) > MAX_ANALYZED_REPOS,
                    "sample_stars": sum(nonnegative_int(r.get("stargazers_count", 0)) for r in repos),
                    "commit_scope": "Unique candidate-attributed commit SHAs sampled from analyzed repositories within 90 days; not lifetime commits.",
                    "errors": errors, "limits": {"repo_pages": MAX_REPO_PAGES, "analyzed_repos": MAX_ANALYZED_REPOS,
                                                 "commits_per_repo": MAX_COMMITS, "files_per_repo": MAX_FILES}},
    }
