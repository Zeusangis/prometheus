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

## Phase 7 checkpoint — 2026-10-06

### PHASE

Bounded public GitHub evidence and job-weighted repository analysis.

### COMPLETED

- Adapted prototype public REST pagination, language/tree/file selection and structured evidence review into lazy backend services; no unsafe `main1` app imports.
- Fixed-origin HTTPS, no redirects, bounded request/response/time budgets, repository/commit/tree/file caps, safe rate-limit/not-found/network/provider outcomes.
- Public counts and sample scopes are distinct; candidate author login is filtered/verified, commit SHAs deduplicated across forks, unknown totals remain null. No repository history-as-authorship claim.
- Persisted repository dimensions, normalized enabled metric weights, evidence citations/SHAs/truncation/caveats, partial provider outcomes and independent resume/GitHub retries.
- Wizard wording now discloses sampled activity, unmeasured coverage, and unsupported PR/issue/review evidence.

### FILES CHANGED

[REST client](../talent_intelligence_backend/services/github/client.py), [collector](../talent_intelligence_backend/services/github/collector.py), [scoring](../talent_intelligence_backend/services/github/analyzer.py), component orchestration and repository serialization; [GitHub regression tests](../talent_intelligence_backend/tests/test_github_analysis.py), offline test fixtures and prior resume expectations; [scraper wizard](../frontend_hackathon_1/src/components/jobs/steps/ScraperConfig.jsx), README and environment template.

### DATABASE MIGRATIONS

None: existing `c840ab218f12` analysis tables support these results. Full-suite migration/schema-drift tests remain passing.

### VERIFICATION RUN

151 pytest cases, Ruff, frontend typecheck/build pass. Initial Ruff found two semicolon-style violations; both corrected and all checks rerun. Verified caps (two repo pages, three analyzed repos, 30 commits, three 4,000-character file excerpts), author-only activity, fork deduplication, invalid citations/scores/config, safe HTTP errors, partial evidence and retry uniqueness/stale cleanup. Tests prevent live GitHub requests or local-key leakage. No performance improvement claim.

### MANUAL SMOKE TEST

Real localhost HTTP with isolated migrated SQLite, mocked GitHub evidence and eager Celery: authenticated job metric configuration, public PDF application, persisted GitHub language score/provenance despite resume parsing failure, unchanged screening stage, protected analysis GET, and retry preserving completed GitHub timestamp/rows pass. This is not live provider or real broker verification.

### KNOWN LIMITATIONS

Live GitHub/Gemini analysis, PostgreSQL and hosted CI are unverified. Public evidence is bounded/default-branch/sample-only; PRs/issues/reviews and measured test coverage are unavailable, missing metrics stay null. No global provider caching/rate budget or concurrent task leases yet. Repository excerpts can still contain sensitive public content despite filename exclusions; stronger redaction/consent policies remain necessary before production use. Candidate/profile mocks still need removal. Full remediation remains incomplete.

### NEXT PHASE

Wire truthful candidate/profile screens to persisted resume/GitHub evidence and statuses, then continue secure interview migration and deployment/privacy hardening. Push each verified coherent checkpoint.

## Phase 8 checkpoint — 2026-10-06

### PHASE

Truthful candidate profile wired to persisted resume and GitHub evidence.

### COMPLETED

- Removed every mock from the candidate profile: no fabricated name, location, contact links, archetypes, engagement score, verified-skill heatmap, match/verification badges, AI summary, "last scanned" timestamp, or demo footer.
- The profile renders only saved data from the authenticated candidate and analysis endpoints: real name, email, GitHub entity, resume filename, submission time, recruiting stage, and analysis status.
- Tabs are Overview, Resume, GitHub Evidence and Scores & Analysis. Resume ATS evidence and sampled repository scores are shown as unrelated scales that are never combined into one candidate score or ranking.
- Resume and GitHub components render explicit pending/running/complete/partial/failed/not-requested states, provider messages, weight coverage, fork caution, cited sampled files, commit provenance, authorship caveat, and sampling limits.
- Dead Share/Reject/Move buttons were replaced by real server-authorized stage actions: the client offers only `allowed_actions`, confirms before moving, surfaces transition errors, and states when a stage is terminal.
- Retry is offered only for failed, enqueue_failed and partial analysis, calls the existing retry endpoint with CSRF protection, and invalidates the profile and analysis queries; completed components stay preserved server-side.
- Loading, error, empty and not-found states are explicit; a candidate without a linked job states that stage changes are unavailable. The profile no longer links to the still-mocked interview summary screen.

