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
- Asynchronous processing with Celery and Redis
- Recruiter authentication, CSRF protection, and organization-scoped data access
- Organization-scoped screening queue with stage and analysis filters, real ATS evidence, and server-authorized stage moves
- Recruiter dashboard built from stored applications: pipeline distribution, per-role applicant and interviewing counts, and an analysis-attention view
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
- `GEMINI_API_KEY` and optional `GEMINI_MODEL` — enable server-side resume analysis
- `GITHUB_TOKEN` — optional read-only authentication for higher GitHub API limits
- `VITE_API_BASE_URL` — optional frontend API override for local development
- `FRONTEND_ORIGIN` — optional cross-origin restriction when explicitly required

Never commit secrets or expose provider credentials through `VITE_*` variables. Live interview-provider settings are placeholders and are not an implemented integration.

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
- Recruiting stages are never advanced by provider output or analysis failures, and the client offers only the stage actions the server reports as allowed.
- The candidate profile renders only saved analysis: it never fabricates scores, skills, contact details or recommendations, and it keeps resume ATS evidence, sampled repository scores and recruiting stages separate.
- The dashboard and screening queue show only stored applicant records; counts, stages and scores come from the API, and missing analysis is shown as "Not measured" rather than a placeholder number. Screening queue results are always filtered by the recruiter's organization and by jobs that organization owns.
- Recruiter mutations require authenticated organization membership and CSRF protection. Sessions use HTTP-only, SameSite cookies.
- Local file uploads are intended for development. Production requires controlled object storage, retention/deletion policies, access control, rate limiting, and provider verification.

Do not use the application with real candidate data until the remaining production privacy, storage, concurrency, and provider-validation work is complete.

## Project status

Core job management, applications, authentication, persistence, background processing, resume analysis, GitHub analysis, candidate pipelines, the persisted candidate evidence profile, the screening queue and the recruiter dashboard, and CI are implemented. Dashboard filtering/pagination, the interview-summary screen and a secure live AI interview workflow remain under development.

For implementation details and known limitations, see [`docs/engineering-audit.md`](docs/engineering-audit.md).
