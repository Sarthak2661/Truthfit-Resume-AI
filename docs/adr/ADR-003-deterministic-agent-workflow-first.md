# ADR-003: Use Deterministic Orchestration Before LangGraph

## Status

Proposed

## Context

The long-term plan includes multiple agents for requirement extraction, evidence matching, skill gaps, tailoring, and verification. Agent frameworks can help later, but they can also obscure control flow too early.

## Decision

Start with a simple Python state-machine workflow before adopting LangGraph or another orchestration framework.

## Consequences

- The workflow is easier to test, debug, and explain in interviews.
- Each step can have a clear input schema, output schema, and failure mode.
- A future framework migration remains possible after the agent contract stabilizes.
