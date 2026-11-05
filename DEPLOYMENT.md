# Deployment Guide

TruthFit Resume AI currently has one public demo and one separately deployable product stack.

The repo now contains two runnable interfaces:

- Streamlit v1 at `app.py` is the temporary **Legacy Demo** during the product deployment transition.
- The Next.js frontend at `apps/web`, backed by FastAPI at `apps/api`, is verified locally and is not served by the Streamlit URL.

The product path includes reliability, ownership, lifecycle, privacy, schema, API-hardening, and production-verification phases. FastAPI validates Supabase access tokens, scopes records to the verified account, stores redacted resume text by default, and moves production provider work to Redis/RQ. Durable environments also require the current Alembic head revision before API startup.

```mermaid
flowchart LR
    visitor["Portfolio visitor"] --> streamlit["Public Streamlit v1 demo"]
    user["Product user"] --> web["Next.js frontend"]
    web --> auth["Supabase Auth"]
    web --> api["FastAPI API"]
    api --> postgres[("PostgreSQL")]
    api --> redis[("Private TLS Redis")]
    redis --> worker["RQ worker"]
    worker --> providers["LLM providers"]
    scheduler["Retention scheduler"] --> api
```

Deploying Streamlit does not deploy the Next.js/FastAPI product. Those services need separate public hosts and environment configuration.

## Streamlit Cloud

1. Push this project to GitHub.
2. Go to Streamlit Cloud and create a new app from the repository.
3. Set the main file path to:

```text
app.py
```

4. Add optional secrets in Streamlit Cloud only if you want to provide hosted provider keys:

```toml
GEMINI_API_KEY = ""
ANTHROPIC_API_KEY = ""
OPENAI_API_KEY = ""
PERPLEXITY_API_KEY = ""
```

5. Deploy.

For a public portfolio deployment, the safest setup is to avoid hosted keys and let visitors enter their own API key in the sidebar.

## Hugging Face Spaces

1. Create a new Space.
2. Choose the Streamlit SDK.
3. Upload this repository.
4. Keep `app.py` at the project root.
5. Add secrets in Space settings only if you want hosted provider keys.

## API and Database Deployment

The Streamlit app can still run by itself for portfolio use. The FastAPI backend verifies Supabase access tokens and scopes persisted records to the authenticated user. Configure Supabase, the database, and migrations before starting the API:

```bash
uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

For PostgreSQL persistence, set:

```text
DATABASE_URL=postgresql+psycopg://user:password@host:5432/truthfit
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_AUDIENCE=authenticated
TRUTHFIT_ANALYSIS_QUEUE=rq
REDIS_URL=rediss://your-private-redis-host:6379/0
TRUTHFIT_DAILY_ANALYSIS_QUOTA=5
TRUTHFIT_RETENTION_DAYS=30
TRUTHFIT_PENDING_RETENTION_DAYS=1
TRUTHFIT_FAILED_RETENTION_DAYS=7
TRUTHFIT_CLEANUP_ENABLED=true
TRUTHFIT_RETENTION_ENCRYPTION_KEY=base64-encoded-32-byte-key
```

Use the same database URL for both the migration process and API process. Alembic loads the repository root `.env`, while an explicitly exported environment variable takes precedence. See [database setup](docs/api.md#database) for PowerShell instructions and handling an existing database.

Then run:

```bash
alembic upgrade head
```

The repository already contains versioned Alembic migrations under `alembic/versions/` and a development seed command at `scripts/seed_database.py`.

If `DATABASE_URL` is not set, the API uses local SQLite at `.truthfit/truthfit.db`, which is useful for development but not for production hosting.

Run one or more analysis workers separately from the API web process:

```bash
rq worker --url "$REDIS_URL" truthfit-analysis
```

Local development can keep `TRUTHFIT_ANALYSIS_QUEUE=background` and does not need Redis. Public RQ deployments use server-managed provider credentials; browser-provided keys are rejected and are not placed in Redis payloads. Use private TLS Redis with authentication regardless.

Run retention cleanup daily through the hosting platform's scheduler or cron service:

```bash
python scripts/cleanup_expired_data.py
```

The repository also includes `.github/workflows/retention-cleanup.yml`. To use it, add the hosted PostgreSQL connection string as the GitHub Actions secret `TRUTHFIT_PRODUCTION_DATABASE_URL`. Optional repository variables `TRUTHFIT_RETENTION_DAYS`, `TRUTHFIT_PENDING_RETENTION_DAYS`, and `TRUTHFIT_FAILED_RETENTION_DAYS` override the workflow defaults. The workflow skips cleanly until the database secret exists.

`TRUTHFIT_DAILY_ANALYSIS_QUOTA` limits submitted analyses per authenticated account per UTC day. The production default is `5`; set it explicitly so billing behavior is intentional. Failed and pending submissions count because they can consume provider resources. Replaying an existing idempotency key does not consume another slot.

Generate the optional retention key once and store it only in the API secret manager:

```powershell
python -c "import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

