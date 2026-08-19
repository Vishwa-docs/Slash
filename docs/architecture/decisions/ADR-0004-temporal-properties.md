# ADR-0004 — Time is data: temporal edges via properties + sentinels

- **Status:** accepted
- **Date:** 2026-08-19
- **Owner:** team
- **Links:** `docs/architecture/hydradb-notes.md` (WHERE restrictions)

## Context
The strategy claims HydraDB is "temporal-first". At the API level, temporal versioning is **not**
a documented first-class query feature; HydraDB's `WHERE` supports only `= <> < > <= >=` and
`STARTS WITH` (no `IS NULL`, `IN`, `CONTAINS`, `ENDS WITH`). We must implement time ourselves.

## Decision
- Model time as **edge/node properties**: `valid_from`, `valid_until`, `published_at`,
  `resolved_at`, `created_at`.
- "Still live" = `valid_until == 9999999999` (epoch sentinel) because `IS NULL` is unsupported.
- Deprecation never deletes: `SET r.valid_until = $ts` and add a fresh edge.
- Where a forensic question is hot ("did this lockfile resolve the bad version while live?"),
  precompute a boolean edge property at ingest (`was_resolved_while_live`) **and** keep the raw
  timestamps so the query can recompute — belt and suspenders against HydraDB quirks.

## Consequences
- All temporal filtering uses comparisons on numbers (supported).
- Ground-truth manifest and dataset generator emit these sentinels consistently.
- Abstention can fire on temporal inconsistency (e.g. resolved_at before published_at → data bug).