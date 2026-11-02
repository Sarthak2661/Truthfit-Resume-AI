# FastAPI Backend

The API backend lives in `apps/api` and can run independently from Streamlit. Phase 0 production safeguards, Phase 1 authentication/ownership, the Phase 2 durable analysis lifecycle, and Phase 3 privacy controls are implemented.

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
| `DELETE` | `/analysis/{run_id}` | Delete one owned analysis and orphaned resume/job records. |
| `GET` | `/account/data` | Inspect owned record counts, retained-original count, and retention period. |
| `DELETE` | `/account/data` | Delete all TruthFit application data for the authenticated account. |
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
TRUTHFIT_RETENTION_DAYS=30
TRUTHFIT_PENDING_RETENTION_DAYS=1
TRUTHFIT_FAILED_RETENTION_DAYS=7
TRUTHFIT_CLEANUP_ENABLED=true
TRUTHFIT_RETENTION_ENCRYPTION_KEY=base64-encoded-32-byte-key
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

- Redaction is heuristic and can miss unusual names, addresses, or resume layouts.
- Job descriptions and structured analysis results are stored until deletion or expiry.
- Deleting application data does not remove the corresponding Supabase Auth identity.
- A deployment scheduler must invoke the cleanup command; the API process does not run its own scheduler.
- Rate limits, managed quotas, and provider-cost controls remain future work.

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

Production RQ analysis uses server-managed provider credentials. The API rejects browser-provided keys in RQ mode and strips key fields before enqueueing. Local background mode can use a temporary browser key, which remains in process memory for the duration of that request.

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

### Phase 3 local upgrade

Back up an existing database before applying revision `0003_privacy_and_retention`. The migration intentionally clears legacy `resumes.parsed_text` values because that column may contain unencrypted originals; existing `redacted_text` and analysis results remain available.

Add the retention settings from `.env.example`, then run:

```powershell
cd "C:\path\to\Truthfit-Resume-AI"
.\.codex-run-venv\Scripts\python.exe -m alembic upgrade head
.\.codex-run-venv\Scripts\python.exe -m uvicorn apps.api.app.main:app --reload --port 8000
```

Only generate `TRUTHFIT_RETENTION_ENCRYPTION_KEY` if encrypted-original retention will be offered:

```powershell
.\.codex-run-venv\Scripts\python.exe -c "import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

Store that value in the API environment, never in Git. Restart FastAPI and Next.js after changing environment variables.

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

- Successful analysis runs persist redacted resume text, filename, JD text, authenticated owner, result JSON, evidence rows, and lifecycle events. Parse-only endpoints do not persist uploads.
- Original resume text remains transient by default. When `retain_original_resume=true`, it is encrypted with AES-GCM using `TRUTHFIT_RETENTION_ENCRYPTION_KEY`; plaintext is never written to the resume table.
- Saved runs survive API restarts when the same database is retained. The Next.js dashboard uses `/analysis` and `/dashboard/summary` to show recent runs without rerunning the model.
- The verified JWT `sub` claim maps to `users.auth_subject`. Client payloads cannot choose an email or owner. Run lookup, history, dashboard aggregation, and tracker updates all include `user_id`; cross-user IDs return `404`.
- Failed provider calls persist a failed run and an independent failure event. They are excluded from completed-score averages.
- Users can inspect record counts, delete one owned run, or delete all TruthFit application data. Cross-account deletion returns `404`.
- `expires_at` is set per lifecycle state. Run `python scripts/cleanup_expired_data.py` from a daily scheduler to remove expired runs and orphaned resume/job records.
- The Streamlit app still uses session analysis state and its separate local JSON tracker. It does not use the API database.
- Automated API tests use SQLite and mocked provider responses. They do not verify a live PostgreSQL deployment or live provider calls.