### FILES CHANGED

[ProfilePage](../frontend_hackathon_1/src/pages/dashboard/ProfilePage.tsx) rewritten; it consumes the [analysis types and fetchers](../frontend_hackathon_1/src/api/apply.ts), [ResumeSection](../frontend_hackathon_1/src/pages/dashboard/ResumeSection.tsx) and [GitHubSection](../frontend_hackathon_1/src/pages/dashboard/GitHubSection.tsx) added earlier in this phase; README and this audit.

### DATABASE MIGRATIONS

None. No schema change: `c840ab218f12` remains the head migration and the full-suite migration/schema-drift tests are unaffected.

### VERIFICATION RUN

`npm run typecheck` and `npm run build` pass (both exit status 0). No backend file changed in this phase, so the backend 151-case pytest suite and Ruff were not re-run; their last verified result stands for the unchanged backend. Browser verification used an isolated migrated SQLite database served from outside the repository: only `GitHubClient.get` (canned HTTP responses) and the two Gemini `generate_json` entry points were replaced, so the real collector, weighting, validation, persistence, auth guard and stage logic executed.

### MANUAL SMOKE TEST

Real Chromium against a Vite dev server on port 5183 (proxy to the harness on port 5000), signed in as a seeded recruiter:

- Candidate applied through the real public endpoint with a GitHub username: profile shows the true name/email/filename, "Screening", "Analysis: Complete", resume 68/100 with all seven categories, verdict and four evidence lists, plus GitHub evidence for three repositories (67.67/100 at 90% weight coverage, 23.38/100 at 80%, 0/100 at 20%) with cited files, fork caution and provenance details.
- Candidate without a GitHub username: "Analysis: Failed", resume failed with the safe provider message and no score, GitHub tab "Not requested", retry offered. Clicking retry issued `POST /api/candidates/3/analysis/retry` (202) and refetched both queries; the component stayed failed with no invented score.
- Persisted queued candidate with pending components: "Analysis: Queued", resume "Pending" with "No score has been produced yet", retry correctly withheld.
- "Move to Interview Scheduled" showed a confirmation, then moved the candidate: badge "Interview Scheduled", next action "Move to Interview Completed", analysis still Complete, and both the API and the job applicant list reported `interview_scheduled`. Anonymous `GET /api/candidates/2/analysis` returned 401 `authentication_required`.
- No console errors or failed requests. No mock string (for example "Jane Sutherland", "High Match", "Figma Expert", "9.0", or the portfolio/engagement/archetype blocks) remained in the rendered profile.

### KNOWN LIMITATIONS

Live Gemini/GitHub calls, PostgreSQL and hosted CI remain unverified; the harness stubs GitHub HTTP transport instead of calling GitHub for real, and the resume provider output is canned. `/profile/$candidateId/interview-summary` still renders demo interview data and is no longer linked from the profile until the interview phase replaces it. No automated frontend test runner exists, so profile behaviour rests on typecheck/build plus manual browser checks. Candidate listing and dashboard screens still contain prototype content, and deployment hardening (rate limits, storage, privacy, concurrency) is outstanding.

### NEXT PHASE

Replace the interview-summary mock and the remaining prototype dashboard screens with persisted data, then continue interview-session security and deployment/privacy/concurrency hardening. Push each verified coherent checkpoint.

## Phase 9 checkpoint — 2026-10-06

### PHASE

Applicant screening queue and a recruiter dashboard built from stored applications.

### COMPLETED

