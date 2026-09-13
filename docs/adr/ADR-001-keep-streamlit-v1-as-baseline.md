# ADR-001: Keep Streamlit v1 as the Baseline

## Status

Accepted

## Context

TruthFit already has a working Streamlit deployment, sample mode, provider integrations, tests, and portfolio documentation. The phase-wise plan proposes a larger FastAPI, PostgreSQL, Next.js, Redis, Docker, Kubernetes, and observability platform.

## Decision

Keep the current Streamlit app as the v1 baseline while building the v2 platform incrementally.

## Consequences

- The public app remains available while architecture work continues.
- Future API/frontend work can be compared against a known working product.
- The repo should avoid empty scaffold folders that imply unfinished services are implemented.
- Documentation must clearly separate current functionality from planned v2 work.
