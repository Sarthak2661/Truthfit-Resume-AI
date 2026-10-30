# Deployment Guide

TruthFit Resume AI can be deployed on Streamlit Cloud or Hugging Face Spaces.

The repo now contains two runnable interfaces:

- Streamlit v1 at `app.py`
- Next.js frontend at `apps/web`, backed by the FastAPI API at `apps/api`

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

The Streamlit app can still run by itself for portfolio use. The FastAPI backend is currently suitable for trusted development use: authentication and record ownership checks are not implemented. Configure the database and run migrations before starting the API:

```bash
uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

For PostgreSQL persistence, set:

```text
DATABASE_URL=postgresql+psycopg://user:password@host:5432/truthfit
```

Set this as an environment variable for both the migration process and API process. Alembic does not automatically load `.env`. See [database setup](docs/api.md#database) for PowerShell instructions and handling an existing database.

Then run:

```bash
alembic upgrade head
```

If `DATABASE_URL` is not set, the API uses local SQLite at `.truthfit/truthfit.db`, which is useful for development but not for production hosting.

## Next.js Frontend Deployment

Deploy `apps/web` to a Next.js host such as Vercel, Netlify, or a Node-capable container platform.

Set the frontend environment variable to the public API host:

```text
NEXT_PUBLIC_TRUTHFIT_API_URL=https://your-api-host
```

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

The API also stores original and redacted resume text, JD text, user email, results, and evidence on successful analyses. Configure database access, backups, and retention before using real data. Streamlit's session-only analysis and local JSON tracker remain separate from this database.
