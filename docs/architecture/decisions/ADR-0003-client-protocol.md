# ADR-0003 — Primarily talk to HydraDB over HTTPS, fall back to Bolt

- **Status:** accepted
- **Date:** 2026-08-19
- **Owner:** team
- **Links:** `docs/architecture/hydradb-notes.md`

## Context
HydraDB exposes two wire protocols: a typed JSON/NDJSON HTTPS query API (8443) and Neo4j Bolt
(7687). We must pick a client primary.

## Considered options
| Option | Pros | Cons |
|---|---|---|
| **HTTPS query API (chosen)** | No `neo4j` driver versioning concerns; simple `requests`-style calls; typed rows; streaming | One extra header/token detail to get right |
| Bolt (neo4j driver) | Familiar; supported by hydradb smoke scripts | Driver version churn; less debuggable from logs |
| Both | Redundancy | More surface than needed |

## Decision
`src/hydradb_client.py` uses the HTTPS JSON API as the primary path, with a Bolt path as a
drop-in fallback only if the HTTPS path fails in the live container. Both are behind one
`query()` interface so the rest of the code does not care.

## Consequences
- Auth = `Authorization: Bearer $TOKEN` + `X-Graph-Namespace: default` header.
- Smoke script asserts `GET /healthz` then a `CREATE`/`MATCH` round trip before any feature work.