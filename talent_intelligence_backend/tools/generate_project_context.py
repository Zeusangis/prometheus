"""Regenerate the factual inventory block of docs/project-context.md from the code.

Only the region between the generated markers is rewritten, so the narrative stays
hand-written. Everything emitted here is read from the application itself:

- Flask route table (path, methods, auth requirement, endpoint) from ``app.url_map``
- database tables and columns from ``db.metadata``
- recruiting stage and analysis status vocabularies from ``services.candidate_stage``
- configured limits from the modules that enforce them
- frontend routes parsed from ``frontend_hackathon_1/src/main.tsx``
- test function inventory parsed from ``tests/``

Run it after any change that touches those surfaces:

    cd talent_intelligence_backend
    venv/bin/python -m tools.generate_project_context

``tests/test_project_context.py`` fails when the committed document is stale.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "talent_intelligence_backend"
DOCUMENT = REPO_ROOT / "docs" / "project-context.md"
FRONTEND_MAIN = REPO_ROOT / "frontend_hackathon_1" / "src" / "main.tsx"
TESTS_DIR = BACKEND_ROOT / "tests"

BEGIN_MARKER = "<!-- BEGIN GENERATED INVENTORY -->"
END_MARKER = "<!-- END GENERATED INVENTORY -->"

INTRO = (
    "Generated from the code by `python -m tools.generate_project_context` "
    "(backend working directory). Run it after changing routes, models, statuses, "
    "limits, frontend routes or tests; `tests/test_project_context.py` fails when this "
    "block is stale. Do not edit it by hand."
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_app():
    """Create an isolated app instance used only for introspection."""
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))
    from app import create_app

    return create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "UPLOAD_FOLDER": tempfile.mkdtemp(prefix="truehire-doc-gen-"),
        "CELERY": {"broker_url": "memory://", "result_backend": "cache+memory://"},
    })


def routes_section(app) -> list:
    from services.auth import AUTH_EXEMPT_ENDPOINTS, is_exempt_path

    rows = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        methods = sorted(rule.methods - {"HEAD", "OPTIONS"})
        if not methods:
            continue
        path = str(rule)
        public = path in {"/api/health"} or is_exempt_path(path) or rule.endpoint in AUTH_EXEMPT_ENDPOINTS
        access = "public" if public else "session"
        if not public:
            access = "session" if methods == ["GET"] else "session + CSRF"
        rows.append((path, ", ".join(methods), access, rule.endpoint))
    rows.sort(key=lambda row: (row[0], row[1]))
    table = ["| Path | Methods | Access | Endpoint |", "| --- | --- | --- | --- |"]
    table += [f"| `{path}` | {methods} | {access} | `{endpoint}` |" for path, methods, access, endpoint in rows]
    return table


def tables_section() -> list:
    from models import db

    lines = []
    for table in db.metadata.sorted_tables:
        columns = []
        for column in table.columns:
            kind = "text" if column.type.__class__.__name__ == "Text" else column.type.__class__.__name__.lower()
            if column.type.__class__.__name__ == "String" and column.type.length:
                kind = f"string({column.type.length})"
            flags = []
            if column.primary_key:
                flags.append("pk")
            if column.foreign_keys:
                targets = ", ".join(sorted({fk.target_fullname for fk in column.foreign_keys}))
                flags.append(f"fk → {targets}")
            if not column.nullable and not column.primary_key:
                flags.append("not null")
            if column.default is not None or column.server_default is not None:
                flags.append("default")
            suffix = f" [{', '.join(flags)}]" if flags else ""
            columns.append(f"`{column.name}` {kind}{suffix}")
        unique = sorted(
            ", ".join(sorted(constraint.columns.keys()))
            for constraint in table.constraints
            if constraint.__class__.__name__ == "UniqueConstraint"
        )
        line = f"- `{table.name}`: " + "; ".join(columns)
        if unique:
            line += f". Unique: {'; '.join('(' + item + ')' for item in unique)}"
        lines.append(line)
    return lines


def vocabulary_section() -> list:
    from services.candidate_stage import (
        ANALYSIS_STATUSES, RETRYABLE_ANALYSIS, STAGES, TRANSITIONS,
    )

    lines = ["**Recruiting stages** (server-authoritative; the client offers only these):", ""]
    for stage in STAGES:
        targets = ", ".join(f"`{target}`" for target in TRANSITIONS[stage]) or "terminal"
        lines.append(f"- `{stage}` → {targets}")
    lines += [
        "",
        "**Analysis statuses** (independent of recruiting stages): "
        + ", ".join(f"`{status}`" for status in ANALYSIS_STATUSES)
        + ". Retry is offered only for "
        + ", ".join(f"`{status}`" for status in RETRYABLE_ANALYSIS)
        + ".",
    ]
    return lines


def limits_section() -> list:
    from config import DevelopmentConfig
    from routes.application_routes import MAX_QUEUE_RESULTS, MAX_RESUME_BYTES
    from services.ai.gemini import (
        DEFAULT_MODEL, RETRY_ATTEMPTS, RETRY_BASE_SECONDS, RETRY_MAX_SERVER_DELAY, RETRY_MAX_SECONDS,
    )
    from services.github import client as github_client
    from services.github import collector
    from services.resume.analyzer import CATEGORY_LIMITS, MAX_RESUME_CHARS

    mib = 1024 * 1024
    rows = [
        ("Resume file size", f"{MAX_RESUME_BYTES // mib} MiB", "routes/application_routes.py"),
        ("Request size", f"{MAX_RESUME_BYTES // mib} MiB + {(DevelopmentConfig.MAX_CONTENT_LENGTH - MAX_RESUME_BYTES) // 1024} KiB multipart overhead", "config/__init__.py"),
        ("Screening queue rows", str(MAX_QUEUE_RESULTS), "routes/application_routes.py"),
        ("Resume text sent to provider", f"{MAX_RESUME_CHARS:,} characters", "services/resume/analyzer.py"),
        ("Provider model (default)", DEFAULT_MODEL, "services/ai/gemini.py"),
        ("Provider retry attempts", str(RETRY_ATTEMPTS), "services/ai/gemini.py"),
        ("Provider retry backoff", f"{RETRY_BASE_SECONDS} s base, doubling, capped at {RETRY_MAX_SECONDS} s", "services/ai/gemini.py"),
        ("Provider retry wait ceiling", f"{RETRY_MAX_SERVER_DELAY} s; a longer requested wait is not retried", "services/ai/gemini.py"),
        ("GitHub requests", str(github_client.MAX_REQUESTS), "services/github/client.py"),
        ("GitHub response size", f"{github_client.MAX_RESPONSE_BYTES // mib} MiB", "services/github/client.py"),
        ("GitHub total budget", f"{github_client.BUDGET_SECONDS} s", "services/github/client.py"),
        ("GitHub request timeout", f"{github_client.REQUEST_TIMEOUT} s", "services/github/client.py"),
        ("Repository pages", f"{collector.MAX_REPO_PAGES} x {collector.REPOS_PER_PAGE}", "services/github/collector.py"),
        ("Analyzed repositories", str(collector.MAX_ANALYZED_REPOS), "services/github/collector.py"),
        ("Commits sampled per repository", str(collector.MAX_COMMITS), "services/github/collector.py"),
        ("Tree entries read", f"{collector.MAX_TREE_ENTRIES:,}", "services/github/collector.py"),
        ("Files sampled per repository", str(collector.MAX_FILES), "services/github/collector.py"),
        ("File size read", f"{collector.MAX_FILE_BYTES // 1000} KB", "services/github/collector.py"),
        ("File characters kept", f"{collector.MAX_FILE_CHARS:,}", "services/github/collector.py"),
        ("Commit lookback", f"{collector.LOOKBACK_DAYS} days", "services/github/collector.py"),
        ("Resume ATS categories", ", ".join(f"{key} {value}" for key, value in CATEGORY_LIMITS.items()), "services/resume/analyzer.py"),
    ]
    table = ["| Limit | Value | Enforced in |", "| --- | --- | --- |"]
    table += [f"| {name} | {value} | `{source}` |" for name, value, source in rows]
    return table


def frontend_routes_section() -> list:
    text = read(FRONTEND_MAIN)
    rows = []
    for block in re.findall(r"createRoute\(\{(.*?)\n\}\);", text, re.S):
        path = re.search(r'path:\s*"([^"]*)"', block)
        component = re.search(r"component:\s*(\w+)", block)
        if path and component:
            rows.append((path.group(1), component.group(1)))
    rows.sort(key=lambda row: row[0])
    table = ["| Path | Component |", "| --- | --- |"]
    table += [f"| `{path}` | `{component}` |" for path, component in rows]
    return table


def tests_section() -> list:
    rows = []
    total = 0
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        count = len(re.findall(r"^def test_", read(path), re.M))
        rows.append((path.name, count))
        total += count
    table = ["| Module | Test functions |", "| --- | --- |"]
    table += [f"| `tests/{name}` | {count} |" for name, count in rows]
    table.append(f"| **total** | **{total}** (parametrized cases expand at run time) |")
    return table


def build_block(app) -> str:
    sections = [
        INTRO,
        "",
        "### A.1 API surface",
        "",
        *routes_section(app),
        "",
        "### A.2 Database tables",
        "",
        *tables_section(),
        "",
        "### A.3 Stage and analysis vocabularies",
        "",
        *vocabulary_section(),
        "",
        "### A.4 Configured limits",
        "",
        *limits_section(),
        "",
        "### A.5 Frontend routes",
        "",
        *frontend_routes_section(),
        "",
        "### A.6 Test inventory",
        "",
        *tests_section(),
    ]
    return "\n".join(sections).rstrip() + "\n"


def render(document_text: str, block: str) -> str:
    if BEGIN_MARKER not in document_text or END_MARKER not in document_text:
        raise SystemExit(f"Markers {BEGIN_MARKER} / {END_MARKER} are missing from {DOCUMENT}")
    pattern = re.compile(
        re.escape(BEGIN_MARKER) + r".*?" + re.escape(END_MARKER), re.S
    )
    replacement = f"{BEGIN_MARKER}\n{block}\n{END_MARKER}"
    return pattern.sub(lambda _: replacement, document_text, count=1)


def main() -> int:
    app = build_app()
    with app.app_context():
        block = build_block(app)
    updated = render(read(DOCUMENT), block)
    if updated == read(DOCUMENT):
        print("docs/project-context.md is already up to date.")
        return 0
    DOCUMENT.write_text(updated, encoding="utf-8")
    print("Updated the generated inventory in docs/project-context.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
