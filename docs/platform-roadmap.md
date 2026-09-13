# Platform Roadmap

This roadmap translates the phase-wise plan into an implementation order that keeps the current app useful while growing it into a stronger production-style portfolio project.

## Current Baseline: v1 Streamlit

Status: implemented.

TruthFit v1 is a public Streamlit app with resume/JD upload, privacy-aware redaction, multi-provider LLM calls, evidence-based scoring, dashboard sections, no-API sample mode, chat, PDF export, tests, and a local job tracker.

Keep this version deployable while the v2 platform is built.

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

## Phase 2: Persistence

Status: database foundation implemented as SQLAlchemy models, repositories, Alembic migration, seed script, and SQLite API integration tests. User-facing history and tracker migration remain pending.

The API supports PostgreSQL configuration and a local SQLite fallback.

Core tables:

- users
- resumes
- jobs
- analysis_runs
- evidence
- agent_events

Progress against acceptance criteria:

- Completed analyses can be retrieved by run ID; saved-job browsing and user-facing history remain pending.
- Evidence records are stored separately and queryable through the database; no evidence-listing endpoint exists yet.
- The Streamlit tracker still depends on local JSON files; migrating it remains pending.

Current implementation note:

- The backend supports PostgreSQL through `DATABASE_URL`.
- Local development and tests use SQLite as a lightweight fallback.
- Authentication and real user sessions are still planned; until then, API requests can pass `user_email`.

## Phase 3: Product Frontend

Move to a Next.js frontend after backend contracts stop changing.

The frontend should focus on:

- polished dashboard navigation
- persistent user sessions
- analysis history
- job-specific result pages
- clearer resume improvement workflows

## Phase 4: LLM Gateway and Agent Workflow

Convert provider calls into a gateway with consistent routing, retries, fallback logging, timeouts, and model metadata.

Then split the analysis into deterministic agents:

- Job Requirement Agent
- Resume Evidence Agent
- Skill Gap Agent
- Resume Tailoring Agent
- Verification Agent

The first version should use a simple state machine before introducing a heavier orchestration framework.

## Phase 5: Production Signals

Add production-style platform features once the product flow is stable:

- Docker and Docker Compose
- Redis for rate limits, cache, and task state
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

Do not claim production readiness until auth, production database deployment and validation, rate limits, server-side key controls, stronger redaction, and data-retention controls are implemented.
