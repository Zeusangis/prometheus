



import re
import json
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from google import genai
from google.genai import types


GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 100


# =========================
# Helpers
# =========================

def safe_json_loads(text: str) -> dict:
    text = (text or "").strip()

    if not text:
        return {}

    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_output": text}


def build_headers(token: Optional[str] = None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_get(
    url: str,
    headers: dict,
    params: Optional[dict] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> requests.Response:
    response = requests.get(url, headers=headers, params=params or {}, timeout=timeout)
    response.raise_for_status()
    return response


def get_last_page(link_header: str) -> int:
    if not link_header:
        return 1

    for part in link_header.split(","):
        if 'rel="last"' in part:
            start = part.find("<") + 1
            end = part.find(">")
            url = part[start:end]
            query = parse_qs(urlparse(url).query)
            return int(query.get("page", ["1"])[0])

    return 1


def parse_repo_url(repo_url: str) -> Tuple[str, str]:
    repo_url = repo_url.strip().rstrip("/")

    if repo_url.startswith("http://") or repo_url.startswith("https://"):
        match = re.search(r"github\.com/([^/]+)/([^/]+)", repo_url)
        if not match:
            raise ValueError(f"Invalid GitHub repo URL: {repo_url}")
        owner, repo = match.group(1), match.group(2)
    else:
        parts = repo_url.split("/")
        if len(parts) != 2:
            raise ValueError(f"Repo must be in owner/repo format: {repo_url}")
        owner, repo = parts[0], parts[1]

    if repo.endswith(".git"):
        repo = repo[:-4]

    return owner, repo


# =========================
# GitHub profile summary
# =========================

def get_github_profile_summary(username: str, token: Optional[str] = None) -> dict:
    headers = build_headers(token)
    url = f"{GITHUB_API}/users/{username}"

    print(f"[GitHub] Fetching profile for {username}...")
    response = github_get(url, headers=headers)
    user = response.json()

    created_at = user.get("created_at")
    updated_at = user.get("updated_at")

    account_age_days = None
    if created_at:
        created_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        account_age_days = (datetime.now(timezone.utc) - created_dt).days

    return {
        "top_level_signals": {
            "username": user.get("login"),
            "public_repo_count": user.get("public_repos"),
            "public_gist_count": user.get("public_gists"),
            "followers": user.get("followers"),
            "following": user.get("following"),
            "company": user.get("company"),
            "account_created_at": created_at,
            "profile_updated_at": updated_at,
            "account_age_days": account_age_days,
        },
        "context": {
            "bio": user.get("bio")
        }
    }


# =========================
# Repo stars + commits
# GitHub threading only
# =========================

def get_commit_count(
    owner: str,
    repo_name: str,
    headers: dict,
    timeout: int = DEFAULT_TIMEOUT
) -> int:
    url = f"{GITHUB_API}/repos/{owner}/{repo_name}/commits"

    response = requests.get(
        url,
        headers=headers,
        params={"per_page": 1},
        timeout=timeout
    )

    if response.status_code == 409:
        return 0

    response.raise_for_status()
    link_header = response.headers.get("Link", "")

    if link_header:
        return get_last_page(link_header)

    data = response.json()
    return len(data) if isinstance(data, list) else 0


def get_repo_stats(repo: dict, owner: str, headers: dict) -> dict:
    repo_name = repo["name"]
    stars = repo.get("stargazers_count", 0)

    try:
        commits = get_commit_count(owner=owner, repo_name=repo_name, headers=headers)
        return {
            "repo_name": repo_name,
            "stars": stars,
            "commits": commits,
            "error": None,
        }
    except Exception as exc:
        return {
            "repo_name": repo_name,
            "stars": stars,
            "commits": 0,
            "error": str(exc),
        }


def get_project_details(results: List[dict], projects: List[str]) -> dict:
    result_map = {repo["repo_name"].lower(): repo for repo in results}

    project_status = {}
    for project in projects:
        repo_data = result_map.get(project.lower())
        if repo_data:
            project_status[project] = {
                "exists": True,
                "stars": repo_data["stars"],
                "commits": repo_data["commits"],
            }
        else:
            project_status[project] = {
                "exists": False,
                "stars": 0,
                "commits": 0,
            }

    return project_status


def get_repos_and_stars_threaded(
    username: str,
    token: Optional[str] = None,
    max_workers: int = 8,
    projects: Optional[List[str]] = None
) -> dict:
    headers = build_headers(token)

    print(f"[GitHub] Fetching repos for {username}...")
    repos = []
    page = 1

    while True:
        response = github_get(
            f"{GITHUB_API}/users/{username}/repos",
            headers=headers,
            params={"per_page": 100, "page": page, "sort": "updated"}
        )
        batch = response.json()

        if not batch:
            break

        repos.extend(batch)
        print(f"[GitHub] Loaded page {page}, total repos so far: {len(repos)}")

        if len(batch) < 100:
            break

        page += 1

    print(f"[GitHub] Calculating stars and commits for {len(repos)} repos with threading...")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(get_repo_stats, repo, username, headers) for repo in repos]

        done = 0
        total = len(futures)

        for future in as_completed(futures):
            results.append(future.result())
            done += 1
            if done % 10 == 0 or done == total:
                print(f"[GitHub] Repo stats progress: {done}/{total}")

    results.sort(key=lambda x: x["repo_name"].lower())

    total_stars = sum(item["stars"] for item in results)
    total_commits = sum(item["commits"] for item in results)

    top_3_committed_repos = sorted(results, key=lambda x: x["commits"], reverse=True)[:3]
    top_3_starred_repos = sorted(results, key=lambda x: x["stars"], reverse=True)[:3]
    project_status = get_project_details(results, projects or [])

    print("[GitHub] Repo stats collection complete.")

    return {
        "username": username,
        "total_repos": len(results),
        "total_stars": total_stars,
        "total_commits": total_commits,
        "top_3_committed_repos": [
            {
                "repo_name": repo["repo_name"],
                "commits": repo["commits"],
                "stars": repo["stars"],
            }
            for repo in top_3_committed_repos
        ],
        "top_3_starred_repos": [
            {
                "repo_name": repo["repo_name"],
                "stars": repo["stars"],
                "commits": repo["commits"],
            }
            for repo in top_3_starred_repos
        ],
        "project_check": project_status,
    }


# =========================
# Repo analyzer
# =========================

class RepoAnalyzer:
    def __init__(self, github_token: Optional[str], gemini_api_key: str):
        self.github_headers = build_headers(github_token)

        if not gemini_api_key:
            raise ValueError("gemini_api_key is required")

        self.gemini_client = genai.Client(api_key=gemini_api_key)

    def _github_get_json(self, url: str, params: Optional[dict] = None):
        response = github_get(url, headers=self.github_headers, params=params)
        return response.json()

    def get_repo_metadata(self, owner: str, repo: str) -> Dict:
        repo_data = self._github_get_json(f"{GITHUB_API}/repos/{owner}/{repo}")
        return {
            "full_name": repo_data.get("full_name"),
            "description": repo_data.get("description"),
            "default_branch": repo_data.get("default_branch"),
            "language": repo_data.get("language"),
            "stargazers_count": repo_data.get("stargazers_count"),
            "forks_count": repo_data.get("forks_count"),
            "watchers_count": repo_data.get("watchers_count"),
            "open_issues_count": repo_data.get("open_issues_count"),
            "size_kb": repo_data.get("size"),
            "created_at": repo_data.get("created_at"),
            "updated_at": repo_data.get("updated_at"),
            "pushed_at": repo_data.get("pushed_at"),
            "topics": repo_data.get("topics", []),
            "archived": repo_data.get("archived"),
            "disabled": repo_data.get("disabled"),
        }

    def get_repo_languages(self, owner: str, repo: str) -> Dict:
        return self._github_get_json(f"{GITHUB_API}/repos/{owner}/{repo}/languages")

    def get_default_branch(self, owner: str, repo: str) -> str:
        repo_data = self._github_get_json(f"{GITHUB_API}/repos/{owner}/{repo}")
        return repo_data["default_branch"]

    def get_repo_tree(self, owner: str, repo: str, branch: Optional[str] = None) -> List[Dict]:
        if branch is None:
            branch = self.get_default_branch(owner, repo)

        branch_data = self._github_get_json(f"{GITHUB_API}/repos/{owner}/{repo}/branches/{branch}")
        tree_sha = branch_data["commit"]["commit"]["tree"]["sha"]

        tree_data = self._github_get_json(
            f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{tree_sha}",
            params={"recursive": "1"}
        )
        return tree_data.get("tree", [])

    def get_recent_commit_file_stats(self, owner: str, repo: str, author: Optional[str] = None, per_page: int = 30):
        commit_counts = defaultdict(int)
        commit_summaries = []

        params = {"per_page": per_page}
        if author:
            params["author"] = author

        commits = self._github_get_json(f"{GITHUB_API}/repos/{owner}/{repo}/commits", params=params)

        for commit in commits[:10]:
            sha = commit["sha"]
            detail = self._github_get_json(f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}")

            files = detail.get("files", [])
            changed_paths = []
            patch_summaries = []

            for file_data in files[:8]:
                filename = file_data.get("filename")
                if filename:
                    commit_counts[filename] += 1
                    changed_paths.append(filename)

                patch = file_data.get("patch")
                if patch:
                    patch_summaries.append({
                        "filename": filename,
                        "status": file_data.get("status"),
                        "changes": file_data.get("changes"),
                        "patch_excerpt": patch[:1200],
                    })

            commit_summaries.append({
                "sha": sha,
                "message": detail.get("commit", {}).get("message"),
                "files_changed": changed_paths,
                "patch_summaries": patch_summaries[:4],
            })

        return dict(commit_counts), commit_summaries

    def score_file(self, path: str, size: int = 0, commit_freq: int = 0) -> int:
        path_lower = path.lower()
        filename = path_lower.split("/")[-1]
        score = 0

        entry_points = {
            "main.py", "app.py", "server.py", "manage.py", "wsgi.py", "asgi.py",
            "index.js", "index.ts", "server.js", "server.ts", "main.js", "main.ts",
            "app.js", "app.ts", "program.cs", "main.go"
        }
        if filename in entry_points:
            score += 100

        important_configs = [
            "package.json", "requirements.txt", "pyproject.toml", "pipfile",
            "poetry.lock", "dockerfile", "docker-compose.yml", "compose.yml",
            "tsconfig.json", "vite.config", "webpack.config", ".github/workflows",
            "pytest.ini", "setup.py", "setup.cfg", ".env.example"
        ]
        if any(cfg in path_lower for cfg in important_configs):
            score += 80

        important_keywords = [
            "auth", "login", "signup", "jwt", "session", "oauth",
            "db", "database", "model", "models", "schema", "migration",
            "api", "route", "routes", "controller", "service", "middleware",
            "repository", "serializer", "views", "handlers"
        ]
        if any(word in path_lower for word in important_keywords):
            score += 55

        if "test" in path_lower or "spec" in path_lower:
            score += 40

        junk_patterns = [
            "node_modules/", "dist/", "build/", ".next/", "coverage/",
            "__pycache__/", ".min.js", ".min.css", "vendor/", "generated/",
            "package-lock.json", "yarn.lock", "pnpm-lock.yaml", ".svg", ".png",
            ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".map"
        ]
        if any(j in path_lower for j in junk_patterns):
            score -= 200

        source_exts = (
            ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb",
            ".php", ".cs", ".rs", ".cpp", ".c", ".kt", ".swift", ".sql"
        )
        if filename.endswith(source_exts):
            score += 20

        score += min(size // 250, 30)
        score += commit_freq * 15
        return score

    def fetch_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
        response = requests.get(
            url,
            headers={**self.github_headers, "Accept": "application/vnd.github.raw+json"},
            timeout=DEFAULT_TIMEOUT
        )
        if response.status_code >= 400:
            return None
        return response.text

    def trim_content(self, content: str, max_chars: int = 7000) -> str:
        if len(content) <= max_chars:
            return content
        half = max_chars // 2
        return content[:half] + "\n\n...TRUNCATED...\n\n" + content[-half:]

    def smart_select_repo_evidence(
        self,
        owner: str,
        repo: str,
        author: Optional[str] = None,
        max_files: int = 10
    ) -> Dict:
        print(f"[Gemini Prep] Building evidence for {owner}/{repo}...")

        tree = self.get_repo_tree(owner, repo)
        commit_freq_map, recent_commits = self.get_recent_commit_file_stats(owner, repo, author=author)

        candidates = []
        representative_by_module = {}

        for item in tree:
            if item.get("type") != "blob":
                continue

            path = item["path"]
            size = item.get("size", 0)
            freq = commit_freq_map.get(path, 0)
            score = self.score_file(path, size=size, commit_freq=freq)

            if score <= 0:
                continue

            candidate = {
                "path": path,
                "size": size,
                "commit_frequency": freq,
                "score": score,
            }
            candidates.append(candidate)

            top_module = path.split("/")[0] if "/" in path else "__root__"
            existing = representative_by_module.get(top_module)
            if existing is None or candidate["score"] > existing["score"]:
                representative_by_module[top_module] = candidate

        candidates.sort(key=lambda x: x["score"], reverse=True)
        selected_map = {c["path"]: c for c in candidates[:max_files]}

        for rep in representative_by_module.values():
            if len(selected_map) >= max_files + 4:
                break
            selected_map.setdefault(rep["path"], rep)

        selected_files = []
        for item in sorted(selected_map.values(), key=lambda x: x["score"], reverse=True):
            content = self.fetch_file_content(owner, repo, item["path"])
            selected_files.append({
                **item,
                "content": self.trim_content(content, max_chars=7000) if content else None
            })

        print(f"[Gemini Prep] Selected {len(selected_files)} files for {owner}/{repo}.")

        return {
            "repo": f"{owner}/{repo}",
            "selected_files": selected_files,
            "recent_commit_diffs": recent_commits[:8],
        }

    def analyze_with_gemini(
        self,
        evidence: Dict,
        candidate_context: Optional[Dict] = None,
        model: str = "gemini-2.5-flash-lite"
    ) -> dict:
        payload = {
            "repo": evidence.get("repo"),
            "candidate_context": candidate_context or {},
            "selected_files": evidence.get("selected_files", []),
            "recent_commit_diffs": evidence.get("recent_commit_diffs", []),
        }

        prompt = f"""
You are a deterministic Technical Audit Engine and senior technical recruiter.

Rules:
- Return valid JSON only
- No markdown, no extra text
- Use only the evidence provided
- Be strict, concise, and evidence-based
- Rate numeric categories on a scale of 1 to 10

Return this exact JSON schema:
{{
  "overall_score": 0,
  "project_complexity": {{"score": 0, "reasoning": ""}},
  "originality": {{"score": 0, "reasoning": ""}},
  "code_quality": {{"score": 0, "reasoning": ""}},
  "engineering_maturity": {{"score": 0, "reasoning": ""}},
  "skill_level": {{"score": 0, "reasoning": ""}},
  "claim_alignment": {{"score": 0, "reasoning": ""}},
  "strengths": [],
  "red_flags": [],
  "recruiter_summary": ""
}}

Evidence:
{json.dumps(payload, indent=2)}
""".strip()

        print(f"[Gemini] Sending analysis for {evidence.get('repo')}...")
        response = self.gemini_client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json"
            )
        )

        text = getattr(response, "text", None)
        if not text:
            try:
                text = response.candidates[0].content.parts[0].text
            except Exception:
                text = ""

        print(f"[Gemini] Completed analysis for {evidence.get('repo')}.")
        return safe_json_loads(text)

    def analyze_repo_from_url(
        self,
        repo_url: str,
        author: Optional[str] = None,
        candidate_context: Optional[Dict] = None,
        max_files: int = 10,
        model: str = "gemini-2.5-flash-lite"
    ) -> Dict:
        owner, repo = parse_repo_url(repo_url)

        repo_metadata = self.get_repo_metadata(owner, repo)
        languages = self.get_repo_languages(owner, repo)
        evidence = self.smart_select_repo_evidence(
            owner=owner,
            repo=repo,
            author=author,
            max_files=max_files,
        )

        payload_context = {
            **(candidate_context or {}),
            "repo_metadata": repo_metadata,
            "languages": languages,
        }

        gemini_analysis = self.analyze_with_gemini(
            evidence=evidence,
            candidate_context=payload_context,
            model=model,
        )

        return {
            "repo": f"{owner}/{repo}",
            "repo_metadata": repo_metadata,
            "languages": languages,
            "evidence": evidence,
            "gemini_analysis": gemini_analysis,
        }


