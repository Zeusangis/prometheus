# TrueHire

TrueHire is a technical recruiting application under remediation from a hackathon prototype. AI is intended to provide evidence for **human recruiter decisions**, never automatic hiring or rejection.

## Current feature status

- Implemented core: React job wizard, Flask job persistence/list/update, PDF application storage, applicant listing, Celery extraction and job-aware structured Gemini resume analysis, durable component records, bounded public GitHub evidence/weighted repository review, and scoped analysis/retry APIs.
- Stabilized core: actual public job/application links, 5 MB PDF validation, separate recruiting/analysis states, recoverable enqueue failures, recruiter cookie authentication, organization-scoped reads/writes, and CSRF protection.
- **Not production-ready:** live provider verification, broader GitHub contribution evidence, truthful candidate/dashboard/interview screens, secure interview sessions/evaluation, concurrent-worker recovery, rate limiting and production storage are still required. Live Gemini calls have not been verified. Existing demo screens are not evidence of functioning integrations.
- `main1/` is retained prototype source, now merged from upstream. Do not run its legacy Flask app or expose it publicly; its secret-returning interview implementation is not integrated into the main app.

See [the engineering audit](docs/engineering-audit.md) for baseline failures and checkpoint status.

## Architecture and folders

```text
React + Vite + TanStack Router/Query
                  | /api
        Flask modular application
          | SQLAlchemy/Alembic
          | Celery -> Redis -> worker
```

- `frontend_hackathon_1/`: React 19, Vite, TypeScript, Tailwind, TanStack.
- `talent_intelligence_backend/`: Flask, SQLAlchemy, Flask-Migrate/Alembic, Celery, PyPDF2.
- `docs/`: engineering audit and verification notes.

The repository name may remain `prometheus`; the product is TrueHire. No directory renames are necessary.

## Prerequisites

- Node.js **22.12+** and npm (one lockfile; do not use pnpm).
- Python **3.11+** (3.14 also tested locally).
- Redis for asynchronous processing.
- SQLite for lightweight local development; PostgreSQL recommended for deployment.

## Environment

```bash
cp .env.example .env
# Edit .env locally; never commit it.
```

Configuration reads the root `.env`. The existing backend-local `.env` is supported for compatibility, with explicit process/root values taking precedence. Use `FLASK_ENV=development`, `test`, or `production`. Production requires an explicit `SECRET_KEY` of at least 32 characters and `DATABASE_URL`; it cannot silently use a development secret.

`GEMINI_API_KEY` enables the server-side resume integration; `GEMINI_MODEL` defaults to `gemini-2.5-flash`. The key is loaded only for worker analysis, so missing configuration does not prevent application boot. `GITHUB_TOKEN` optionally authenticates bounded public GitHub collection for higher rate limits; use a read-only token and never grant unnecessary private-repository access. The collector excludes private repositories. `NAVTALK_API_KEY`, `NAVTALK_NAME`, and `NAVTALK_AVATAR_ID` remain **server-only placeholders**, not proof that interview integration exists. Never put secrets in any `VITE_*` variable or send long-lived keys to browser JavaScript. Live interviews must stay disabled until a secure provider-supported credential model is verified.

## Local setup

Backend terminal:

```bash
cd talent_intelligence_backend
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
flask --app app db upgrade
flask --app app create-recruiter --email recruiter@example.invalid --name "Your Name" --organization "Your Organization"
# Enter a unique password (at least 12 characters) when prompted.
flask --app app run --host=127.0.0.1 --port=5000
```

Worker terminal (same virtualenv/environment):

```bash
cd talent_intelligence_backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info
```

Frontend terminal:

```bash
cd frontend_hackathon_1
npm ci
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to `http://127.0.0.1:5000`; production should route frontend and API through the same origin. Optional `VITE_API_BASE_URL` overrides belong in `frontend_hackathon_1/.env.local`. `FRONTEND_ORIGIN` restricts cross-origin access when explicitly needed. `/api/health` checks application boot, not provider connectivity.

## Verification

```bash
cd frontend_hackathon_1
npm run typecheck
npm run build
```

```bash
cd talent_intelligence_backend
source venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
ruff check .
flask --app app db check
```

GitHub Actions runs backend tests/lint/fresh migrations and frontend install/typecheck/build without provider keys. Hosted CI results must be checked separately; local passes are not a hosted-CI claim. Compose orchestration is still pending. Database changes always use `flask --app app db upgrade`; do not delete existing databases or use `db.create_all()` to bypass migration history.

### Existing data ownership

