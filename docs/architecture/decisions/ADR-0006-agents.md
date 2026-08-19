# ADR-0006 — Deterministic intent router with optional LLM refinement

- **Status:** accepted
- **Date:** 2026-08-19
- **Owner:** team
- **Links:** `docs/architecture/components.md` (`src/intent.py`), `docs/architecture/index.md` (principles)

## Context
The GDELT winner used an LLM planner (ReWOO). For reliability, cost, and a no-key demo we want the
product to work deterministically; the "multi-agent" story must still be real enough to show.

## Decision
- **Researcher** = deterministic classifier over normalized text (entities + verbs) → one of six
  intent classes; produces a parameterized `QueryPlan`. No LLM required.
- **Optional refine** = if an LLM is configured, it may re-parameterize an already-classified plan
  (e.g. disambiguate a package name) using strictly schemas validated by Pydantic. It can never
  change intent class or invent queries.
- **Auditor** = evidence checks: subgraph density, temporal consistency, contradiction.
- **Adjudicator** = verdict or abstention, always attaching the evidence chain.

## Consequences
- Tests can assert intent classification and abstention behavior without any API key.
- The UI "thought process" panel shows Researcher → Auditor → Adjudicator traces; when LLM is off,
  the trace says "deterministic path".
- Token cost is always rendered; budget caps exist.