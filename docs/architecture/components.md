# Components

> Source of truth: `docs/architecture/index.md` (naming mirrors files in `src/`).

## Graph data model (the HydraDB schema)

Node labels and edge types (implemented as HydraDB `CREATE`/`MERGE` statements — see
`docs/product/glossary.md` for the domain vocabulary):

```
(:Service {id, name})                      internal services we protect
(:Lockfile {id, app, created_at, resolved_at})
(:PackageVersion {id, name, version, published_at, valid_until, deprecated,
                  popular, malicious, advisory_id, is_typosquat})
(:Developer {id, handle, email})

(Service)-[:USES_LOCKFILE {since}]->(Lockfile)
(Lockfile)-[:RESOLVES_TO {at}]->(PackageVersion)   // resolved_at is the edge timestamp
(PackageVersion)-[:DEPENDS_ON {pinned, valid_from, valid_until}]->(PackageVersion)  // dependant -> dependency
(PackageVersion)-[:MAINTAINED_BY {since}]->(Developer)
```

Invariants:
- Every edge has a `valid_from`; temporal versions get `valid_until` (sentinel `9999999999` = live).
- `malicious`, `popular`, `is_typosquat`, `deprecated` are booleans we filter with `= true`.
- No `DELETE` during normal operation for advisory data — deprecation is a `SET` on `valid_until`.

## Component responsibilities

### `src/hydradb_client.py`
- `constructor(host, port, token)`; `query(cypher, params) -> QueryResult {rows, elapsed_ms}`.
- Uses stdlib `urllib`/`requests` against `POST /v1/graphs/default/query`.
- Raises `HydraDBError` with the server message on a failed query; never returns partial rows silently.
- Exposes `healthz()`, `metrics()` (latency + cost telemetry).

### `src/graph_service.py` (pure, unit-testable)
Parameterized Cypher builders for the five core questions, plus `fetch_subgraph(node_id, depth)`.
Exact queries are pinned in `docs/product/features.md` and validated against the live container.

### `src/intent.py` (Researcher persona)
- Deterministic classifier: keyword/entity patterns → intent class (`BLAST_RADIUS`, `EXPOSED_SERVICES`,
  `RESOLVED_WHILE_LIVE`, `MAINTAINER_CONTAGION`, `TYPOSQUAT_CANDIDATES`, `PACKAGE_LOOKUP`, `UNSUPPORTED`).
- Optional LLM refinement produces a stricter param set only when configured and available.
- Output is a `QueryPlan` (list of query builders + params) — never free text.

### `src/adjudicate.py` (Auditor + Adjudicator personas)
- Auditor: runs the plan; checks **subgraph density** (nodes/edges present), **temporal consistency**
  (e.g. resolved_at within advisory window), and **contradictions** (conflicting facts for same entity).
- Adjudicator: emits `Verdict {answer, evidence_chain[], abstain:bool, reason}`.
- Abstains when: empty/low-density evidence, out-of-vocabulary intent, or confidence below threshold.

### `src/models.py`
Pydantic models for `QueryPlan`, `QueryResult`, `Evidence`, `Verdict`, telemetry.

### `app.py` (Streamlit console)
Renders per DESIGN.md: mono type, cream canvas, hairline sections, dark "console" panel showing the
live Cypher, semantic colors for verdicts, Plotly subgraph, thought-process panel, latency/cost badges.

## Scripts
- `scripts/gen_dataset.py` — deterministic ecosystem generator + `ground_truth.json`.
- `scripts/ingest.py` — `UNWIND` batch loader; idempotent.
- `scripts/eval.py` — held-out advisory precision/recall, latency, cost → `docs/research/scoring.md`.
- `scripts/smoke.sh` — health check + round-trip smoke test (evidence capture).
- `src/infra/hydradb-up.sh` — starts the HydraDB container with the documented env contract.