# v1 Streamlit Baseline

This document records the current TruthFit Resume AI baseline before the larger platform migration begins.

## Implemented Features

- Resume upload and parsing for PDF, DOCX, and TXT files.
- Job description input through upload, paste, and optional job posting link.
- Upload size and PDF page-count checks.
- Privacy-aware redaction for common contact details before live provider calls.
- Multi-provider LLM configuration for Gemini, Claude, OpenAI, and Perplexity.
- Provider retry and fallback handling with privacy-safe observability logs.
- Pydantic-backed structured output validation and safe normalization before rendering.
- No-API demo report using synthetic sample data.
- Dashboard sections for overview, skills and requirements, evidence and risks, resume improvement, export, and tracking.
- Score drivers, evidence coverage, matched/missing skills table, top fixes, and resume evidence score.
- Resume improvement suggestions, grounded rewrites, project ideas, certification ideas, and optional cover letter.
- Chat helper for analysis follow-up.
- PDF report export.
- Local job tracker with dedupe behavior.
- Light and dark themes with responsive card layouts.
- FastAPI Phase 1 backend endpoints for health checks, parsing, analysis, tailoring, stored analysis lookup, and provider discovery.
- SQLAlchemy persistence for API users, resumes, jobs, analysis runs, evidence rows, and agent events.

## Current Test Coverage

The current test suite covers:

- resume and JD loader behavior
- upload validation
- JSON extraction from messy LLM output
- provider retry and fallback behavior
- observability log scrubbing
- URL validation
- job tracker save/load/dedupe behavior
- PDF report generation
- UI text cleanup
- resume proof map generation
- resume evidence scoring
- API endpoint contracts for parsing, analysis, provider listing, stored lookup, and tailoring

## Known Limitations

- The Streamlit app is single-user and session-oriented.
- The API supports PostgreSQL through `DATABASE_URL` and uses SQLite as a local development fallback.
- User identity is still lightweight; production auth/session handling is planned for a later phase.
- The job tracker stores local JSON data and is not production multi-user storage.
- Redaction is heuristic, not compliance-grade anonymization.
- Live analysis sends redacted resume/JD text to the selected external provider.
- The scoring is an explainable review score, not a real ATS simulation.
- PDF extraction can be messy for heavily designed resumes.
- The API stores completed analyses for retrieval by run ID, but there is no history-listing UI, server-side billing, rate limiting, or authentication yet.

## Baseline Rule

Keep this Streamlit version runnable while extracting the future FastAPI backend and product frontend. Architecture changes should preserve or explicitly replace each baseline feature.
