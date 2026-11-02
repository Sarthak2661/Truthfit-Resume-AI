# TruthFit Resume AI

[![Tests](https://github.com/Sarthak2661/Truthfit-Resume-AI/actions/workflows/tests.yml/badge.svg)](https://github.com/Sarthak2661/Truthfit-Resume-AI/actions/workflows/tests.yml)
[![Open Streamlit v1 Demo](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://truthfit-resume-ai-vaos6czappyfazhugbyffub.streamlit.app/)

**Public demo (Streamlit v1):** https://truthfit-resume-ai-vaos6czappyfazhugbyffub.streamlit.app/

TruthFit Resume AI is an evidence-grounded resume and job-fit review product. It compares a resume against a specific job description, explains the match score, checks whether important claims are backed by real evidence, and turns gaps into practical resume improvements and application actions.

The goal is not to "game" an ATS or invent stronger experience. TruthFit is built around a simple idea: a resume should be tailored only with evidence that already exists in the candidate's work, projects, education, or portfolio.

The repository currently contains two interfaces:

- **Streamlit v1** is the deployed portfolio demo with no-API sample data, chat, PDF export, and a local job tracker.
- **Next.js + FastAPI** is the newer product interface with combined resume/JD review, persisted analyses, Apply Readiness, inline tailoring, and an API-backed Kanban tracker. It currently runs locally and is not yet publicly deployed.

## Current Product Status

The first four security and reliability phases of the Next.js/FastAPI product path are complete:

| Phase | Status | Delivered |
| --- | --- | --- |
| Reliability Phase 0: containment | Complete | Production API URL validation, environment-driven CORS, recoverable client errors, removal of public development labels, and fail-fast production configuration. |
| Reliability Phase 1: authentication and ownership | Complete | Supabase email authentication, JWT verification in FastAPI, protected product routes, authenticated user mapping, user-scoped repositories, cross-account `404` responses, and ownership isolation tests. |
| Reliability Phase 2: analysis lifecycle | Complete | Durable pending, processing, completed, and failed states; `202 Accepted` analysis requests; client polling; typed provider errors; independently committed failure events; and Redis/RQ production dispatch. |
| Privacy Phase 3: retention and deletion | Complete | Redacted-only default persistence, optional AES-GCM encrypted originals, per-analysis and account-data deletion, configurable expiry, cleanup tooling, and memory-only browser BYOK credentials. |

Supabase stores login identities in its managed `auth.users` table, visible under **Authentication > Users**. TruthFit stores its application user record and owned analyses in the database selected by `DATABASE_URL`. A local `DATABASE_URL` therefore keeps application tables in local PostgreSQL even though authentication is handled by Supabase.

## Streamlit v1 Screenshots

These screenshots show the currently deployed Streamlit demo. Updated Next.js product screenshots will replace this section when the new frontend is publicly deployed.

| Home | Analyze | Overview |
| --- | --- | --- |
| ![Landing](resources/landing.png)<br><sub>Landing page with provider settings, theme toggle, and product overview.</sub> | ![Analyze](resources/analyze.png)<br><sub>Privacy-first upload flow for resume, job description, job link, and project notes.</sub> | ![Dashboard](resources/dashboard.png)<br><sub>Overview tab with scores, privacy note, verdict, score drivers, and top fixes.</sub> |

| Skills & Requirements | Evidence & Risks | Improve Resume |
| --- | --- | --- |
| ![Skills and Requirements](resources/skills-requirements.png)<br><sub>Matched and missing skills, role details, and requirement-level evidence.</sub> | ![Evidence and Risks](resources/evidence-risks.png)<br><sub>Proof checks, unsupported claims, eligibility risks, and optional resume proof map.</sub> | ![Improve Resume](resources/improve-resume.png)<br><sub>Editable resume summary, rewrites, fixes, projects, certifications, and learning ideas.</sub> |

| Export & Track | Job Tracker |
| --- | --- |
| ![Export and Track](resources/export-track.png)<br><sub>PDF export, original posting link, and shortcut into job tracking.</sub> | ![Job Tracker](resources/tracker.png)<br><sub>Local tracker for role, company, link, status, salary expectation, score, priority, and notes.</sub> |

## Architecture

```mermaid
flowchart LR
    resume["Resume<br>PDF / DOCX / TXT"] --> loaders["Validation and text extraction"]
    jd["Job description<br>file, paste, or link"] --> loaders
    loaders --> redact["Privacy-aware redaction"]
    redact --> api["FastAPI services"]
    projects["Project evidence"] --> api
    web["Next.js product interface"] --> api
    streamlit["Streamlit v1 demo"] --> shared["Shared domain services"]
    api --> shared
    shared --> providers["Gemini / Claude / OpenAI / Perplexity"]
    providers --> schema["Structured validation and normalization"]
    schema --> db[("PostgreSQL / SQLite")]
    schema --> review["Fit review and tailoring"]
    db --> history["Analysis history and job tracker"]
    sample["No-API sample analysis"] --> streamlit
```

The UI layers do not contain the core analysis logic. FastAPI routes call services, services call shared parsing and analysis modules, and persistence is isolated behind SQLAlchemy repositories. The same loaders, privacy rules, provider clients, structured schemas, evidence scoring, and cleanup services can support both interfaces.

- `apps/web/` contains the Next.js product interface.
- `apps/api/` contains FastAPI routes, application services, and SQLAlchemy repositories.
- Local analysis work uses FastAPI background tasks. Production uses Redis and RQ so provider calls do not hold request or database transactions open.
- `source/ai/` contains prompts, provider clients, retry/fallback behavior, and structured schemas.
- `source/loaders/` contains upload validation and shared file extraction.
- `source/services/` contains evidence, scoring, reporting, privacy, tracker, URL, and observability logic.
- `source/pages/` and `source/ui/` contain the Streamlit v1 experience.

For the detailed current architecture, target v2 architecture, migration plan, and architecture decisions, see:

- [Architecture](docs/architecture.md)
- [FastAPI backend](docs/api.md)
- [Platform roadmap](docs/platform-roadmap.md)
- [v1 Streamlit baseline](docs/v1-baseline.md)
- [Architecture decision records](docs/adr/ADR-001-keep-streamlit-v1-as-baseline.md)

## What It Does

- Upload a resume as PDF, DOCX, or TXT.
- Upload or paste a job description on the same review screen.
- Add the original job posting link.
- Choose Gemini, Claude, OpenAI, or Perplexity with a bring-your-own-key setup.
- Extract hard requirements, preferred signals, role metadata, and ATS formatting risks.
- Generate a structured fit review with explainable scores, evidence, risks, and priority fixes.
- Review Apply Readiness, score drivers, requirement coverage, missing proof, and unsupported claims.
- Accept, edit, reject, and copy evidence-grounded bullet rewrites in the Next.js tailoring workflow.
- Save completed analyses to an API-backed Kanban tracker with role, company, location, score, notes, status, and a link back to the review.
- Create an account or sign in with Supabase Auth; dashboard, analysis, tailoring, and tracker records are isolated by the verified account identity.
- Use a no-API sample report so reviewers can explore the product without adding an API key.

Safe demo inputs are included in [`samples/sample_resume.txt`](samples/sample_resume.txt) and [`samples/sample_job_description.txt`](samples/sample_job_description.txt). They are fictional and safe to use when testing the deployed app.

## Fastest Demo Path

1. Open the [live app](https://truthfit-resume-ai-vaos6czappyfazhugbyffub.streamlit.app/).
2. Click **Try Demo** in the sidebar.
3. Review the dashboard sections in order: Overview, Skills & Requirements, Evidence & Risks, Improve Resume, and Export & Track.
4. Open **Tracker** to see how a completed analysis can be saved as an application record.

The demo uses synthetic data and does not call Gemini, Claude, OpenAI, or Perplexity.

## Core Features

### Privacy-Aware Review

TruthFit applies best-effort redaction before resume preview, proof mapping, and live provider calls. It currently targets common names, phone numbers, emails, URLs, and street-style addresses.

The Streamlit app does not save uploaded resume and job-description files. It uses session text for analysis and stores local tracker data when an entry is saved. Completed FastAPI analyses store redacted resume text by default, plus JD text, the structured result, evidence records, and operational events. Original resume text remains transient unless the account explicitly enables encrypted retention. Parse-only API requests are not persisted. See [API storage and access boundaries](docs/api.md#storage-and-access-boundaries).

The redaction heuristic is covered by tests against several realistic resume-header layouts across US, India, UK, and GCC-style contact formats. The current fixture set redacts all checked sensitive tokens, but this is still a test-sample result, not a guarantee for every resume design.

### Resume Evidence Score

TruthFit does not only ask "does this keyword appear?" It also checks whether claims are backed by concrete proof:

- work experience
- project evidence
- tools and technologies
- measurable outcomes
- education or certification details

This helps separate strong resume evidence from unsupported or vague claims.

### Score Explanation

The fit review shows:

- overall match
- technical match
- requirement and keyword coverage
- resume evidence strength
- eligibility fit
- experience fit
- score drivers that explain what raised or lowered the final score
- Apply Readiness based on parser checks, requirement coverage, unsupported claims, and the top three fixes

## How Scoring Works

TruthFit uses structured model output plus local normalization checks. The score is not a real ATS simulation; it is a transparent review score designed to show fit, risk, and evidence quality.

- **Overall match** summarizes the role fit after technical skills, keyword coverage, experience, eligibility, and proof quality are considered.
- **Technical match** checks whether the resume supports the tools, systems, and workflows requested in the job description.
- **ATS coverage** measures keyword and requirement coverage, but it does not claim to reproduce any employer's ATS.
- **Resume evidence proof** checks whether important claims are backed by work, project, tool, metric, education, or certification evidence.
- **Eligibility and experience** flag location, authorization, salary, years-of-experience, or must-have requirement risks when the JD makes them visible.
- **Score drivers** explain what raised or lowered the final score so the result does not feel like a black box.

The prompt requires the model to write "Not found in resume" when evidence is missing. The UI also shows confidence, resume evidence, JD evidence, and what should be verified manually for major findings.

Before results are rendered, TruthFit validates the model response with Pydantic-backed schema checks. Missing sections are filled with safe defaults, score fields are clamped to 0-100, and malformed list/dictionary sections are normalized so the dashboard does not render raw or unstable model output.

### Skills and Requirements Review

The app compares the resume against must-have and nice-to-have job requirements, then shows matched and missing skills in a table with:

- skill
- status
- importance
- resume evidence
- suggested action

### Proof and Risk Checks

TruthFit flags gaps that could weaken an application:

- unsupported claims
- eligibility or location risks
- timeline issues
- missing requirement evidence
- claims that should be verified manually before rewriting the resume

### Resume Improvement Tools

The app can generate:

- tailored resume summary
- rewritten bullets grounded in existing evidence
- before/after bullet comparisons
- resume fix suggestions
- project suggestions
- certification suggestions
- optional cover letter

The Next.js tailoring page adds an inline bullet editor with accept, edit, reject, and copy actions. Those decisions currently remain in browser state and are not yet persisted or exported as a new resume file.

### Chat and Export

After an analysis is generated, the chat helper can answer follow-up questions, draft a cover letter, suggest recruiter outreach, or explain the score. The report can also be exported as a PDF.

### Basic Observability

TruthFit logs privacy-safe operational events for local and cloud debugging:

- provider/model used for live calls
- request duration and retry attempts
- JSON parsing failures
- file loading errors
- chat and analysis failures

Logs intentionally exclude API keys, prompts, resume text, job descriptions, and uploaded file contents.

Provider failures are stored as failed runs with a safe error category and message. They are not converted into successful zero-score analyses.

## Product Interfaces

### Next.js Product Interface

- **Analyze:** resume upload, redacted preview, ATS formatting checks, JD extraction, regional targeting, and provider setup on one page.
- **Dashboard:** recent saved analyses, average match score, recurring skill gaps, provider usage, and failed runs.
- **Fit Review:** five score dimensions, Apply Readiness, score drivers, requirement coverage, skills evidence, unsupported claims, and tracker actions.
- **Tailoring:** priority fixes, tailored summary, inline bullet editing, project ideas, certifications, learning steps, and optional cover letter.
- **Tracker:** API-backed Kanban columns for Saved, Applied, Interview, and Rejected opportunities.

### Streamlit v1 Demo

The deployed Streamlit interface remains available as a self-contained portfolio demo. It includes the no-API sample dashboard, five analysis sections, follow-up chat, PDF export, theme switching, and a local JSON-backed tracker.

## Tech Stack

- Python
- Streamlit
- Plotly
- pandas
- pypdf
- python-docx
- Google Gemini API
- Anthropic Claude API
- OpenAI API
- Perplexity API
- pytest
- GitHub Actions
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Next.js
- React
- TypeScript

## Setup

TruthFit is developed and tested with **Python 3.12.8**. The repository includes `.python-version` and `runtime.txt` so local and deployment environments can use the same version.

### Python Environment

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Copy `.env.example` to `.env` for local development, or enter a temporary provider key in the interface:

```env
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
```

### Streamlit v1

```powershell
streamlit run app.py
```

The Streamlit app opens at `http://127.0.0.1:8501`.

### Next.js + FastAPI Product Interface

Create a Supabase project and enable Email authentication. Add both `http://127.0.0.1:3000/auth/callback` and `http://localhost:3000/auth/callback` to the allowed redirect URLs in Supabase. Copy the project URL and publishable key into the API and frontend environments. For public account creation, create an hCaptcha site, add its site key to the frontend, and configure its secret under Supabase Authentication > Bot and Abuse Protection.

Root `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_AUDIENCE=authenticated
TRUTHFIT_ANALYSIS_QUEUE=background
```

For a public API deployment, use `TRUTHFIT_ANALYSIS_QUEUE=rq`, set `REDIS_URL`, and run an RQ worker. Keep Redis private and encrypted because queued jobs may contain a temporary bring-your-own provider key.

The current provider catalog is returned by `GET /providers` and is the source of truth for both interfaces. Retired model IDs are rejected before an analysis is created.

`apps/web/.env.local`:

```env
NEXT_PUBLIC_TRUTHFIT_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_publishable_key
NEXT_PUBLIC_HCAPTCHA_SITE_KEY=your_hcaptcha_site_key
```

Configure persistence and apply the database migration. PostgreSQL is recommended for deployment; without `DATABASE_URL`, development uses SQLite at `.truthfit/truthfit.db`.

```powershell
$env:DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/truthfit"
alembic upgrade head
```

Alembic reads the repository root `.env`; an explicitly exported `DATABASE_URL` takes precedence. If the URL points to `localhost`, tables are created in local PostgreSQL. To keep application records in Supabase Postgres, use the Supabase database connection string instead.

Start the API:

```powershell
py -3.12 -m uvicorn apps.api.app.main:app --reload --env-file .env
```

The Swagger UI is available at `http://127.0.0.1:8000/docs`. To seed safe sample records:

```powershell
py -3.12 scripts/seed_database.py
```

In another terminal, start the frontend:

```powershell
cd apps/web
npm ci
npm run dev
```

The frontend opens at `http://127.0.0.1:3000`. Sign in or create an account before opening dashboard, analysis, tailoring, or tracker routes. Production builds require explicit API and Supabase configuration.

```env
NEXT_PUBLIC_TRUTHFIT_API_URL=https://your-api-host
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_publishable_key
NEXT_PUBLIC_HCAPTCHA_SITE_KEY=your_hcaptcha_site_key
```

Production API deployments must also set `TRUTHFIT_ENV=production`, `SUPABASE_URL`, and a comma-separated `TRUTHFIT_ALLOWED_ORIGINS` value. FastAPI verifies Supabase JWT signatures and scopes every analysis, dashboard, and tracker query to the authenticated subject.

Runtime and development dependencies are pinned for repeatable local and cloud builds. See [database setup](docs/api.md#database) for additional PostgreSQL and migration guidance.

## Tests

Install the dev dependency and run the test suite:

```bash
pip install -r requirements-dev.txt
pytest -q
```

The test suite covers:

- resume and JD file loaders
- JSON extraction from messy LLM output
- job tracker normalization, save/load, and dedupe behavior
- PDF report generation
- UI text cleanup
- privacy-aware redaction
- resume proof map generation
- resume evidence scoring
- API authentication, cross-user ownership isolation, route contracts, database health, persisted analysis retrieval, dashboard summaries, tracker compatibility, and mocked provider responses

Validate the Next.js frontend separately:

```powershell
cd apps/web
npm run typecheck
npm run build
```

The current repository contains 70 Python tests, TypeScript validation, and a production Next.js build.

### Continuous Integration

GitHub Actions runs two independent checks on every push and pull request:

- **Python:** installs the pinned dependencies on Python 3.12.8, runs `pytest -q`, and checks the repository with Ruff.
- **Web:** installs the lockfile-pinned packages on Node.js 24, runs the TypeScript check, and creates a production Next.js build.

Both jobs must pass before a product update is considered ready to merge.

## Deployment

The public Streamlit v1 demo is deployed on Streamlit Community Cloud. The Next.js product interface requires the frontend, API, and database to be deployed separately.

| Component | Recommended deployment |
| --- | --- |
| Streamlit v1 demo | Streamlit Community Cloud |
| Next.js frontend | Vercel, Netlify, or a Node-capable container host |
| FastAPI backend | Render, Railway, Fly.io, or a container platform |
| PostgreSQL | Neon, Supabase, Railway, or Render |

Keep provider keys out of the repository. The current portfolio flow supports user-provided keys; a production service should use controlled server-side keys with authentication, rate limits, and usage caps.

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment steps.

## Limitations

- The ATS score is an approximation, not a real ATS simulation.
- ATS formatting checks are deterministic heuristics over extracted content and cannot reproduce every employer parser.
- Model output can be incomplete, inconsistent, or overconfident.
- PDF parsing can be messy for resumes with columns, tables, images, or unusual layouts.
- Privacy redaction is heuristic and should not be treated as legal or compliance-grade anonymization.
- Live analysis still sends redacted resume/JD text to the selected provider.
- Inline tailoring decisions are not persisted or exported as a new DOCX/PDF resume.
- Regional targeting is an initial prompt-based mode, not a validated market-specific rules engine.
- The Streamlit tracker is local; the Next.js tracker is authenticated and database-backed.
- The Next.js frontend is not yet publicly deployed.

## Roadmap

TruthFit now includes the Streamlit v1 baseline, FastAPI services, SQLAlchemy persistence, and the first Next.js product interface. The next work is focused on making that product path safer, more persistent, and easier to deploy. The detailed phased plan is tracked in [docs/platform-roadmap.md](docs/platform-roadmap.md).

### 1. Security and User-Scoped History

Phases 0-3 now cover production configuration, account ownership, durable analysis state, redacted-only storage, optional encrypted retention, and user-controlled deletion. The next security work is rate limiting, abuse controls, managed provider quotas, key rotation, and security monitoring.

### 2. Persistent Resume Versions and Export

Persist accepted, edited, and rejected bullet decisions. Let each tracked job reference the exact tailored resume version used, then export that version to DOCX or PDF.

### 3. GitHub Evidence Extractor

Allow users to paste GitHub repository links and automatically extract project evidence from README files, tech stacks, commits, folder structure, and documentation. This would make project suggestions and resume proof scoring more grounded in real portfolio work.

### 4. Project Recommendation Model

Build a stronger recommendation layer that maps missing role evidence to specific portfolio projects, including scope, stack, difficulty, timeline, resume bullet examples, and the exact requirement each project would support.

### 5. Role and Region-Specific Review Modes

Replace the current regional prompt hints with tested India, GCC, and US rules for role titles, notice periods, location and visa realities, resume conventions, and hiring terminology. Add role-specific weighting for Data Engineering, Analytics, Software Engineering, and Machine Learning.

### 6. Production Provider Controls

Add managed provider quotas, rate limiting, abuse controls, per-account usage reporting, and security monitoring. Production RQ runs already use server-managed provider credentials and reject browser-provided keys.

### 7. Evaluation and Score Calibration

Build a versioned evaluation dataset for requirement extraction, evidence precision, unsupported-claim detection, redaction, score stability, and tailoring safety.

### 8. Containerized Deployment and Observability

Containerize the Next.js, FastAPI, and PostgreSQL product path. Add configurable production CORS, metrics, health monitoring, security scanning, and deployment automation.

## Privacy Note

TruthFit applies heuristic redaction before resume preview, proof mapping, and live analysis. Streamlit does not save uploaded files. FastAPI stores redacted resume text by default; users may explicitly retain an AES-GCM encrypted original when the server has a retention key configured. JD text and structured results remain persisted until the run expires or the user deletes them. Resume/JD text may still be sent to the selected provider during live analysis. Redaction is best-effort, not compliance-grade anonymization.

## Git Hygiene

The repo ignores local secrets, virtual environments, logs, tracker data, and generated reports. Do not commit `.env`, `.streamlit/secrets.toml`, real resumes, or private job application data.

## License

Copyright (c) 2026 Sarth.

This project is source-available for portfolio review only. Reuse, redistribution, sublicensing, or commercial use is not permitted without written permission. See [LICENSE](LICENSE).