- New `GET /api/candidates` screening queue, always scoped to the recruiter's organization through a join on that organization's jobs. It supports validated `stage` and `analysis_status` filters, named `attention` (failed/enqueue_failed/partial) and `running` (queued/running) groupings, job scoping that returns 404 for an unowned job, and case-insensitive name/email search. Results are newest first and bounded to 200 rows.
- `GET /api/jobs` now reports real `stage_counts` and `interviewing_count` from a single grouped query, so a job list never issues a query per job and no count is client-invented.
- The dashboard was rewritten against those endpoints: open roles, applicants, awaiting screening and analysis-needing-attention metrics; pipeline distribution across the canonical stages; roles with real applicant and interviewing counts; and a screening queue table showing stage, analysis status, real ATS evidence or "Not measured", review-and-retry links for retryable results, and server-authorized stage moves that invalidate the queue, job list and per-job applicant queries.
- Removed every fabricated dashboard widget: the fixed stats (24 jobs, 156 applicants, 42 interviews, 8 pending reviews), the "Import Data" button, the analytics bar chart, the "Interview with Sarah Chen" reminder with its Start Interview button, the fake team members with remote avatars and Add Member action, the fixed 41% "Positions Filled" ring, and the time tracker. Those six component files were deleted.
- Removed dead job-detail controls (a non-functional Edit Job Description button and two no-op icon buttons) and added real ATS evidence to each applicant row.
- The jobs table "Interviewing" column no longer renders a placeholder dash; it shows the real interviewing count plus how many applicants await screening.
- The legacy `/candidate/$candidateId` placeholder now redirects to the truthful applicant profile instead of rendering an empty screen.

### FILES CHANGED

[application_routes.py](../talent_intelligence_backend/routes/application_routes.py) (queue endpoint), [job_routes.py](../talent_intelligence_backend/routes/job_routes.py) (stage counts), [candidate_stage.py](../talent_intelligence_backend/services/candidate_stage.py) (analysis status vocabulary); [screening tests](../talent_intelligence_backend/tests/test_screening_queue.py); [screening API client](../frontend_hackathon_1/src/api/screening.ts), [jobs client types](../frontend_hackathon_1/src/api/jobs.ts), [Dashboard](../frontend_hackathon_1/src/components/Dashboard.tsx), [JobsList](../frontend_hackathon_1/src/components/JobsList.tsx), [JobDetail](../frontend_hackathon_1/src/pages/dashboard/JobDetail.tsx), [CandidateDetail](../frontend_hackathon_1/src/pages/dashboard/CandidateDetail.tsx); six deleted prototype components; README and this audit.

### DATABASE MIGRATIONS

None. No schema change: `c840ab218f12` remains the head migration, and the full-suite migration/schema-drift tests still pass.

### VERIFICATION RUN

163 pytest cases pass (12 new screening-queue and job-count cases) and Ruff reports no findings. `npm run typecheck` and `npm run build` both exit 0. The browser smoke again used an isolated migrated SQLite database served from outside the repository, where only `GitHubClient.get` (canned HTTP) and the Gemini `generate_json` entry points are replaced; the real queue query, org scoping, filters, stage transitions and serialization executed. No assertion was weakened and no check was skipped.

### MANUAL SMOKE TEST

Real Chromium against a Vite dev server on port 5183 (proxy to the harness on port 5000), signed in as a seeded recruiter, with four seeded applicants (complete, failed, partial and queued analysis):

- Dashboard rendered 1 open role, 4 applicants, 4 awaiting screening and 2 results needing attention with "1 analysis job still queued or running"; the pipeline showed Screening 4; the roles card showed "4 applicants · 0 interviewing".
- Screening queue showed all four applicants with their real stage, analysis status (Complete / Failed / Partial / Queued), ATS evidence (68/100 where the resume component completed, "Not measured" where it did not) and "Review and retry" links only for the failed and partial rows.
- Clicking "Move to Interview Scheduled" on an applicant moved the row to Interview Scheduled, changed its action to "Move to Interview Completed", dropped awaiting screening to 3, showed Interview Scheduled 1 in the pipeline, and updated the roles card to "1 interviewing".
- `/dashboard/jobs` showed "4 applicants / 3 awaiting screening" and "1 interviewing"; `/candidate/2` redirected to `/profile/2`; job detail listed each applicant with real ATS evidence and no dead controls.
- The partial applicant's profile reported "Overall status: Partial" with the retry affordance, and no fabricated dashboard string (Sarah Chen, Alexandra Deff, 156 applicants, 41% Positions Filled, Import Data) remained. No console errors and no failed requests.

### KNOWN LIMITATIONS

The queue is capped at 200 rows and returns only applicants linked to a job in the recruiter's organization; the dashboard table shows the 10 most recent of them. The filters exist server-side but the dashboard has no filter or search controls yet, and there is no pagination or CSV export. Live Gemini/GitHub, PostgreSQL, a real broker and hosted CI remain unverified. The interview-summary screen and interview workflow are still mocked, and candidates deleted outside the application would leave no audit trail. Deployment hardening (rate limits, storage, privacy, concurrency) is outstanding.

### NEXT PHASE

