# ADR-004: Centralize Provider Routing and Fallback

## Status

Accepted for v1, expandable for v2

## Context

TruthFit supports multiple LLM providers and already handles retry/fallback behavior. Silent fallback can make results hard to reproduce.

## Decision

Keep provider selection, fallback, model metadata, timeout handling, and fallback logging in the provider layer rather than scattering it through pages.

## Consequences

- UI code stays focused on product flow.
- Provider behavior is easier to test.
- Fallback events can be logged and surfaced more clearly over time.
- v2 can expand this into a full LLM gateway with provider health, usage caps, and routing rules.
