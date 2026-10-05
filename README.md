# TrueHire

TrueHire is a technical recruiting application under remediation from a hackathon prototype. AI is intended to provide evidence for **human recruiter decisions**, never automatic hiring or rejection.

## Current feature status

- Implemented core: React job wizard, Flask job persistence/list/update, PDF application storage, Celery PDF extraction, applicant listing.
- Being stabilized: public job/application flow, separate recruiting/processing states, recoverable enqueue failures, regression coverage.
- **Not production-ready:** recruiter authentication, organization authorization, persisted ATS/GitHub AI analysis, real candidate/dashboard/interview screens, secure interview sessions and evaluation are still required. Existing demo screens are not evidence of functioning integrations.
- `main1/`, referenced in the remediation plan, is absent from this checkout. Prototype migration requires obtaining those sources first.

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

Backend test/lint/CI commands and Compose orchestration will be documented when delivered, not before they exist. Database changes always use `flask --app app db upgrade`; do not delete existing databases or use `db.create_all()` to bypass migration history.

## Security and deployment boundaries

Do not deploy this checkpoint with real candidate data: recruiter APIs are still unauthenticated/unscoped. Static recruiter identity and demo UI remain pending replacement. Restricted CORS alone is not authorization. Uploads use local storage for development; production needs controlled object storage, retention/deletion policy, and access control. PDF type checks are not malware scanning. AI scores must remain decision support.

No license decision, repository metadata update, remote push, or deployment is included in remediation without an explicit request.