Add screening filters, search and pagination to the dashboard, then replace the interview-summary mock and continue interview-session security and deployment hardening. Push each verified coherent checkpoint.

## Phase 10 checkpoint — 2026-10-06

### PHASE

Screening queue filters, search, pagination and CSV export in the dashboard.

### COMPLETED

- `GET /api/candidates` is now paged: `page` (1-based) and `page_size` (default 10, maximum 100), and the response adds `page`, `page_size`, `total` and `summary`. `total` counts the rows matching the active filters, while `summary` carries organization-wide stage and analysis counts. The blunt 200-row cap was removed because one request can now only ever return `page_size` rows.
- Invalid pagination is rejected instead of silently coerced: a non-positive or non-numeric `page` returns 400 `page_invalid`, and a `page_size` outside 1..100 returns 400 `page_size_invalid`.
- The dashboard gained server-backed controls: stage, analysis-status, named grouping (needs attention / queued or running), per-role and rows-per-page selects, a debounced (300 ms) name/email search, page navigation with "Showing X–Y of N" and "Page p of n", and a CSV export of the rows on screen.
- Metric cards and the pipeline distribution now read the organization-wide `summary` instead of the rendered rows. This fixed a latent truthfulness bug: the previous implementation counted only the rows the client happened to have loaded, so narrowing or paging the queue would have changed "14 applicants" into the filtered count.
- CSV export quotes every field, doubles embedded quotes, and prefixes a leading `=`, `+`, `-`, `@`, tab or carriage return with an apostrophe so a stored value cannot execute as a spreadsheet formula.
- The `dashboard-queue-controls-missing` claim was closed, not weakened: its section 7 entry, its section 8 next step and its `tools/known_gaps.py` check were removed together, and section 8 was renumbered.

### FILES CHANGED

[application_routes.py](../talent_intelligence_backend/routes/application_routes.py) (pagination, total, organization summary), [test_screening_queue.py](../talent_intelligence_backend/tests/test_screening_queue.py) (13 new cases); [screening.ts](../frontend_hackathon_1/src/api/screening.ts), [Dashboard.tsx](../frontend_hackathon_1/src/components/Dashboard.tsx); [generate_project_context.py](../talent_intelligence_backend/tools/generate_project_context.py), [known_gaps.py](../talent_intelligence_backend/tools/known_gaps.py); [project-context.md](project-context.md) and the README.

### DATABASE MIGRATIONS

None. No schema change: `c840ab218f12` remains the head migration and the migration/schema-drift tests still pass.

### VERIFICATION RUN

207 pytest cases pass (13 new screening-queue cases: page and total reporting, paging without gaps or duplicates, a page past the end, seven invalid-pagination parameters, the largest allowed page, filter-independent totals and summary, and organization scoping of the summary) and Ruff reports no findings. `npm run typecheck` and `npm run build` both exit 0. The generated-inventory test passes, confirming Appendix A.4 now reports the page-size limit in place of the removed row cap and that the claim markers still match the registry.

### MANUAL SMOKE TEST

Real Chromium against a Vite dev server on port 5184 proxying an isolated harness on 5099, signed in as a seeded recruiter, with 15 applicants inserted directly into the smoke database so that no provider call or GitHub request was made:

- Page 1 listed the 10 newest applicants newest-first with "Showing 1–10 of 14" and "Page 1 of 2". The metric cards read 1 open role, 14 applicants, 3 awaiting screening and 7 needing attention with "4 analysis jobs still queued or running"; the pipeline showed Screening 3, Interview Scheduled 3, Interview Completed 2, Offer Made 2, Hired 2, Rejected 2 — each matching the database.
- "Next" listed the 4 oldest applicants with "Showing 11–14 of 14", "Page 2 of 2" and Next disabled, while every metric card stayed unchanged.
- Filtering to Rejected reduced the table to 2 rows, reset to "Page 1 of 1" and "Showing 1–2 of 2 applicants matching these filters", and the metric cards again stayed at 14 / 3 / 7 — the property that naive pagination would have silently broken.
- Typing `grace` (after the debounce) reduced the table to Grace Hopper with "Showing 1–1 of 1 applicant matching these filters".
- Rows per page 25 showed all 14 rows on a single page.
- CSV export produced the expected header and 15 rows. A deliberately hostile applicant name `=HYPERLINK("http://evil.invalid","click")` was exported as `'=HYPERLINK(""http://evil.invalid"",""click"")` — formula neutralised and quotes doubled — and an email containing a comma and a quote stayed inside one correctly quoted field.
- No console errors and no failed requests.

