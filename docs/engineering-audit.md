# TrueHire engineering audit

## Phase 0 baseline — 2026-10-05

Branch: `main`. Existing changes are owned by the user and must be preserved:

- `frontend_hackathon_1/package-lock.json`
- `frontend_hackathon_1/src/api/apply.ts` (candidate fetch helper)
- `frontend_hackathon_1/src/pages/dashboard/ProfilePage.tsx` (candidate query/name integration)
- `talent_intelligence_backend/routes/application_routes.py` (candidate GET endpoint)
- untracked `.freebuff/` metadata

During the Phase 0 baseline, no commits, staging, database resets, repository renames, or provider calls were performed. The user subsequently authorized periodic commits/pushes and inclusion of the related pre-existing edits.

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

## Verified phases 1–3 checkpoint

- Configuration/build baseline committed as `4a3f647`; initial push rejected because remote main contained a newer commit. No force push was attempted.
- Remote commit `19eeec9` adds only `main1/`; the shared checkout merged it as `578c6fd` after workflow `2409e1d` and layout `a1bc7ea` checkpoints. Remote main was verified at `578c6fd`; no force push or duplicate commits were made. The prototype-source blocker is resolved.
- 67 pytest cases pass without provider credentials, including the full transition matrix, upload bounds/signature checks, broker failure/retry, parser failure recovery, fresh schema drift, and legacy migration downgrade/reupgrade.
- Ruff, `npm ci`, frontend typecheck/build, and fresh-database migration upgrade/check pass.
- Browser profile initialization was resolved by using the default profile. The job wizard generated the correct `/apply/1` link; the incognito application page loaded the real job; browser submission returned success during a real broker outage. That browser upload used a PDF-signature fixture, not a parseable resume. Separately, an actual valid blank PDF was submitted over HTTP through the Vite proxy and persisted with `enqueue_failed` during the real outage.
- Browser recruiter stage confirmation successfully moved screening -> interview_scheduled, and pipeline counts updated from 1/0 to 0/1 while analysis remained enqueue_failed.
- CI workflow is added but hosted GitHub Actions results must be checked after a successful push; local checks alone are not a hosted-CI pass.
- No Postgres migration/runtime test or real provider call has been performed. PyPDF2 and existing migration-engine access emit deprecation warnings.

## Phase 4 checkpoint

- Added User/Organization/Membership with hashed passwords, active-account checks, eight-hour HTTP-only sessions, production Secure cookies, pre-login/mutation CSRF, and logout revocation.
- All recruiter reads/writes now query by organization in SQL, including compatibility aliases and candidate retry/stage routes. Public job/application endpoints remain unauthenticated and exclude sensitive recruiter fields.
- Migration `b730cce208a1` quarantines legacy jobs in an unclaimed organization without memberships; explicit operator CLI assignment is tested. The static recruiter file is removed.
- React login/session gate, real header identity, and logout are API-backed. Fake header notifications/search and unimplemented navigation are removed.
- Final verification: 75 pytest cases, Ruff, frontend typecheck/build, fresh schema check and legacy ownership migration tests pass. Browser redirect, cookie login, authenticated identity display, and logout pass against an isolated migrated SQLite database.
- One test initially failed because login fixtures made a request before a test registered its error route; it was repaired by replacing an existing view, with the same secret-leak assertions retained. No checks were skipped.
- Still unverified: PostgreSQL runtime, hosted CI status, actual provider integrations. Rate limiting and the legacy prototype's insecure endpoints remain pending; `main1` must not be run publicly.

## Phases 5–6 checkpoint — 2026-10-06

### PHASE

Persistent analysis foundation and job-aware Gemini resume analysis. This is a bounded checkpoint, not completion of GitHub integration or the full remediation plan.

### COMPLETED

- Durable one-to-one resume/GitHub records and per-repository storage; application persistence includes empty records before enqueue.
- Organization-scoped analysis GET and existing CSRF-protected retry API; completed components survive partial retries and sequential redelivery.
- Existing registered Celery task now extracts text and runs lazy, server-only Gemini structured analysis using linked job context and the prototype's category weights.
- Strict finite/bounded score, breakdown-sum, list and summary validation; safe persisted parsing/missing-key/provider failures. AI never changes recruiting stage.
- GitHub absence is optional/null; requested GitHub analysis explicitly reports unavailable rather than inventing evidence.

### FILES CHANGED

- [analysis models](../talent_intelligence_backend/models/analysis.py), candidate relationships and model registration.
- [orchestration](../talent_intelligence_backend/services/candidate_analysis.py), [Gemini adapter](../talent_intelligence_backend/services/ai/gemini.py), [resume analyzer](../talent_intelligence_backend/services/resume/analyzer.py), worker and application routes.
- [worker regression tests](../talent_intelligence_backend/tests/test_resume_pipeline.py), [provider validation tests](../talent_intelligence_backend/tests/test_resume_analyzer.py), migration/authorization tests and isolated fixtures.
- SDK dependency, root environment template, README and this audit.

### DATABASE MIGRATIONS

[c840ab218f12](../talent_intelligence_backend/migrations/versions/c840ab218f12_persist_resume_github_and_repository_.py) adds three tables and backfills existing candidates with pending records. Existing candidate text/scores/stages and jobs remain unchanged; no historical provider results are invented. Fresh upgrades, schema drift and legacy downgrade/reupgrade are tested. Downgrade drops component results as documented.

### VERIFICATION RUN

102 pytest cases and Ruff pass; frontend typecheck and production build pass. Tests isolate provider keys and mock provider output. Fresh SQLite schema check, legacy data preservation and migration roundtrips pass. No assertion weakening or skipped checks.

### MANUAL SMOKE TEST

Real HTTP against an isolated migrated SQLite server on port 5001: cookie/CSRF login, job creation, a parseable PDF containing text, application persistence, missing-key failure saved as null score, protected analysis GET returning 401 without login, retry, and unchanged screening stage all pass. The smoke server uses Celery eager execution, not a real broker/worker transport. Two smoke-fixture mistakes were corrected before the final pass: missing required jobType and modification of a PDF page copy rather than the writer-owned page. The final command preserves failure status.

### KNOWN LIMITATIONS

Live Gemini calls, PostgreSQL and hosted CI are unverified. GitHub integration and truthful candidate UI are still pending. Concurrent worker deliveries, killed-worker leases/recovery, an enqueue outbox and versioned analysis history are not implemented; only sequential redelivery is verified. Existing dependency deprecation warnings remain. No deployment-readiness claim.

### NEXT PHASE

Migrate bounded GitHub evidence collection/scoring with candidate-attributed activity, then replace candidate/profile mocks with persisted analyses and explicit unavailable states. Continue verified medium-sized GitHub pushes.

## Subsequent required work

Authentication + organization ownership/CSRF are implemented in Phase 4; deployment remains blocked on remaining privacy/rate-limit/provider/storage work. Persistent analyses and migrated providers, truthful candidate/interview/dashboard screens, secure interview sessions, privacy/rate limits/storage/audit, Compose, and final end-to-end scenario remain required. Do not treat a green initial CI checkpoint as product completion.
