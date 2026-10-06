# TrueHire project context

Standing handoff document: what exists, how it fits together, what is verified, and what is
still missing. Update this file at the end of each work phase so a new contributor (or a new
session) can pick up without re-reading the whole history. For the phase-by-phase audit trail of
decisions and their evidence, see [`engineering-audit.md`](engineering-audit.md).

- **Repository**: `Zeusangis/prometheus` (the product is TrueHire; the repo name is historical).
- **Status snapshot**: phases 0-9 complete and pushed. Head migration `c840ab218f12`.
- **Verified at this snapshot**: backend test suite passing (inventory in [Appendix A.6](#appendix-a--generated-inventory)),
  Ruff clean, frontend typecheck and production build passing, real-browser smoke of
  apply → analysis → profile → screening queue.

## 1. What the product is

Evidence-first technical recruiting. A recruiter creates a job with scoring configuration, shares
a public application link, and candidates apply with a PDF resume (optionally a GitHub username).
Background workers produce job-aware resume analysis and bounded public GitHub evidence. A
recruiter reviews the evidence in a screening queue and applicant profile and moves candidates
through a hiring pipeline by hand.

**Non-negotiable product rules** (enforced in code, not just wording):

- AI never hires, rejects, or moves a candidate. Stage transitions are human, server-authorized.
- Recruiting stage and analysis status are separate columns and separate vocabularies.
- Missing evidence stays `null` / "Not measured"; nothing is converted into a fabricated zero.
- Resume ATS scores and sampled repository scores are unrelated scales and are never combined
  into a single candidate score or ranking.
- Analysis failure never blocks or reverses a stage change, and a completed component is never
  silently overwritten by a retry.

## 2. Architecture

```text
React + TypeScript (Vite, TanStack Router/Query)
        │  relative /api requests, same-origin session cookie
        ▼
Flask modular monolith ── SQLAlchemy models ── SQLite (dev) / PostgreSQL (deployment)
        │
        ├── public apply endpoint (PDF validation + persistence)
        └── Celery task ── Redis broker ── resume + GitHub analysis services
                                              ├── Gemini (job-aware resume + repository review)
                                              └── GitHub REST (bounded, read-only)
```

Repository layout:

- `talent_intelligence_backend/` — Flask app, models, routes, services, Celery tasks, tests.
- `frontend_hackathon_1/` — React/TypeScript recruiter and applicant UI.
- `main1/` — retained prototype material. **Not** the application entry point and never imported
  by the app; it is an unsafe legacy Flask app (leaks a key at `/api/session`, crashes without a
  provider key, raw tracebacks). Do not expose it; keep it only until its useful ideas are migrated.
- `docs/` — this file plus the engineering audit.

## 3. Backend

### 3.1 App wiring

[`app.py`](../talent_intelligence_backend/app.py) exposes `create_app(config_overrides)` with
config from [`config/__init__.py`](../talent_intelligence_backend/config/__init__.py)
(`FLASK_ENV=development|test|production`; production refuses a weak `SECRET_KEY` or a missing
`DATABASE_URL`). It registers `auth`, `jobs`, `application`, `github` and `check_portfolio`
blueprints, CORS limited to `FRONTEND_ORIGIN`, unified JSON error handlers
([`utils/api_errors.py`](../talent_intelligence_backend/utils/api_errors.py)), the auth guard, CLI
commands and Celery. `/api/health` returns `{"status": "ok", "service": "TrueHire"}`.

### 3.2 Authentication and ownership

[`services/auth.py`](../talent_intelligence_backend/services/auth.py) installs a `before_request`
guard over every `/api/*` path except `/api/public/*`, `/api/health`, `/api/github/health`,
`/api/auth/{login,me,csrf}`, and the legacy apply alias.

- Users authenticate with salted `scrypt` password hashes (Werkzeug 3.1.8 default via
  `generate_password_hash` in [`models/auth.py`](../talent_intelligence_backend/models/auth.py),
  minimum 12 characters), sessions are server-side,
  cookies are `HttpOnly` + `SameSite=Lax` with an 8-hour lifetime, and logout revokes the session
  by bumping `session_version` (an old cookie stays dead).
- Mutations require the `X-CSRF-Token` header to match the token in the session.
- Every job and candidate read is scoped through `owned_jobs()`, `owned_job()` and
  `owned_candidate()`, which join on the recruiter's organization. Cross-organization access
  returns 404 (not 403) so existence is not disclosed.
- CLI: `flask --app app create-recruiter` and the operator-only `assign-legacy-job`.

### 3.3 API surface

The complete route table, including which endpoints the auth guard leaves public, is generated in
[Appendix A.1](#appendix-a--generated-inventory).

Behaviour worth knowing beyond the table:

- `/api/candidates/<id>/analysis` returns `{status, error_message, resume, github}`; each component
  carries its own status and error, and `github` is `null` when no GitHub username was supplied.
- `/api/candidates/<id>/analysis/retry` answers 202 when the retry was queued, 409 when analysis is
  already queued/running/complete, and 503 when the broker refused the task.
- Job creation requires title, job type and description; `/api/jobs/my-company` is an alias for the
  job list, and the legacy `/api/jobs/<int:id>/apply` path is kept as a public alias.

Screening queue query parameters: `stage`, `analysis_status`, `attention=1`
(failed / enqueue_failed / partial), `running=1` (queued / running), `job_id`, `q` (name or email,
case-insensitive). Results are newest-first and capped at 200 rows.

### 3.4 Data model

Column-level detail is generated in [Appendix A.2](#appendix-a--generated-inventory). What each
table is for:

- `users`, `organizations`, `organization_memberships` — recruiter identity and explicit
  organization ownership; there is no implicit legacy access.
- `jobs` — role, requirements, scraper and interview configuration, status, owning organization.
- `candidates` — applicant identity, stored resume file path, recruiting `status`, separate
  `analysis_status` and `analysis_error`, plus a legacy `ats_score` mirror of the resume component.
- `resume_analyses` — one row per candidate: status, `ats_score`, `breakdown`, missing keywords,
  weak areas, improvements, projects, verdict, model name, error message.
- `github_analyses` — one row per candidate: status, username, public repo / star / attributed
  commit counts (nullable when unknown), summary, error message.
- `repository_analyses` — sampled repositories with score, dimension scores and weights, score
  aggregation and weight coverage, strengths, red flags, recruiter summary and provenance; unique
  per (GitHub analysis, repository name).
- `meeting_summaries` — interview placeholder created when a candidate reaches
  `interview_scheduled`; replaced by the real interview model in a later phase.

Migration history is additive and never squashed; head is `c840ab218f12`. Fresh upgrades, schema
drift and legacy-data preservation are covered by
[`tests/test_migrations_and_config.py`](../talent_intelligence_backend/tests/test_migrations_and_config.py).
Never use `create_all` to fake a migration.

### 3.5 Status vocabularies

- Stages (`services/candidate_stage.py`): `screening` → `interview_scheduled` →
  `interview_completed` → `offer_made` → `hired`; `rejected` is reachable from every non-terminal
  stage; `hired` and `rejected` are terminal. `allowed_actions()` is the only source of truth for
  what the UI may offer.
- Analysis statuses: `queued`, `running`, `complete`, `partial`, `failed`, `enqueue_failed`.
  Overall candidate analysis is `complete` only when every component is complete, `partial` when
  some component has a result, otherwise `failed`.

### 3.6 Analysis pipeline

[`services/candidate_analysis.py`](../talent_intelligence_backend/services/candidate_analysis.py)
owns orchestration: `ensure_records`, `prepare_retry`, `overall_status` and `process_analysis`.

- Resume: `tasks/resume_tasks.py` extracts PDF text, then
  [`services/resume/analyzer.py`](../talent_intelligence_backend/services/resume/analyzer.py)
  prompts the provider with job context (resume text capped at 60,000 chars) and validates the
  JSON: finite bounded scores, breakdown that sums to `ats_score`, capped lists, unknown fields
  stripped. Category maxima: keyword match 25, skills 15, experience 20, education 10, formatting
  10, achievements 10, completeness 10.
- GitHub: [`services/github/client.py`](../talent_intelligence_backend/services/github/client.py)
  (fixed `https://api.github.com` origin, no redirects, bounded requests/time/response size, safe
  error mapping), [`collector.py`](../talent_intelligence_backend/services/github/collector.py)
  (owner-only public repos, candidate-attributed commits in a 90-day window, sampled source files
  with junk/sensitive paths excluded) and
  [`analyzer.py`](../talent_intelligence_backend/services/github/analyzer.py) (job-weighted
  dimensions, citations required for every non-null score, `weight_coverage` reported, unsupported
  metrics listed).
- Provider access is centralised in
  [`services/ai/gemini.py`](../talent_intelligence_backend/services/ai/gemini.py): lazy key read,
  SDK import inside the call, explicit timeout, JSON schema response mode. An empty key produces a
  stored, safe `failed` state rather than a crash or a fabricated score.
- Failure handling: a component failure clears its own stale outputs, keeps the other component's
  results, and leaves the recruiting stage untouched.
- Enqueue is separate from persistence: a broker failure records `enqueue_failed` and never loses
  the application.

### 3.7 Limits worth knowing

Resume upload: PDF only, 5 MiB file limit with 64 KiB multipart overhead, extension + mimetype +
`%PDF-` signature checks, stored once as `uuid4-secure_filename` (MIME checks are not malware
scanning). GitHub: 40 requests, 2 MiB responses, 90 s budget, 5 s per request, 2 repo pages of 100,
3 analyzed repositories, 30 commits, 3,000 tree entries, 3 files of 50 KB (4,000 characters kept),
90-day lookback. Screening queue: 200 rows. Raw repository code is never persisted — only scores,
summaries and short provenance excerpts.

## 4. Frontend

### 4.1 Routes (`src/main.tsx`)

| Path | Screen | Data |
| --- | --- | --- |
| `/login` | `LoginPage` | real session login |
| `/`, `/dashboard` | `pages/dashboard/Dashboard` → `components/Dashboard` | real KPIs, pipeline, roles, screening queue |
| `/dashboard/jobs` | `JobsPage` → `JobsList` | real jobs with applicant/stage/interviewing counts |
| `/dashboard/$jobId` | `JobDetail` | real job, per-stage pipeline cards, applicant list with ATS evidence, stage moves |
| `/profile/$candidateId` | `ProfilePage` | real candidate, tabs Overview / Resume / GitHub Evidence / Scores & Analysis |
| `/profile/$candidateId/interview-summary` | `InterviewSummaryPage` | **still mocked — do not link or trust** |
| `/candidate/$candidateId` | `CandidateDetail` | redirects to the real profile |
| `/apply/$jobId` | `pages/apply/ApplyPage` | real public application form |
| `/jobs/new` | `NewJob` | multi-step job wizard (job details, scraper config, interview setup, review) |

`SessionGate` in `src/main.tsx` calls `/api/auth/me` and redirects to `/login` when signed out;
`/apply/*` and `/login` are public.

### 4.2 API clients

- [`src/api/auth.ts`](../frontend_hackathon_1/src/api/auth.ts) — `authMe`, `login`, `logout`, and
  `recruiterFetch`, which attaches the in-memory CSRF token to every non-GET request with
  `credentials: "same-origin"`. All authenticated clients go through it.
- [`src/api/jobs.ts`](../frontend_hackathon_1/src/api/jobs.ts) — jobs, applicants, stage moves.
- [`src/api/screening.ts`](../frontend_hackathon_1/src/api/screening.ts) — screening queue with
  typed filters.
- [`src/api/apply.ts`](../frontend_hackathon_1/src/api/apply.ts) — public job/apply plus the
  candidate profile and typed analysis payloads (`getCandidateAnalysis`,
  `retryCandidateAnalysis`).
- [`src/api/errors.ts`](../frontend_hackathon_1/src/api/errors.ts) — `apiErrorMessage`, which only
  ever surfaces backend-provided safe messages.

No credentials or provider secrets are stored in the browser; sessions are same-origin cookies and
CSRF tokens stay in memory only.

### 4.3 UI conventions

Evidence components live in `src/pages/dashboard/`: [`ResumeSection.tsx`](../frontend_hackathon_1/src/pages/dashboard/ResumeSection.tsx)
exports the shared `formatLabel`, `formatDate` and `EvidenceList` helpers used by
[`GitHubSection.tsx`](../frontend_hackathon_1/src/pages/dashboard/GitHubSection.tsx). Dates from
SQLite arrive without a timezone suffix, so `formatDate` appends `Z` before parsing. Every screen
must render explicit loading, error, empty, `pending`, `failed` and `not-requested` states, and must
never invent a number for absent evidence.

## 5. Verification

```bash
# Backend
cd talent_intelligence_backend
venv/bin/python -m pytest -q          # inventory in Appendix A.6
venv/bin/python -m ruff check .       # clean
venv/bin/python -m flask --app app db check

# Frontend
cd frontend_hackathon_1
npm run typecheck
npm run build
```

The module-by-module test inventory is generated in
[Appendix A.6](#appendix-a--generated-inventory). Tests set `GEMINI_API_KEY=""` and
`GITHUB_TOKEN=""` and stub the GitHub transport, so the suite never calls a live provider. The
frontend has **no automated test runner** (typecheck + build + manual browser checks only).

`tests/test_project_context.py` regenerates the appendix below and fails when this document is
stale, so route, model, status, limit, frontend-route and test changes must be followed by
`python -m tools.generate_project_context`.

Browser verification pattern used in recent phases: boot the real Flask app on an isolated
migrated SQLite database from a throwaway harness outside the repository, replacing only
`GitHubClient.get` (canned HTTP) and the two Gemini `generate_json` entry points, then drive a Vite
dev server (proxying `/api` to that backend) with a real browser tab and assert on rendered text.
Because that harness lives in a temp directory, recreate it when needed.

Environment quirks on the original development machine: use `--noproxy '*'` (or an empty
`ProxyHandler`) for localhost HTTP; Vite binds `[::1]` so use `localhost`, not `127.0.0.1`, for dev
server URLs; the local Redis on 6379 may belong to another process — never flush it.

## 6. Configuration

Root `.env` (see [`.env.example`](../.env.example)): `FLASK_ENV`, `SECRET_KEY`, `DATABASE_URL`,
`CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `FRONTEND_ORIGIN`, `UPLOAD_FOLDER`,
`GEMINI_API_KEY`, `GEMINI_MODEL`, `GITHUB_TOKEN`, `NAVTALK_*` placeholders, `VITE_API_BASE_URL`.
Never expose provider credentials through `VITE_*` variables.

## 7. Deliberately not built yet

- **Interviews**: `/profile/$candidateId/interview-summary` still renders demo interview data, and
  live interviews are disabled (provider settings are placeholders). No secure session model has
  been designed; do not send long-lived provider keys to a browser.
- **Dashboard controls**: the queue API supports stage/analysis filters, search and job scoping, but
  the UI has no filter, search, pagination or CSV export yet, and it renders the 10 most recent of
  the queue.
- **Audit trail**: stage changes update a column only; there is no immutable record of who moved a
  candidate, when, or from which stage.
- **Concurrency**: no worker leases or dead-worker recovery, no enqueue outbox, no versioned
  analysis history. Only sequential redelivery is verified; concurrent double delivery is not.
- **Abuse/deployment hardening**: no auth or apply rate limiting, no object storage, retention or
  deletion policy, no malware scanning, no Compose/deployment configuration. SQLite is the verified
  database; PostgreSQL is untested (no Docker daemon available).
- **Verification gaps**: live Gemini and GitHub calls, PostgreSQL, a real Celery broker/Redis
  worker and hosted CI have never been exercised (the `gh` CLI is not installed).
- **Prototype residue**: `main1/` (unsafe, never imported) and the unused
  `models/github_ats.py` (`Summary` back-populates reference a table that no longer exists).
- **Multi-org UI**: users belong to one organization in the UI; there is no organization switcher.

## 8. Suggested next steps

1. Screening filters, search and pagination in the dashboard, using the existing query parameters.
2. An immutable audit trail for stage changes and analysis retries, surfaced on the profile.
3. Replace the mocked interview summary with persisted interview data and design a secure
   interview-session model before enabling live interviews.
4. Rate limiting (auth and apply), object storage for resumes, and retention/deletion policy.
5. Concurrency hardening: worker leases, dead-worker recovery, an enqueue outbox and versioned
   analysis results.
6. Delete or quarantine the prototype residue (`main1/`, `models/github_ats.py`) once its ideas are
   confirmed migrated.

## 9. Working conventions

- Keep migrations append-only and never rewrite applied ones; verify fresh upgrade, schema drift
  and legacy preservation whenever the schema changes.
- Never let provider output change a recruiting stage, and never let a failed component erase a
  successful one.
- Verify before claiming: run the checks above, exercise the delivered behavior through the
  interface the user will use, and report anything that could not be run as a limitation.
- Write commit subjects in the imperative with a short body explaining why; keep commit messages
  free of tool or bot attribution.
- Update this file and the audit when a phase lands; if the change touched routes, models,
  statuses, limits, frontend routes or tests, regenerate Appendix A with
  `cd talent_intelligence_backend && venv/bin/python -m tools.generate_project_context`.

## Appendix A — generated inventory

<!-- BEGIN GENERATED INVENTORY -->
Generated from the code by `python -m tools.generate_project_context` (backend working directory). Run it after changing routes, models, statuses, limits, frontend routes or tests; `tests/test_project_context.py` fails when this block is stale. Do not edit it by hand.

### A.1 API surface

| Path | Methods | Access | Endpoint |
| --- | --- | --- | --- |
| `/api/auth/csrf` | GET | public | `auth.csrf` |
| `/api/auth/login` | POST | public | `auth.login` |
| `/api/auth/logout` | POST | session + CSRF | `auth.logout` |
| `/api/auth/me` | GET | public | `auth.me` |
| `/api/candidates` | GET | session | `application.list_candidates` |
| `/api/candidates/<int:candidate_id>` | GET | session | `application.get_candidate` |
| `/api/candidates/<int:candidate_id>/analysis` | GET | session | `application.get_analysis` |
| `/api/candidates/<int:candidate_id>/analysis/retry` | POST | session + CSRF | `application.retry_analysis` |
| `/api/candidates/<int:candidate_id>/next-step` | POST | session + CSRF | `application.move_to_next_step` |
| `/api/candidates/<int:candidate_id>/stage` | POST | session + CSRF | `application.move_to_next_step` |
| `/api/check-portfolio` | POST | session + CSRF | `check_portfolio.check_portfolio_links` |
| `/api/github/health` | GET | public | `github.github_health` |
| `/api/health` | GET | public | `health` |
| `/api/jobs` | GET | session | `jobs.list_jobs` |
| `/api/jobs` | POST | session + CSRF | `jobs.create_job_route` |
| `/api/jobs/` | GET | session | `jobs.list_jobs` |
| `/api/jobs/<int:job_id>/apply` | POST | public | `application.apply_for_job` |
| `/api/jobs/<int:job_id>/candidates/<int:candidate_id>/next-step` | POST | session + CSRF | `application.move_to_next_step` |
| `/api/jobs/<job_id>` | GET | session | `jobs.get_job` |
| `/api/jobs/<job_id>` | PATCH, POST, PUT | session + CSRF | `jobs.update_job` |
| `/api/jobs/<job_id>/applicants` | GET | session | `jobs.get_job_applicants` |
| `/api/jobs/<job_id>/info` | GET | session | `jobs.get_job_info` |
| `/api/jobs/<job_id>/interview` | POST | session + CSRF | `jobs.update_job_interview` |
| `/api/jobs/<job_id>/scraper` | POST | session + CSRF | `jobs.update_job_scraper` |
| `/api/jobs/<job_id>/status` | POST | session + CSRF | `jobs.update_job_status` |
| `/api/jobs/<job_id>/update` | PATCH, POST, PUT | session + CSRF | `jobs.update_job` |
| `/api/jobs/create` | POST | session + CSRF | `jobs.create_job_route` |
| `/api/jobs/my-company` | GET | session | `jobs.get_my_company_jobs` |
| `/api/jobs/my-company/` | GET | session | `jobs.get_my_company_jobs` |
| `/api/public/jobs/<int:job_id>` | GET | public | `jobs.get_public_job` |
| `/api/public/jobs/<int:job_id>/apply` | POST | public | `application.apply_for_job` |

### A.2 Database tables

- `organizations`: `id` integer [pk]; `name` string(255) [not null]; `created_at` datetime [not null, default]
- `users`: `id` integer [pk]; `email` string(255) [not null]; `name` string(255) [not null]; `password_hash` string(500) [not null]; `active` boolean [not null, default]; `session_version` integer [not null, default]; `created_at` datetime [not null, default]. Unique: (email)
- `jobs`: `id` integer [pk]; `organization_id` integer [fk → organizations.id, not null]; `created_by_user_id` integer [fk → users.id]; `title` string(255) [not null]; `company` string(255) [not null]; `location` string(255); `description` text; `requirements` json; `scraper_config` json; `interview_config` json; `recruiter_data` json; `status` string(20) [not null, default]; `posted_date` datetime [default]
- `organization_memberships`: `id` integer [pk]; `user_id` integer [fk → users.id, not null]; `organization_id` integer [fk → organizations.id, not null]; `role` string(30) [not null, default]. Unique: (organization_id, user_id)
- `candidates`: `id` integer [pk]; `full_name` string(255); `email` string(255); `github_username` string(255); `original_filename` string(255) [not null]; `file_path` string(500) [not null]; `meeting_id` string(255); `job_id` integer [fk → jobs.id]; `raw_text` text; `ats_score` float; `status` string(50) [not null, default]; `analysis_status` string(50) [not null, default]; `analysis_error` text; `uploaded_at` datetime [default]. Unique: (file_path)
- `github_analyses`: `id` integer [pk]; `candidate_id` integer [fk → candidates.id, not null]; `status` string(20) [not null, default]; `username` string(255); `total_public_repos` integer; `total_stars` integer; `candidate_attributed_commits` integer; `summary` json; `error_message` text; `created_at` datetime [not null, default]; `updated_at` datetime [not null, default]. Unique: (candidate_id)
- `meeting_summaries`: `id` integer [pk]; `candidate_id` integer [fk → candidates.id, not null]; `job_id` integer [fk → jobs.id]; `meeting_id` string(255) [not null]; `created_at` datetime [default]. Unique: (meeting_id)
- `resume_analyses`: `id` integer [pk]; `candidate_id` integer [fk → candidates.id, not null]; `status` string(20) [not null, default]; `ats_score` float; `breakdown` json; `missing_keywords` json; `weak_areas` json; `top_improvements` json; `projects` json; `final_verdict` text; `model_name` string(100); `error_message` text; `created_at` datetime [not null, default]; `updated_at` datetime [not null, default]. Unique: (candidate_id)
- `repository_analyses`: `id` integer [pk]; `github_analysis_id` integer [fk → github_analyses.id, not null]; `repo_name` string(255) [not null]; `repo_url` string(500) [not null]; `primary_language` string(100); `pushed_at` datetime; `score` float; `metrics` json; `strengths` json; `red_flags` json; `recruiter_summary` text; `evidence_metadata` json; `created_at` datetime [not null, default]. Unique: (github_analysis_id, repo_name)

### A.3 Stage and analysis vocabularies

**Recruiting stages** (server-authoritative; the client offers only these):

- `screening` → `interview_scheduled`, `rejected`
- `interview_scheduled` → `interview_completed`, `rejected`
- `interview_completed` → `offer_made`, `rejected`
- `offer_made` → `hired`, `rejected`
- `hired` → terminal
- `rejected` → terminal

**Analysis statuses** (independent of recruiting stages): `queued`, `running`, `complete`, `partial`, `failed`, `enqueue_failed`. Retry is offered only for `failed`, `enqueue_failed`, `partial`.

### A.4 Configured limits

| Limit | Value | Enforced in |
| --- | --- | --- |
| Resume file size | 5 MiB | `routes/application_routes.py` |
| Request size | 5 MiB + 64 KiB multipart overhead | `config/__init__.py` |
| Screening queue rows | 200 | `routes/application_routes.py` |
| Resume text sent to provider | 60,000 characters | `services/resume/analyzer.py` |
| GitHub requests | 40 | `services/github/client.py` |
| GitHub response size | 2 MiB | `services/github/client.py` |
| GitHub total budget | 90 s | `services/github/client.py` |
| GitHub request timeout | 5 s | `services/github/client.py` |
| Repository pages | 2 x 100 | `services/github/collector.py` |
| Analyzed repositories | 3 | `services/github/collector.py` |
| Commits sampled per repository | 30 | `services/github/collector.py` |
| Tree entries read | 3,000 | `services/github/collector.py` |
| Files sampled per repository | 3 | `services/github/collector.py` |
| File size read | 50 KB | `services/github/collector.py` |
| File characters kept | 4,000 | `services/github/collector.py` |
| Commit lookback | 90 days | `services/github/collector.py` |
| Resume ATS categories | keyword_match 25, skills_alignment 15, experience_relevance 20, education 10, formatting 10, achievements 10, completeness 10 | `services/resume/analyzer.py` |

### A.5 Frontend routes

| Path | Component |
| --- | --- |
| `/apply/$jobId` | `ApplyPage` |
| `/candidate/$candidateId` | `CandidateDetail` |
| `/dashboard` | `Dashboard` |
| `/dashboard/$jobId` | `JobDetail` |
| `/dashboard/jobs` | `JobsPage` |
| `/jobs/new` | `NewJob` |
| `/login` | `LoginPage` |
| `/profile/$candidateId` | `ProfilePage` |
| `/profile/$candidateId/interview-summary` | `InterviewSummaryPage` |

### A.6 Test inventory

| Module | Test functions |
| --- | --- |
| `tests/test_analysis_readiness.py` | 7 |
| `tests/test_auth.py` | 3 |
| `tests/test_authorization.py` | 3 |
| `tests/test_bootstrap.py` | 2 |
| `tests/test_candidate_stage.py` | 4 |
| `tests/test_github_analysis.py` | 25 |
| `tests/test_jobs_api.py` | 6 |
| `tests/test_migrations_and_config.py` | 6 |
| `tests/test_project_context.py` | 2 |
| `tests/test_provider_errors.py` | 12 |
| `tests/test_public_applications.py` | 10 |
| `tests/test_resume_analyzer.py` | 6 |
| `tests/test_resume_pipeline.py` | 8 |
| `tests/test_screening_queue.py` | 12 |
| **total** | **106** (parametrized cases expand at run time) |

<!-- END GENERATED INVENTORY -->
