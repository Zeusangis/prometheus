# TrueHire

TrueHire is a technical recruiting application under remediation from a hackathon prototype. AI is intended to provide evidence for **human recruiter decisions**, never automatic hiring or rejection.

## Current feature status

- Implemented core: React job wizard, Flask job persistence/list/update, PDF application storage, Celery PDF extraction, applicant listing.
- Stabilized core: actual public job/application links, 5 MB PDF validation, separate recruiting/analysis states, recoverable enqueue failures, recruiter cookie authentication, organization-scoped reads/writes, and CSRF protection.
- **Not production-ready:** persisted ATS/GitHub AI analysis, truthful candidate/dashboard/interview screens, secure interview sessions/evaluation, rate limiting and production storage are still required. Existing demo screens are not evidence of functioning integrations.
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

Provider settings (`GEMINI_API_KEY`, `GITHUB_TOKEN`, `NAVTALK_API_KEY`, `NAVTALK_NAME`, `NAVTALK_AVATAR_ID`) are **server-only placeholders**, not proof that an integration exists. Never put secrets in any `VITE_*` variable or send long-lived keys to browser JavaScript. Live interviews must stay disabled until a secure provider-supported credential model is verified.

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

## Security and deployment boundaries

Recruiter APIs require an active hashed-password account, an organization membership, and a CSRF header for mutations. Sessions use HTTP-only SameSite cookies (Secure in production), expire after eight hours, and are revoked on logout. Credentials are never stored in localStorage; CSRF values stay in memory. Use same-origin deployment; separate-origin browser login is intentionally unsupported. Static recruiter JSON has been removed. Do not deploy with real candidate data until the remaining privacy/rate-limit/provider/storage work is complete. Uploads use local storage for development; production needs controlled object storage, retention/deletion policy, and access control. PDF type checks are not malware scanning. AI scores must remain decision support.

No license decision, repository metadata update, remote push, or deployment is included in remediation without an explicit request.
