# TrueHire engineering audit

## Phase 0 baseline — 2026-10-05

Branch: `main`. Existing changes are owned by the user and must be preserved:

- `frontend_hackathon_1/package-lock.json`
- `frontend_hackathon_1/src/api/apply.ts` (candidate fetch helper)
- `frontend_hackathon_1/src/pages/dashboard/ProfilePage.tsx` (candidate query/name integration)
- `talent_intelligence_backend/routes/application_routes.py` (candidate GET endpoint)
- untracked `.freebuff/` metadata

No commits, staging, database resets, repository renames, or provider calls were performed.

### Baseline checks

| Check | Result |
| --- | --- |
| `npm ci --no-audit --no-fund` | PASS; existing npm lockfile preserved |
| `npm run build` | PASS; Vite warns about ESM config loaded as CommonJS |
| `./node_modules/.bin/tsc --noEmit --incremental false` | FAIL: unused `components/theme-provider.tsx` and `components/ui/sonner.tsx` import absent `next-themes`; `src/components/TimeTracker.tsx` uses a numeric browser timer type with Node timer overload |
| Backend import with temporary SQLite/memory Celery configuration | PASS using existing Python 3.14 virtualenv |
| Python source compile via builtin `compile()` | PASS: 28 files; no bytecode generated |
| Existing `/api/github/health` | PASS, HTTP 200; health only, not a GitHub integration |
| Target `/api/health` | FAIL, HTTP 404 |
| All existing Alembic upgrades on fresh temporary SQLite + schema check | PASS; head `f87109fe65cc`, no drift |
| Vite server HTTP `/` | PASS, HTTP 200 on 5173 |
| Docker daemon | UNAVAILABLE; CLI installed but daemon is not running |
| Browser panel | UNAVAILABLE: profile/tab initialization errors; no interactive UI smoke test claimed |

Environment: Node 22.23.2, npm 11.13.0. System Python is 3.9.6, existing backend virtualenv Python is 3.14.7. Redis is already listening on localhost:6379; it is not owned by this task and must not be stopped or flushed. No backend or frontend listeners existed initially.

### Important difference from supplied plan

**`main1/` is absent from both this checkout and HEAD's tracked root tree.** Its GitHub analyzer, Gemini prompts, WebRTC client, and transcript evaluator cannot currently be extracted or tested. Do not invent a replacement and claim migration, delete another checkout, or fetch unrelated branches silently. Obtain the prototype source/location before phases 6–9 and final prototype cleanup. NavTalk security support remains unverified; live sessions must remain disabled until its credential model is verified.

### Known defects and scope

The supplied remediation plan is the acceptance contract. Confirmed locally: invalid backend-origin application link, mixed recruiting/worker state, duplicate resume form keys, mismatched upload limits, unscoped unauthenticated recruiter APIs, wildcard CORS, raw exception responses, static recruiter identity, mock candidate/dashboard/interview content, competing config sources, two frontend lockfiles, tracked caches, and no tests/CI/Compose. ATS/GitHub/interview provider features are not implemented in the main backend.

Work in independently verified checkpoints, preserving the React wizard, Flask blueprints/factory, model payload mapper, migrations, UUID upload pattern, and Celery design. The initial checkpoint targets phases 1–3 only; it is **not** the definition of done for the full product.

## Acceptance criteria for initial checkpoint

- npm remains the only frontend package manager; generated artifacts are untracked/ignored.
- explicit development/test/production config; production cannot use a default secret.
- real directories and commands in README, safe root `.env.example`.
- job creation returns `publicApplicationPath: /apply/<numeric-id>`; share URL uses browser origin.
- public GET `/api/public/jobs/<id>` returns only public job data and rejects closed/draft jobs.
- public POST `/api/public/jobs/<id>/apply` and legacy apply alias persist exactly one validated PDF, at most 5 MiB.
- candidate stage is canonical and separate from analysis status; legacy values are migrated without resetting data.
- one backend transition service rejects illegal/terminal transitions; API returns allowed actions.
- persisted applications succeed even if broker enqueue fails; safe `enqueue_failed` state and explicit retry exist.
- parser worker never changes recruiting stage; extraction alone must not be presented as completed AI analysis.
- core tests and fresh/legacy migration tests require no provider credentials.
- CI runs backend lint/tests/migrations and frontend npm/typecheck/build.

## Subsequent required work

Authentication + organization ownership/CSRF must precede deployment; analysis/retry/stage endpoints in the initial checkpoint are still development-only. Persistent analyses and migrated providers, truthful candidate/interview/dashboard screens, secure interview sessions, privacy/rate limits/storage/audit, Compose, and final end-to-end scenario remain required. Do not treat a green initial CI checkpoint as product completion.
