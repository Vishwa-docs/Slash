# ADR-0007 — Bounded traversals (`*1..6`), never unbounded closure

- **Status:** accepted
- **Date:** 2026-08-19
- **Owner:** team
- **Links:** `docs/architecture/hydradb-notes.md` (var-length paths must be bounded)

## Context
HydraDB requires bounded variable-length paths and patterns are single-type directed. Unbounded
community detection / closure is not expressible.

## Decision
- All variable-length traversals are bounded: `[:DEPENDS_ON*1..6]` is our ceiling ("captures
  realistic transitive exposure within the demo dataset; deeper hops are rare and slower").
- The product makes the hop ceiling explicit in every evidence chain and in the UI when it is hit.
- Where a deeper fan-out is needed, compose multiple bounded queries and union the results,
  with a hard query budget.

## Consequences
- No unbounded queries in production paths → predictable latency and cost.
- Scoring is honest about the 6-hop ceiling (documented in `docs/research/scoring.md`).