Losing or rotating this key without a re-encryption procedure makes retained originals unreadable. The key is not needed when original-resume retention is disabled.

### Authentication data versus application data

- Supabase Auth stores account identities in its managed `auth.users` table. View them in **Authentication > Users** rather than the `public` schema visualizer.
- TruthFit creates its own `users` row when an authenticated account first calls a protected API workflow.
- That application row, resumes, jobs, analyses, evidence, and tracker state are stored wherever `DATABASE_URL` points.
- A localhost URL means Supabase can authenticate the user while all TruthFit application tables remain in local PostgreSQL. Use a hosted PostgreSQL connection string for a deployed API.

## Next.js Frontend Deployment

Deploy `apps/web` to a Next.js host such as Vercel, Netlify, or a Node-capable container platform.

Set the frontend environment variable to the public API host:

```text
NEXT_PUBLIC_TRUTHFIT_API_URL=https://your-api-host
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_publishable_key
NEXT_PUBLIC_HCAPTCHA_SITE_KEY=your_hcaptcha_site_key
```

Enable hCaptcha in Supabase under Authentication > Bot and Abuse Protection and store the hCaptcha secret there. Only the hCaptcha site key belongs in the public frontend environment.

Build command:

```bash
npm run build
```

Install command:

```bash
npm ci
```

Root directory:

```text
apps/web
```

The Next.js app will not run the analysis workflow by itself; it requires the FastAPI backend and database to be deployed separately.

### Uptime and error visibility

Set these GitHub Actions repository variables after the frontend and API are deployed:

```text
TRUTHFIT_API_HEALTH_URL=https://your-api-host/health
TRUTHFIT_WEB_URL=https://your-web-host
```

`.github/workflows/uptime-monitor.yml` checks both endpoints every 30 minutes and can also be run manually. Enable GitHub Actions failure notifications for the repository so a failed check reaches the maintainer. The API emits structured, request-ID-based failure logs without document text or provider keys; retain those logs in the API host and alert on repeated `5xx`, provider-failure, and quota events. This is a basic free-tier baseline, not a replacement for centralized tracing or incident management.

In Supabase Authentication URL configuration, add the deployed frontend callback URL and password-recovery callback:

```text
https://your-web-host/auth/callback
https://your-web-host/auth/callback?next=/reset-password
```

Password-reset emails exchange their recovery code through the callback and then open `/reset-password`. Test this flow with a real email address before launch.

Before making this stack public, run the same gates used in CI: PostgreSQL integration tests, Playwright workflows, security regressions, versioned LLM evaluations, and bounded load scenarios. The commands are documented in the README testing section.

Before a production release, apply migrations and verify that a PostgreSQL backup restores into an isolated temporary database:

```powershell
alembic upgrade head
python scripts/verify_backup_restore.py
```

The drill compares row counts for the core account, resume, job, analysis, evidence, and event tables, then removes only the randomly named verification database it created.
Keep the application role restricted. When that role does not have `CREATEDB`, set
`TRUTHFIT_ADMIN_DATABASE_URL` to a temporary PostgreSQL admin connection for the drill rather than
granting database-creation rights to the running application. Remove the variable after the check.

## Privacy

Resume and job description text may be sent to the selected provider during live analysis. Do not upload sensitive documents unless you are comfortable sending that content to the selected provider.

The API stores redacted resume text by default. Original resume text is transient unless the user explicitly enables retention, in which case it is encrypted with AES-GCM. Users can delete individual analyses or all TruthFit application data from Settings. The account-data action does not delete the Supabase login identity. The frontend requires a separate consent checkbox before sending redacted documents to a provider. Retention cleanup must be scheduled through the deployment platform or the included GitHub Actions workflow. Streamlit's session-only analysis and local JSON tracker remain separate.
