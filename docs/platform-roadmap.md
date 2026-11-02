# Platform Roadmap

This roadmap translates the phase-wise plan into an implementation order that keeps the current app useful while growing it into a stronger production-style portfolio project.

## Current Baseline: v1 Streamlit

Status: implemented.

TruthFit v1 is a public Streamlit app with resume/JD upload, privacy-aware redaction, multi-provider LLM calls, evidence-based scoring, dashboard sections, no-API sample mode, chat, PDF export, tests, and a local job tracker.

Keep this version deployable while the v2 platform is built.

## Security Hardening: Phase 0 and Phase 1

Status: implemented.

Phase 0 established the production boundary: explicit API configuration, validated CORS origins, recoverable frontend failures, and removal of development-only labels from public UI.

Phase 1 added Supabase email authentication and ownership enforcement. FastAPI verifies access tokens, maps the JWT subject to `users.auth_subject`, protects product workflows, scopes repository reads and writes by `user_id`, and returns `404` for cross-account record IDs. Automated tests cover missing authentication and account isolation.

Phase 3 now covers redacted-only persistence, encrypted retained originals, retention/deletion workflows, and queued-key isolation. Remaining security work includes rate limiting, quotas, abuse controls, key rotation, and security monitoring.

## Privacy Phase 3: Retention And Deletion

Status: implemented.

- Resume originals remain transient by default; the database stores the redacted copy.
- Explicit retention uses AES-GCM with a server-managed 32-byte key.
- Users can inspect their stored record counts and delete one analysis or all TruthFit application data.
- Pending, failed, and completed runs receive configurable expiry dates.
- A cleanup command is available for a daily platform scheduler.
- Browser BYOK credentials stay in React memory. Production RQ accepts only server-managed provider credentials.

Operational follow-up: define a key-rotation procedure, schedule cleanup in each deployed environment, and add retention audit metrics.

## Reliability Phase 2: Analysis Lifecycle

Status: implemented.

Analysis creation is asynchronous and durable:

- `POST /analysis/run` commits a `pending` run and returns `202 Accepted`.
- A worker transitions the run through `processing` to `completed` or `failed`.
- Provider calls run without an open database transaction.
- Completion and failure events are committed independently.
- The Next.js fit-review page polls the owned run until it reaches a terminal state.
- Local development uses FastAPI background tasks; production selects Redis/RQ through environment configuration.

This reliability sequence is separate from the original platform phases below, where Platform Phase 2 refers to PostgreSQL persistence.

## Phase 1: API Boundary

Status: implemented as the first backend slice.

Extract a FastAPI backend with these first endpoints:

- `GET /health`
- `POST /resumes/parse`
- `POST /jobs/parse`
- `POST /analysis/run`
- `GET /analysis/{run_id}`
- `POST /tailor`
- `GET /providers`

Acceptance criteria:

- A complete analysis can run through the API without Streamlit.
- Request and response bodies are validated with Pydantic.
- Provider failures return safe, user-facing errors.
- Unit tests cover the service layer and route contracts.

Remaining follow-up:

- The temporary in-memory store has been replaced by SQLAlchemy persistence in Phase 2.
- Add contract tests around external provider error payloads.
- Decide whether Streamlit should eventually call the API or remain a separate v1 demo.

## Platform Phase 2: Persistence

Status: implemented with SQLAlchemy models, Alembic migrations, authenticated ownership, database-backed history, and tracker workflows.

The API supports PostgreSQL configuration and a local SQLite fallback.

Core tables:

- users
- resumes
- jobs
- analysis_runs
- evidence
- agent_events

Progress against acceptance criteria:

- Completed analyses, saved jobs, and dashboard history are scoped to the authenticated user.
- Evidence records are stored separately and queryable through the database; no evidence-listing endpoint exists yet.
- The Streamlit tracker still depends on local JSON files; migrating it remains pending.

Current implementation note:

- The backend supports PostgreSQL through `DATABASE_URL`.
- Local development and tests use SQLite as a lightweight fallback.
- Supabase sessions are verified by FastAPI and mapped through `users.auth_subject`; client payloads cannot select an owner.

## Platform Phase 3: Product Frontend

Status: implemented as a first Next.js frontend slice.

Build the product workflow on the stabilized FastAPI contracts while keeping Streamlit available as the public v1 demo.

The frontend should focus on:

- polished dashboard navigation
- persistent user sessions
- analysis history
- job-specific result pages
- clearer resume improvement workflows

Current implementation:

- `apps/web` contains a Next.js app.
- Core routes are implemented: `/`, `/dashboard`, `/resumes`, `/jobs`, `/analysis/[id]`, `/tailor/[id]`, and `/settings/providers`.
- The frontend calls the FastAPI backend through `NEXT_PUBLIC_TRUTHFIT_API_URL`.
- Resume parsing, job parsing, analysis run creation, saved analysis retrieval, tailoring, provider settings, dashboard metrics, and error/loading states are covered in the UI.
- Supabase sign-up, sign-in, sign-out, callback handling, protected navigation, and authenticated API requests are implemented.
- The dashboard emphasizes application progress, score history, recurring gaps, follow-ups, and resume-version comparisons; the tracker supports inline status, priority, dates, filtering, sorting, and notes.
- CI typechecks and builds the web app.

Remaining follow-up:

- Add richer aggregate charts after enough real persisted analysis data exists.
- Decide whether to retire Streamlit or keep it as a simple public demo.

## Platform Phase 4: LLM Gateway and Agent Workflow

Convert provider calls into a gateway with consistent routing, retries, fallback logging, timeouts, and model metadata.

Then split the analysis into deterministic agents:

- Job Requirement Agent
- Resume Evidence Agent
- Skill Gap Agent
- Resume Tailoring Agent
- Verification Agent

The first version should use a simple state machine before introducing a heavier orchestration framework.

## Platform Phase 5: Production Signals

Add production-style platform features once the product flow is stable:

- Docker and Docker Compose
- Redis for rate limits and cache, building on the existing RQ analysis queue
- Prometheus metrics
- Grafana dashboards
- Kubernetes manifests
- CI/CD and security scanning
- Terraform for cloud infrastructure
- an evaluation dataset for extraction, evidence, and tailoring safety

## Portfolio Demo Standard

A strong demo should show:

1. Upload a resume.
2. Add a job description and job link.
3. Run analysis.
4. Review requirements, evidence, gaps, tailoring, and verification.
5. Trigger or explain provider fallback behavior.
6. Show tests and GitHub Actions.
7. Explain the architecture and migration path in two minutes.

Do not claim full production readiness until the hosted PostgreSQL/RQ path is validated, cleanup is scheduled, rate limits and quotas are enforced, key rotation is documented, and redaction is evaluated against a broader corpus.