# =========================
# Gemini result extraction
# =========================

def extract_gemini_claims(result: dict) -> dict:
    parsed = result.get("gemini_analysis", {}) if isinstance(result, dict) else {}
    return {
        "score": parsed.get("overall_score"),
        "summary": parsed.get("recruiter_summary"),
        "strengths": parsed.get("strengths", []),
        "red_flags": parsed.get("red_flags", []),
    }


# =========================
# Gemini only for requested projects
# Sequential only
# =========================

def add_gemini_to_projects_sequential(
    people: dict,
    github_token: Optional[str],
    gemini_api_key: str,
    projects: Optional[List[str]],
    model: str = "gemini-2.5-flash-lite"
) -> dict:
    username = people["top_level_signals"]["username"]
    candidate_context = {
        "top_level_signals": people.get("top_level_signals", {}),
        "context": people.get("context", {}),
    }
    commit_star = people.get("commit_star", {})
    project_check = commit_star.get("project_check", {})

    repo_names = []
    for project in projects or []:
        repo_data = project_check.get(project)
        if repo_data and repo_data.get("exists"):
            repo_names.append(project)

    if not repo_names:
        print("[Gemini] No requested projects found for Gemini analysis.")
        for project_name, repo_data in project_check.items():
            repo_data["gemini_claims"] = None
        return people

    print(f"[Gemini] Starting sequential analysis for requested projects: {len(repo_names)} repo(s)...")

    analyzer = RepoAnalyzer(
        github_token=github_token,
        gemini_api_key=gemini_api_key
    )

    analysis_map = {}
    total = len(repo_names)

    for idx, repo_name in enumerate(repo_names, start=1):
        repo_url = f"https://github.com/{username}/{repo_name}"
        print(f"[Gemini] {idx}/{total} -> {repo_url}")

        try:
            result = analyzer.analyze_repo_from_url(
                repo_url=repo_url,
                author=None,
                candidate_context=candidate_context,
                max_files=10,
                model=model,
            )
            analysis_map[repo_name] = extract_gemini_claims(result)

        except Exception as exc:
            print(f"[Gemini] Failed project -> {repo_name}: {exc}")
            analysis_map[repo_name] = {
                "score": None,
                "summary": None,
                "strengths": [],
                "red_flags": [str(exc)],
            }

    print("[Gemini] Sequential project analysis complete.")

    for project_name, repo_data in project_check.items():
        if repo_data.get("exists"):
            repo_data["gemini_claims"] = analysis_map.get(project_name)
        else:
            repo_data["gemini_claims"] = None

    return people


