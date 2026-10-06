# TrueHire

**Evidence-first technical recruiting.**

TrueHire helps recruiters evaluate technical candidates with job-specific resume analysis, bounded public GitHub evidence, and structured hiring workflows. AI provides supporting evidence for **human decisions**; it does not make automatic hiring or rejection decisions.

## Product workflow

```text
Create a job
    ↓
Candidate applies with a resume
    ↓
Resume and public GitHub analysis
    ↓
Structured candidate evidence
    ↓
Recruiter review
    ↓
Hiring pipeline
```

## Features

- Job creation with configurable languages, frameworks, criteria, and scoring weights
- Public candidate application links with PDF resume uploads and validation
- Job-aware, structured resume analysis using Gemini
- Bounded public GitHub and repository analysis with attributable evidence
- Weighted technical metrics with transparent score coverage and missing-evidence handling
- Independent resume and GitHub components with durable results, partial states, and retry support
- Candidate evidence profiles backed only by persisted results, with explicit pending, failed, partial and not-requested states
- Resume analysis keeps the exact text extracted from the PDF next to the saved scores, and records an actionable reason whenever analysis cannot run
- Server readiness reporting for resume analysis: a `/api/health` flag, an operator warning on the dashboard, and a `check-analysis` command that explains what is missing
- Bounded retry with backoff for transient provider failures, so a brief provider spike does not fail an otherwise valid analysis
- Asynchronous processing with Celery and Redis
- Recruiter authentication, CSRF protection, and organization-scoped data access
- Organization-scoped screening queue with stage and analysis filters, real ATS evidence, and server-authorized stage moves
- Dashboard queue controls: stage, analysis and grouping filters, debounced name/email search, per-role scoping, page-size selection with pagination, and CSV export of the rows on screen
- Recruiter dashboard built from stored applications: pipeline distribution, per-role applicant and interviewing counts, and an analysis-attention view
- Append-only audit trail of every stage change and analysis retry, with the acting recruiter and the stage or status that was replaced, shown on the applicant profile
- Database migrations, legacy-data ownership safeguards, automated tests, linting, and CI

## Technology stack

| Layer | Technologies |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS, TanStack Router, TanStack Query |
| Backend | Python, Flask, SQLAlchemy, Flask-Migrate/Alembic, PyPDF2 |
| Background processing | Celery and Redis |
| Analysis providers | Gemini API and GitHub REST API |
| Database | SQLite for local development; PostgreSQL-ready |

## Architecture

```text
React + TypeScript
        │ REST API
        ▼
      Flask
   ┌────┴────┐
   │         │
Database   Celery ── Redis
   │         │
   └───┬─────┘
       ├── Resume analysis
       └── GitHub analysis
```

## Repository structure

- `frontend_hackathon_1/` — React frontend and recruiter-facing screens
- `talent_intelligence_backend/` — Flask API, persistence, authentication, and background tasks
- `docs/` — engineering audit and verification notes

The repository is named `prometheus`; the product is TrueHire. The retained `main1/` directory contains prototype material and is not the application entry point.

## Prerequisites

- Node.js 22.12+ and npm
- Python 3.11+
- Redis
- SQLite for local development or PostgreSQL for deployment

## Local setup

Create the environment file first:

```bash
cp .env.example .env
```

### Backend

```bash
cd talent_intelligence_backend
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
flask --app app db upgrade
flask --app app create-recruiter \
  --email recruiter@example.invalid \
  --name "Your Name" \
  --organization "Your Organization"
flask --app app run --host=127.0.0.1 --port=5000
```

### Background worker

In a second terminal, using the same virtual environment:

```bash
cd talent_intelligence_backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend_hackathon_1
npm ci
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` to the backend at `http://127.0.0.1:5000`.

## Configuration

Configuration is loaded from the root `.env` file. The most relevant settings are:

- `SECRET_KEY` and `DATABASE_URL` — required for production
- `GEMINI_API_KEY` — required for server-side resume analysis; without it every applicant records a failed analysis state that names the missing key instead of failing silently. It is read from the root `.env` or `talent_intelligence_backend/.env`
- `GEMINI_MODEL` — optional; defaults to `gemini-flash-lite-latest`. If analysis reports that the model is not recognised, set this to a model the key can use and restart the worker. Free-tier keys allow only a small number of requests per day per model, and GitHub analysis spends one request per sampled repository
- `GITHUB_TOKEN` — optional read-only authentication for higher GitHub API limits
- `VITE_API_BASE_URL` — optional frontend API override for local development
- `FRONTEND_ORIGIN` — optional cross-origin restriction when explicitly required

