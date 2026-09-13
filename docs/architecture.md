# TruthFit Architecture

TruthFit is currently a Streamlit-first portfolio application with an extracted FastAPI backend slice. The codebase is intentionally kept small enough to run from one public deployment, while the core logic is separated into loaders, AI providers, services, API routes, UI modules, and page modules.

## Current Architecture

```mermaid
flowchart LR
    resume["Resume upload<br>PDF / DOCX / TXT"] --> loaders["Text loaders<br>source/loaders"]
    jd["Job description<br>paste, upload, or link"] --> loaders
    links["Project notes<br>and links"] --> prompt["Prompt builder<br>source/ai/prompts.py"]
    api["FastAPI routes<br>apps/api"] --> api_services["API services<br>parse / analysis / tailor"]
    api_services --> loaders
    api_services --> prompt
    loaders --> validation["Upload validation<br>size and page checks"]
    validation --> redaction["Privacy-aware redaction"]
    redaction --> prompt
    prompt --> providers["Provider clients<br>Gemini / Claude / OpenAI / Perplexity"]
    providers --> schema["Structured result validation<br>Pydantic schemas"]
    schema --> services["Evidence, scoring, tracker,<br>report, observability services"]
    api_services --> db["SQLAlchemy persistence<br>users / resumes / jobs / runs / evidence / events"]
    db --> api_services
    services --> api_services
    services --> pages["Streamlit pages<br>Home / Analyze / Dashboard / Chat / Tracker"]
```

## Current Boundaries

- `app.py` owns Streamlit bootstrapping, session state, theme state, provider settings, and top-level page routing.
- `apps/api/` exposes the Phase 1 FastAPI backend with parse, analysis, tailoring, health, and provider endpoints.
- `apps/api/app/db/` contains the Phase 2 SQLAlchemy models, database session management, and repositories.
- `source/pages/` contains user-facing page flows.
- `source/loaders/` validates and extracts resume/JD text.
- `source/ai/` builds prompts, calls LLM providers, validates structured output, and handles retry/fallback behavior.
- `source/services/` contains product logic that is not page-specific: evidence scoring, proof mapping, PDF export, job tracking, URL validation, sample reports, and observability.
- `source/ui/` contains reusable cards, charts, tables, layout helpers, text cleanup, and styles.
- `tests/` covers loaders, provider fallback, observability, scoring, report generation, tracker behavior, URL handling, and UI cleanup.

## Target Platform Architecture

The phase plan moves TruthFit toward a production-style platform:

```mermaid
flowchart TB
    web["Next.js frontend"] --> api["FastAPI backend"]
    api --> auth["Auth and sessions"]
    api --> db["PostgreSQL<br>users, resumes, jobs, analyses, evidence"]
    api --> orchestrator["Agent orchestrator"]
    orchestrator --> job_agent["Job requirement agent"]
    job_agent --> evidence_agent["Resume evidence agent"]
    evidence_agent --> gap_agent["Skill gap agent"]
    gap_agent --> tailor_agent["Tailoring agent"]
    tailor_agent --> verify_agent["Verification agent"]
    verify_agent --> gateway["LLM gateway"]
    gateway --> gemini["Gemini"]
    gateway --> openai["OpenAI"]
    gateway --> claude["Claude"]
    gateway --> redis["Redis<br>cache, rate limits, task state"]
    api --> metrics["Prometheus metrics"]
    metrics --> grafana["Grafana dashboards"]
```

## Migration Principle

Do not replace the working Streamlit app all at once. Preserve v1 as the public demo, then extract one stable API boundary at a time:

1. Keep the FastAPI backend and SQLAlchemy persistence passing tests while the Streamlit app remains the public demo.
2. Replace the local SQLite development fallback with managed PostgreSQL in deployed API environments.
3. Replace Streamlit UI with a Next.js frontend only after the backend contract is stable.
4. Add Redis, Docker, observability, Kubernetes, and Terraform after the core product behavior is proven.