# =========================
# Final hire decision
# =========================


# =========================
# Full summary builder
# =========================

def build_full_github_summary(
    username: str,
   
    projects: Optional[List[str]] = None,
    github_token: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    repo_workers: int = 8,
    gemini_model: str = "gemini-2.5-flash-lite"
) -> dict:
    if not username:
        raise ValueError("username is required")
    if not gemini_api_key:
        raise ValueError("gemini_api_key is required")

    people = get_github_profile_summary(username=username, token=github_token)

    commit_star = get_repos_and_stars_threaded(
        username=username,
        token=github_token,
        max_workers=repo_workers,
        projects=projects or [],
    )
    people["commit_star"] = commit_star

    people = add_gemini_to_projects_sequential(
        people=people,
        github_token=github_token,
        gemini_api_key=gemini_api_key,
        projects=projects or [],
        model=gemini_model,
    )

   

    return people


# =========================
# Pretty printer
# =========================

def print_people_summary(people: dict):
    username = people["top_level_signals"]["username"]
    commit_star = people.get("commit_star", {})

    print("\n=== TOP LEVEL SIGNALS ===")
    for key, value in people.get("top_level_signals", {}).items():
        print(f"{key}: {value}")

    print("\n=== CONTEXT ===")
    for key, value in people.get("context", {}).items():
        print(f"{key}: {value}")

    print("\n=== COMMIT / STAR SUMMARY ===")
    print(f"username: {username}")
    print(f"total_repos: {commit_star.get('total_repos')}")
    print(f"total_stars: {commit_star.get('total_stars')}")
    print(f"total_commits: {commit_star.get('total_commits')}")

    print("\n=== TOP 3 COMMITTED REPOS ===")
    for repo in commit_star.get("top_3_committed_repos", []):
        repo_name = repo["repo_name"]
        repo_url = f"https://github.com/{username}/{repo_name}"
        print(f"- {repo_name} | commits={repo['commits']} | stars={repo['stars']}")
        print(f"  url: {repo_url}")

    print("\n=== TOP 3 STARRED REPOS ===")
    for repo in commit_star.get("top_3_starred_repos", []):
        repo_name = repo["repo_name"]
        repo_url = f"https://github.com/{username}/{repo_name}"
        print(f"- {repo_name} | stars={repo['stars']} | commits={repo['commits']}")
        print(f"  url: {repo_url}")

    print("\n=== PROJECT CHECK ===")
    for repo_name, repo_data in commit_star.get("project_check", {}).items():
        repo_url = f"https://github.com/{username}/{repo_name}"
        print(f"- {repo_name} | exists={repo_data['exists']} | stars={repo_data['stars']} | commits={repo_data['commits']}")
        print(f"  url: {repo_url}")
        claims = repo_data.get("gemini_claims")
        if claims:
            print(f"  gemini_score: {claims.get('score')}")
            print(f"  gemini_summary: {claims.get('summary')}")

    print("\n=== HIRE DECISION ===")
    print(json.dumps(people.get("hire_decision", {}), indent=2))


# =========================
# Main
# =========================

# if __name__ == "__main__":
#     username = "bdipesh3045"
#     projects = ["kindle-automation", "geospectral"]



#     summary = build_full_github_summary(
#         username=username,
       
#         projects=projects,
#         github_token=github_token,
#         gemini_api_key=gemini_api_key,
#         repo_workers=8,
#         gemini_model="gemini-2.5-flash-lite"
#     )

#     print(json.dumps(summary, indent=2))