### KNOWN LIMITATIONS

Pagination and search are server-side but `page` is unbounded, so a very large page number still performs a deep offset scan; only the page size is capped. CSV export writes the rows on screen rather than the whole result set. There is still no frontend test runner, so the filter, pagination, search and CSV behaviour is covered by the browser smoke above rather than by an automated unit test. The interview-summary and interview screens remain mocked, and audit, rate limiting, storage, retention and concurrency work remain outstanding.

### NEXT PHASE

Replace the mocked interview-summary screen with persisted interview data and design the secure interview-session model, then continue deployment hardening: an immutable audit trail for stage changes and retries, rate limiting on auth and public apply, and object storage with a retention policy.

## Phase 11 checkpoint — 2026-10-06

### PHASE

A partial or failed GitHub analysis must record a reason that matches its status.

### COMPLETED

- Every incomplete GitHub outcome previously stored one generic sentence ("Some repository evidence or AI reviews could not be completed."), and the repositories that actually failed were only discoverable by inspecting each row. `summary.errors` carried collection failures but never review failures, so a `partial` status could be recorded with no indication of what was missing.
- The recorded `error_message` now names the repositories that failed, split by cause: "repository evidence could not be collected for X" and "the AI review could not be completed for Y", joined with `; ` and prefixed by "GitHub analysis is partial:" or "GitHub analysis failed:". A `partial` or `failed` status can no longer be recorded without a reason naming the failure.
- `summary.review_failures` was added as `[{repo_name, message}]`, so a review failure is discoverable from the summary exactly as a collection failure already was, and the GitHub Evidence tab renders it beside the existing collection errors.
- Only repository names and our own fixed category wording are used. Provider payloads, response bodies, URLs and credentials are never copied into the reason, extending the existing rule that provider exception text is never stored.

### FILES CHANGED

[analyzer.py](../talent_intelligence_backend/services/github/analyzer.py), [test_github_analysis.py](../talent_intelligence_backend/tests/test_github_analysis.py) (6 new cases); [apply.ts](../frontend_hackathon_1/src/api/apply.ts), [GitHubSection.tsx](../frontend_hackathon_1/src/pages/dashboard/GitHubSection.tsx); [project-context.md](project-context.md) and the README.

### DATABASE MIGRATIONS

None. `summary` is an existing JSON column and an added key needs no migration; `c840ab218f12` remains the head migration.

### VERIFICATION RUN

212 pytest cases pass (6 new: a review-only failure names its repository, a collection-only failure names its repository, both kinds named together, a failed analysis that names its reason, a complete analysis with no reason and no review failures, and a persisted partial reason surviving to the API) and Ruff reports no findings. `npm run typecheck` and `npm run build` both exit 0.

### MANUAL SMOKE TEST

Real Chromium against the isolated harness, signed in as a seeded recruiter, with one applicant whose saved GitHub result is partial. The GitHub Evidence tab showed the status chip "Partial", the recorded reason "GitHub analysis is partial: repository evidence could not be collected for Hello-World; the AI review could not be completed for octocat/Spoon-Knife, octocat/octocat.github.io. Retry later.", and the matching per-repository lines drawn from `summary.errors` and `summary.review_failures`. No console errors.

### KNOWN LIMITATIONS

The reason is a single assembled sentence, so it is not machine-readable beyond the two summary lists; a consumer parsing the prose rather than the lists is still guessing. At most three repositories are analysed, so the named list is naturally short and carries no truncation notice.

### NEXT PHASE

Continue deployment hardening: an immutable audit trail for stage changes and retries, rate limiting on auth and public apply, and object storage with a retention policy; and replace the mocked interview-summary screen.

## Subsequent required work

Authentication + organization ownership/CSRF (Phase 4), persisted analyses and providers (Phases 5-7), the truthful applicant evidence profile (Phase 8), the organization-scoped screening queue and dashboard (Phase 9) and its filters, search, pagination and CSV export (Phase 10) are implemented. Deployment remains blocked on remaining privacy/rate-limit/provider/storage work. The interview-summary and interview screens, secure interview sessions, privacy/rate limits/storage/audit, Compose, and the final end-to-end scenario remain required. Do not treat a green initial CI checkpoint as product completion.
