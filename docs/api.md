# FastAPI Backend

The Phase 1 backend lives in `apps/api` and can run independently from Streamlit.

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
| `POST` | `/analysis/run` | Run the complete TruthFit analysis through the provider pipeline. |
| `GET` | `/analysis/{run_id}` | Retrieve a saved analysis, status, provider/model, and overall score from the database. |
| `POST` | `/tailor` | Return resume tailoring sections from an existing analysis or a fresh run. |
| `GET` | `/providers` | List supported LLM providers, models, and defaults. |

## Service Boundaries

Routes call service modules instead of embedding business logic directly:

- `apps/api/app/routes.py` handles HTTP request/response wiring.
- `apps/api/app/services/parse_service.py` adapts FastAPI uploads to the existing loaders and redaction service.
- `apps/api/app/services/analysis_service.py` runs analysis, normalizes output, applies evidence scoring, stores runs, and returns tailoring sections.
- `source/ai`, `source/loaders`, and `source/services` remain the shared business logic used by both Streamlit and the API.

## Current Limitations

- The API persists users, resumes, jobs, analysis runs, evidence rows, and agent events through SQLAlchemy.
- API authentication, rate limits, hosted key controls, and persistent user sessions are planned for later phases.
- Live analysis still depends on the selected provider API key and provider availability.

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

The seed script uses synthetic data without a provider call and prints a run ID. Start the API and request `GET /analysis/{run_id}` with that ID to inspect the saved result. Each seed invocation creates a new resume, job, and analysis run.

Export `DATABASE_URL` in the process environment for both Alembic and the API; Alembic does not load `.env` automatically. For PowerShell:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/truthfit"
python -m alembic upgrade head
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

Run migrations on a fresh database before starting the API. API startup also creates missing tables with SQLAlchemy `create_all`, but does not apply migrations or stamp the Alembic version. For an existing database created this way, verify that its schema matches the initial migration before stamping `0001_create_truthfit_tables`; do not blindly rerun the initial create-table migration.

### Storage and access boundaries

- Successful analysis runs persist the original and redacted resume text, filename, JD text, user email, result JSON, evidence rows, and completion event. Parse-only endpoints do not persist uploads.
- Saved runs survive API restarts when the same database is retained. There is no history-listing UI or endpoint yet; retrieve a run by its ID.
- `user_email` associates records with a user row but is not authentication. Omitted emails share the anonymous user. Retrieval currently has no ownership check, so keep this API in a trusted development environment until access controls are added.
- Failed analysis transactions roll back, including their failure event; durable failure history is not implemented.
- The Streamlit app still uses session analysis state and its separate local JSON tracker. It does not use the API database.
- Automated API tests use SQLite and mocked provider responses. They do not verify a live PostgreSQL deployment or live provider calls.