Migration `b730cce208a1` preserves old jobs/applicants under an **Unclaimed legacy data** organization with no memberships. No recruiter automatically receives access based on old JSON or company names. A trusted local operator must explicitly assign each legacy job after checking ownership:

```bash
flask --app app assign-legacy-job --job-id 123 --organization-id 2
# Review and confirm the prompt. Do not assign data you do not own.
```

New jobs always belong to the signed-in organization. The old `my-company` route remains a scoped compatibility alias, not a static recruiter lookup.

## Analysis behavior

The registered Celery resume task extracts PDF text, includes the linked job's title/description/languages/frameworks/recruiter instructions, and validates structured provider output before persisting it. Scores must be finite, bounded by their category maxima, and equal the breakdown sum. Prompts treat applicant/job text as untrusted evidence and prohibit automatic hiring decisions. Resume input is capped at 60,000 characters and provider calls have a 60-second timeout.

Authenticated `GET /api/candidates/<id>/analysis` returns `{status, error_message, resume, github}` scoped to the recruiter's organization. Component outputs are null until actually measured. Optional GitHub absence is `github: null`. Resume and GitHub components run independently: complete only when both requested components finish, partial when useful component evidence exists but some work fails, and failed when neither component succeeds. Extraction without successful provider output is not completed AI analysis. Missing keys, parsing errors and invalid/provider failures are saved safely and never move recruiting stages.

`POST /api/candidates/<id>/analysis/retry` accepts failed/enqueue_failed/partial candidates, requires CSRF, and preserves completed components. Sequential task redelivery does not repeat successful provider calls or duplicate rows. Concurrent deliveries, worker-kill leases/recovery, a transactional enqueue outbox and versioned analysis history are not yet implemented; late acknowledgment alone does not prove exactly-once execution.

Migration `c840ab218f12` adds resume/GitHub/repository analysis tables and backfills existing candidates with **pending, empty** component records without inventing historical scores or changing their original data. Downgrading this migration removes its component tables/results; candidate/job data remains intact.

### GitHub evidence and score scope

The collector adapts the useful `main1` REST/file-selection/evidence-review approach without importing its unsafe application. It uses a fixed HTTPS API origin, blocks redirects, has a 5-second request timeout and 90-second collection budget, caps requests at 40 and response bodies at 2 MiB, and fetches at most two 100-repository pages. Up to three recent repositories (originals preferred) receive analysis, with up to 30 candidate-author-filtered commits from the last 90 days and three text-file excerpts of 4,000 characters each. Trees are limited to 3,000 processed entries; large, generated, symlink and common sensitive filenames are excluded. Sample/truncation flags, commit URLs, file paths and SHAs are persisted; raw repository code is not persisted.

Profile public-repository count is distinct from listed/analyzed counts. Aggregate stars are null if the repository listing is incomplete; sample stars are labeled separately. Candidate-attributed commit counts deduplicate SHA across analyzed repositories, verify GitHub author login (not committer/name/email), and explicitly describe their default-branch/window/sample scope. They are **not lifetime commits** or identity verification. Fork/repository code is never asserted to be authored by the candidate.

Job metric toggles and relative weights control repository scoring. Language match is based on language bytes; consistency is active ISO weeks in the attributed sample. Code quality/security/complexity/test evidence use schema-validated Gemini output with exact sampled-path citations. Missing evidence is null, not a fabricated zero. Weighted scores normalize over available enabled weights and report weight coverage; a sample mean is not a complete candidate ranking. PR/issues/reviews (`openSource`) are not collected yet and remain unscored. Test evidence is not execution coverage; security review is not a guarantee. Provider failures preserve measured GitHub evidence as partial, independent of resume results.

Tests and the HTTP smoke use mocked GitHub/Gemini evidence; no live analysis/provider connectivity or performance speedup is claimed. The synchronous collector intentionally favors bounded work over the prototype's unbounded pagination/threading. More complete contribution sampling, caching and cost controls remain future work.

## Security and deployment boundaries

Recruiter APIs require an active hashed-password account, an organization membership, and a CSRF header for mutations. Sessions use HTTP-only SameSite cookies (Secure in production), expire after eight hours, and are revoked on logout. Credentials are never stored in localStorage; CSRF values stay in memory. Use same-origin deployment; separate-origin browser login is intentionally unsupported. Static recruiter JSON has been removed. Do not deploy with real candidate data until the remaining privacy/rate-limit/provider/storage work is complete. Uploads use local storage for development; production needs controlled object storage, retention/deletion policy, and access control. PDF type checks are not malware scanning. AI scores must remain decision support.

No license decision, repository metadata update, remote push, or deployment is included in remediation without an explicit request.
