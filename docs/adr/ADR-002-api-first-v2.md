# ADR-002: Extract an API Boundary Before Rebuilding the Frontend

## Status

Proposed

## Context

The current app is Streamlit-first. A React or Next.js frontend would improve product polish, but it should not be built on unstable analysis contracts.

## Decision

Build a FastAPI backend before moving to a Next.js frontend.

## Consequences

- Resume parsing, job parsing, redaction, scoring, provider calls, and report generation become reusable services.
- The frontend can be rebuilt against documented API contracts.
- API tests can validate behavior without depending on Streamlit rendering.
- This adds some duplication risk during migration, so shared service code should be extracted carefully.