Never commit secrets or expose provider credentials through `VITE_*` variables. Live interview-provider settings are placeholders and are not an implemented integration.

To check that resume analysis can actually run before applying a candidate:

```bash
cd talent_intelligence_backend
source venv/bin/activate
flask --app app check-analysis           # reports key presence, model, broker and worker advice
flask --app app check-analysis --live    # also performs one real provider call
```

This command never prints the key itself.

## Verification

Frontend:

```bash
cd frontend_hackathon_1
npm run typecheck
npm run build
```

Backend:

```bash
cd talent_intelligence_backend
source venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
ruff check .
flask --app app db check
```

GitHub Actions runs backend tests, linting, fresh migration checks, and frontend type-check/build validation. These checks use mocked provider evidence; they do not claim live Gemini or GitHub connectivity.

## Analysis and security boundaries

TrueHire is designed for bounded, reviewable evidence:

- Resume and GitHub analysis run independently and preserve successful component results when another component fails.
- GitHub evidence is limited by request count, time, repository count, file size, and sampled content; raw repository code is not persisted.
- Candidate-attributed commits are scoped to the analyzed repositories, default branches, and sampling window. They are not lifetime contribution counts or identity verification.
- Missing evidence remains `null` rather than being converted into an invented zero.
- Analysis failures are recorded and shown to the recruiter with a safe, actionable reason (missing or rejected credentials, an unavailable model, quota, or an unreachable provider). Raw provider payloads are never echoed back, and a generic failure never leaks provider internals. A partial GitHub analysis names the repositories whose evidence collection or AI review failed, so a recorded status always carries a reason that matches it.
- Transient provider failures are retried a bounded number of times with backoff. A failure that asks for a long wait, such as an exhausted daily free-tier quota, is not retried, so the system does not spend more of a small request budget to no effect.
- Recruiting stages are never advanced by provider output or analysis failures, and the client offers only the stage actions the server reports as allowed.
- The candidate profile renders only saved analysis: it never fabricates scores, skills, contact details or recommendations, and it keeps resume ATS evidence, sampled repository scores and recruiting stages separate.
- The dashboard and screening queue show only stored applicant records; counts, stages and scores come from the API, and missing analysis is shown as "Not measured" rather than a placeholder number. Screening queue results are always filtered by the recruiter's organization and by jobs that organization owns.
- Recruiter mutations require authenticated organization membership and CSRF protection. Sessions use HTTP-only, SameSite cookies.
- Stage changes and analysis retries are recorded in an append-only audit trail that names the acting recruiter and what changed. Recorded events cannot be edited or deleted, they are visible only to the organization that owns the candidate, and failing to record one never blocks the change itself.
- Local file uploads are intended for development. Production requires controlled object storage, retention/deletion policies, access control, rate limiting, and provider verification.

Do not use the application with real candidate data until the remaining production privacy, storage, concurrency, and provider-validation work is complete.

## Project status

Implemented: job management, public applications, recruiter authentication with organization scoping and CSRF, persistence and migrations, background processing, provider error classification and readiness reporting, job-aware resume analysis that persists the extracted PDF text, bounded GitHub evidence, the persisted candidate evidence profile, the screening queue with server-side filters, search, pagination and CSV export, the append-only stage and retry audit trail, the recruiter dashboard, and CI.

Not yet implemented: the interview-summary screen and a secure live AI interview workflow, rate limiting, production object storage and retention controls, and worker leases or an outbox for delivery guarantees. There is no frontend test runner, and hosted CI cannot be exercised from every environment. Concrete provider limits also apply in practice: a free-tier Gemini key allows only a small number of requests per day per model, and one applicant's GitHub analysis spends one request per sampled repository, so a small key can exhaust its daily budget and leave analysis genuinely partial until the window resets. The `docs/project-context.md` known-gaps and next-steps sections are test-protected too: each claim carries a marker whose registered check fails as soon as the code contradicts it, so implementing one of those features forces the document to be updated in the same change.

For a standing overview of what is built, how it fits together and what is still missing, see [`docs/project-context.md`](docs/project-context.md). For the phase-by-phase audit trail with verification evidence, see [`docs/engineering-audit.md`](docs/engineering-audit.md).
