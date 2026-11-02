# Deployment Guide

TruthFit Resume AI can be deployed on Streamlit Cloud or Hugging Face Spaces.

The repo now contains two runnable interfaces:

- Streamlit v1 at `app.py`
- Next.js frontend at `apps/web`, backed by the FastAPI API at `apps/api`

The product path includes Phase 0 reliability controls, Phase 1 authentication/ownership, and the Phase 2 durable analysis lifecycle. FastAPI validates Supabase access tokens, scopes persisted records to the verified account, and moves production provider work to Redis/RQ.

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
```

Use the same database URL for both the migration process and API process. Alembic loads the repository root `.env`, while an explicitly exported environment variable takes precedence. See [database setup](docs/api.md#database) for PowerShell instructions and handling an existing database.

Then run:

```bash
alembic upgrade head
```

If `DATABASE_URL` is not set, the API uses local SQLite at `.truthfit/truthfit.db`, which is useful for development but not for production hosting.

Run one or more analysis workers separately from the API web process:

```bash
rq worker --url "$REDIS_URL" truthfit-analysis
```

Local development can keep `TRUTHFIT_ANALYSIS_QUEUE=background` and does not need Redis. Public deployments should use private TLS Redis with authentication. The current BYOK flow places the temporary provider key in the queued job payload, so restrict Redis access and keep job/result retention short.

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

## Privacy

Resume and job description text may be sent to the selected provider during live analysis. Do not upload sensitive documents unless you are comfortable sending that content to the selected provider.

The API stores original and redacted resume text, JD text, authenticated owner, results, and evidence on successful analyses. Ownership is enforced, but encryption, retention, and account-deletion controls still need to be configured before using sensitive real-world data. Streamlit's session-only analysis and local JSON tracker remain separate from this database.
