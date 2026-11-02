# FastAPI Backend

The API backend lives in `apps/api` and can run independently from Streamlit. Phase 0 production safeguards, Phase 1 authentication/ownership, and the Phase 2 durable analysis lifecycle are implemented.

## Run Locally

```bash
uvicorn apps.api.app.main:app --reload
```

OpenAPI and Swagger UI are available at:

- `http://127.0.0.1:8000/openapi.json`
- `http://127.0.0.1:8000/docs`

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Health check for deployment and smoke testing. |
| `POST` | `/resumes/parse` | Parse a resume upload and return original plus redacted text. |
| `POST` | `/jobs/parse` | Parse a job description upload, pasted JD text, and optional job link. |
| `POST` | `/analysis/run` | Create a pending analysis and return `202 Accepted` with a run ID and status URL. |
| `GET` | `/analysis` | List recent saved analyses for dashboard/history views. |
| `GET` | `/analysis/{run_id}` | Retrieve a saved analysis, status, provider/model, and overall score from the database. |
| `POST` | `/tailor` | Return resume tailoring sections from an existing analysis or a fresh run. |
| `GET` | `/providers` | List supported LLM providers, models, and defaults. |
| `GET` | `/dashboard/summary` | Return recent analyses, average score, common gaps, provider usage, and failed-run counts. |
| `GET` | `/tracker` | List the authenticated account's tracked opportunities. |
| `POST` | `/tracker/{run_id}` | Save status, priority, dates, and notes for an owned analysis. |

## Service Boundaries

Routes call service modules instead of embedding business logic directly:

- `apps/api/app/routes.py` handles HTTP request/response wiring.
- `apps/api/app/services/parse_service.py` adapts FastAPI uploads to the existing loaders and redaction service.
- `apps/api/app/services/analysis_service.py` runs analysis, normalizes output, applies evidence scoring, stores runs, and returns tailoring sections.
- `apps/api/app/analysis_queue.py` dispatches work to a local background task or Redis/RQ.
- `apps/api/app/tasks.py` is the worker entry point for provider-backed analysis.
- `source/ai`, `source/loaders`, and `source/services` remain the shared business logic used by both Streamlit and the API.

## Frontend

The Next.js frontend lives in `apps/web` and calls this backend through `NEXT_PUBLIC_TRUTHFIT_API_URL`.

Development defaults to `http://127.0.0.1:8000`. Production builds require an explicit absolute HTTP(S) URL and fail when it is missing or invalid.

```bash
cd apps/web
npm install
npm run dev
```

Open `http://127.0.0.1:3000` after the FastAPI backend is running.

## Runtime Configuration

Local development permits the Next.js origins automatically. Production requires explicit origins:

```bash
TRUTHFIT_ENV=production
TRUTHFIT_ALLOWED_ORIGINS=https://app.example.com
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_AUDIENCE=authenticated
NEXT_PUBLIC_TRUTHFIT_API_URL=https://api.example.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_publishable_key
TRUTHFIT_ANALYSIS_QUEUE=rq
REDIS_URL=rediss://your-private-redis-host:6379/0
```

`TRUTHFIT_ALLOWED_ORIGINS` accepts a comma-separated list of complete HTTP(S) origins. Wildcards, paths, query strings, and malformed origins are rejected. All resume, job, analysis, tailoring, dashboard, and tracker routes require a Supabase access token. `/health` and `/providers` remain public.

## Authentication and ownership

- The Next.js client signs users in through Supabase Auth.
- FastAPI verifies the Supabase JWT signature, issuer, audience, expiry, and `sub` claim.
- The verified `sub` maps to `users.auth_subject`; request payloads cannot select an owner.
- Resume parsing, JD parsing, analysis, history, dashboard, tailoring, and tracker routes require authentication.
- Repository reads and writes include the resolved application `user_id`. A valid record ID owned by another account returns `404`.
- Supabase login identities live in the managed `auth.users` table. TruthFit's `users` table lives in the database selected by `DATABASE_URL` and is created on the account's first protected API workflow.

## Current Limitations

- The API persists users, resumes, jobs, analysis runs, evidence rows, and agent events through SQLAlchemy.
- Rate limits, hosted key controls, retention, and account deletion are planned for later phases.
- Live analysis still depends on the selected provider API key and provider availability.

## Analysis Lifecycle

1. `POST /analysis/run` validates the provider/model, creates the resume, job, and `pending` run, commits them, and returns `202 Accepted`.
2. A worker changes the run to `processing` in a short transaction.
3. The provider call runs without an open database transaction.
4. A separate transaction stores either the completed result and evidence or a typed failure and failure event.
5. Clients poll `GET /analysis/{run_id}` until the status is `completed` or `failed`.

Development defaults to `TRUTHFIT_ANALYSIS_QUEUE=background` and requires no Redis service. Production defaults to `rq`; set `REDIS_URL` and start a worker:

```bash
rq worker --url "$REDIS_URL" truthfit-analysis
```

RQ payloads can include a temporary bring-your-own provider key. Use private TLS Redis, short queue/result retention, and access controls. A later hosted-key gateway should remove client keys from queued payloads entirely.

## Database

Set `DATABASE_URL` for PostgreSQL:

```bash
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/truthfit
```

If `DATABASE_URL` is not set, the API uses a local SQLite database at `.truthfit/truthfit.db` for development.

Run migrations:

```bash
alembic upgrade head
```

Seed demo data:

```bash
python scripts/seed_database.py
```

The seed script uses synthetic data without a provider call and prints a run ID. Set `TRUTHFIT_SEED_AUTH_SUBJECT` to your Supabase user ID if you want the seeded run to appear in your authenticated account. Each invocation creates a new resume, job, and analysis run.

Alembic loads the repository root `.env`. You can override it by exporting `DATABASE_URL` for both Alembic and the API. For PowerShell:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/truthfit"
python -m alembic upgrade head
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

Run migrations on a fresh database before starting the API. API startup also creates missing tables with SQLAlchemy `create_all`, but does not apply migrations or stamp the Alembic version. For an existing database created this way, verify that its schema matches the initial migration before stamping `0001_create_truthfit_tables`; do not blindly rerun the initial create-table migration.

### Storage and access boundaries

- Successful analysis runs persist the original and redacted resume text, filename, JD text, authenticated owner, result JSON, evidence rows, and completion event. Parse-only endpoints do not persist uploads.
- Saved runs survive API restarts when the same database is retained. The Next.js dashboard uses `/analysis` and `/dashboard/summary` to show recent runs without rerunning the model.
- The verified JWT `sub` claim maps to `users.auth_subject`. Client payloads cannot choose an email or owner. Run lookup, history, dashboard aggregation, and tracker updates all include `user_id`; cross-user IDs return `404`.
- Failed provider calls persist a failed run and an independent failure event. They are excluded from completed-score averages.
- The Streamlit app still uses session analysis state and its separate local JSON tracker. It does not use the API database.
- Automated API tests use SQLite and mocked provider responses. They do not verify a live PostgreSQL deployment or live provider calls.
