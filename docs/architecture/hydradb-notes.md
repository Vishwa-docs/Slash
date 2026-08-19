# HydraDB — Verified Notes for Slash

> Source of truth: `hydradb/README.md`, `hydradb/cypher-compat.md`, `hydradb/scripts/runtime_smoke.sh`
> (all in the sibling `hydradb/` repo), plus **live verification against the running container**.
> This file records what we depend on. **If you observe different behavior, update this file.**
> For a structural map of the HydraDB codebase, see `docs/research/hydradb-context-graph/GRAPH_REPORT.md`.

## What HydraDB is
- A **graph database built on object storage** (SlateDB WAL/SST on S3-compatible object storage:
  `aws`, `azure`, `gcp`, `local`, `memory`). `graph-node` (queries/mutations) and `graph-indexer`
  (background index builds) are stateless compute with disposable caches.
- Written in Rust. We interact with it **only** through its wire APIs — we never touch its source.

## How to run it (primary path: Docker)
```bash
docker pull ghcr.io/hydra-db/hydradb:latest
mkdir -p .hydradb/store .hydradb/cache
printf '%s\n' "$(openssl rand -hex 16)" > .hydradb/auth.token
docker run --rm -d --name slash-hydra \
  --user "$(id -u):$(id -g)" \
  -v "$PWD/.hydradb:/var/hydradb" \
  -e CLOUD_PROVIDER=local \
  -e LOCAL_PATH=/var/hydradb/store \
  -e GRAPH_NAMESPACE=default \
  -e GRAPH_ID=default \
  -e GRAPH_CELL_ID=cell-0 \
  -e GRAPH_CELLS=cell-0 \
  -e GRAPH_NODE_ID=node-0 \
  -e GRAPH_BOLT_NODE_ADDRESSES=node-0=127.0.0.1:7687 \
  -e GRAPH_ADVERTISED_BOLT_ADDR=127.0.0.1:7687 \
  -e GRAPH_DATA_CACHE_DIR=/var/hydradb/cache \
  -e GRAPH_AUTH_TOKEN_FILE=/var/hydradb/auth.token \
  -e GRAPH_ALLOW_PLAINTEXT=true \
  -e RUST_MIN_STACK=33554432 \
  -p 7687:7687 -p 8443:8443 -p 9090:9090 \
  ghcr.io/hydra-db/hydradb:latest
```
The auth token file must contain a token on one line (≥32 chars). Generate it before starting the container.
The container runs as UID/GID `10001`; `--user "$(id -u):$(id -g)"` is required so it can write the
bind-mounted store/cache (owned by the host user). Ports: **Bolt 7687 · HTTP 8443 · admin/metrics 9090**.
Default up/teardown is `src/infra/hydradb-up.sh` / `docker stop slash-hydra`.

### Verified deviations from earlier drafts (Phase 1, live)
- `GRAPH_CELLS` must **contain** `GRAPH_CELL_ID`; `GRAPH_CELLS=1` (integer) is rejected at startup with
  `GRAPH_CELLS must contain GRAPH_CELL_ID`. Use `GRAPH_CELLS=cell-0`, `GRAPH_NODE_ID=node-0`,
  `GRAPH_BOLT_NODE_ADDRESSES=node-0=127.0.0.1:7687`.
- HTTP body carries params under **`parameters`** — the key `params` is ignored and the query fails with
  `missing OpenCypher query parameter $name`.
- `GET /healthz` is verified live on the public HTTP port (8443); `GET /admin/readyz` on 9090.

## Two APIs we can use
1. **HTTPS query API** (primary — simple, no driver dependency):
   ```
   POST http://127.0.0.1:8443/v1/graphs/default/query
   Authorization: Bearer <TOKEN>
   X-Graph-Namespace: default
   {"cell_id": "cell-0", "query": "<opencypher>", "consistency": "causal"}
   ```
   Returns typed JSON; streaming NDJSON is also available. `GET /healthz` (public) and
   `GET /admin/readyz`, `GET /metrics` (admin) on 9090.
2. **Neo4j Bolt 5.x** on 7687 — any official `neo4j` Python driver works
   (`neo4j://127.0.0.1:7687`, auth token as password). Used by `hydradb/scripts/runtime_smoke.sh`.

## OpenCypher subset we must live within
From `hydradb/cypher-compat.md` (verified by hydradb's own smoke tests):

- **MATCH** — single relationship type per pattern, **directed** edges only.
- **WHERE** — only `=`, `<>`, `<`, `>`, `<=`, `>=`, `STARTS WITH`.
  **No `IN`, `ENDS WITH`, `CONTAINS`, `IS NULL`, `IS NOT NULL`.**
  (Workaround: encode booleans/flags as properties and compare `= true/false`; encode
  "no end date" as a sentinel epoch instead of NULL.)
  (Live: a *node-only* MATCH needs an id/label/property predicate in the pattern itself —
  `MATCH (n) WHERE n.id = $id` is rejected with `node-only MATCH requires an id, label, or property predicate`.)
- **RETURN** — aggregates `count/sum/avg/collect`; **no `RETURN *`**.
  Aggregates must target a property expression (`count(n.id)`, `collect(b.id)`); `count(n)` on a bare
  binding is rejected with `property values support integer, float, boolean, and string literals`.
- **WITH** — pass-through only. **ORDER BY / SKIP / LIMIT** supported.
- **UNION / UNION ALL** supported.
- **Variable-length paths** `[:TYPE*1..3]` — **must be bounded** (we use `*1..6` as our ceiling).
- **Writes**: `CREATE`, `MERGE` (by node `id`; no `ON CREATE`/`ON MATCH`), `SET`, `REMOVE`,
  `DELETE` / `DETACH DELETE`.
  (Live: `CREATE` supports one or more **one-hop relationship paths** only — a bare `CREATE (n {…})`
  is rejected. `DETACH DELETE` reliably removes a node when its MATCH pattern carries a **label**
  (`MATCH (n:Label {id: $id}) DETACH DELETE n`); an unlabeled node-only delete left the node behind.)
- **Bulk load**: `UNWIND $rows AS row ... MERGE ...` — our main ingestion path.
- **Path procedures**: `CALL algo.SPpaths` (single source→target), `algo.SSpaths` (single source),
  `algo.MSpaths` (multi-source) → `path`, `pathWeight`, `pathCost`.
- Nodes are matched by integer `id` property; params are `$name`; node ids are non-negative ints.
- `EXPLAIN` (read-only query validation) exists via `explain_opencypher_rows`.

### Implications for our schema
- Because patterns are **directed**, model every relationship directionally so the query we
  hotly depend on is a *forward* match. Our blast radius reads `(up)-[:DEPENDS_ON*1..6]->(bad)`,
  i.e. edges point from dependant → dependency.
- No `IS NULL` → represent temporal openness as `valid_until_year = 9999` (sentinel) and filter
  `= 9999` for "still live".
- No `IN` → for "package in the advisory set", match by `name + version` equality per advisory,
  or tag the node with `advisory_id` on ingest.
- Aggregates `collect` let us fetch the exposed-service set in one query; `count` gives blast size.

## Temporal modeling (our convention, implemented in properties)
The strategy says HydraDB is "temporal-first" — at the API level we implement it ourselves:
- Facts carry `valid_from` / `valid_until` (epoch) as **edge or node properties**.
- On contradiction, the old edge's `valid_until` is set and a new edge is created — never delete.
- "Resolved while live": `Lockfile.resolved_at` must fall inside
  `published_at <= resolved_at` for the malicious version and no later-good version preceded it.
  Encode `was_resolved_while_live = true` as a first-class edge property at ingest, AND expose the
  raw timestamps so queries can recompute it.

## Performance ground rules
- Bounded variable-length paths only (`*1..6`), keep hop count modest; deeper = slower on object store.
- Bulk-ingest with `UNWIND` batches (e.g. 500 rows/batch) rather than one CREATE per row.
- Where a fan-out is large, prefer `count`/`collect` aggregates and let the client render.
- Profile with `GET /metrics` and wall-clock timing in `scripts/eval.py`; target sub-second p95
  on query latency for the demo.

### Phase 3 — live-verified query layer facts
- **Result cap:** plain `MATCH ... RETURN` returns **at most 1024 rows** (silently truncated; no error).
  Any full-scan candidate query must be narrowed with `WHERE` predicates so the true set fits under the cap
  (e.g. typosquat pool: `WHERE v.popular = false AND (v.deprecated = true OR v.published_at >= $since)`).
- **No composite list parameters:** `WHERE v.id IN $ids` is rejected (`composite parameter $ids is only
  supported as an UNWIND input`), and `UNWIND $ids AS i MATCH (n {id: i})` is rejected too
  (`UNWIND batch supports one-hop relationships only`). Workaround: iterate the *indexed*
  `(v {id: $id})` pattern one id at a time (fast, ~2-5 ms/query), or scan service-side and intersect in Python.
- **Variable-length paths need a fixed source id on the left, outgoing only.** `(a)-[:T*1..6]->(b {id:$id})`
  and `(b {id:$id})<-[:T*1..6]-(a)` are both rejected (`variable-length MATCH requires a fixed source id`);
  only `(v {id:$id})-[:T*1..6]->(a)` executes. Consequence: reverse closures (dependants) are computed
  level-by-level in `src/graph_service.py` using one-hop `(u)-[:DEPENDS_ON]->(v {id:$id})` per frontier node.
- **`count(DISTINCT x)` rejected** (`DISTINCT aggregate arguments are not executable`); plain `RETURN DISTINCT`
  works.
- Measured on the 2000-node dataset (see `.evidence/runs/phase-3/latency.txt`): exposed-services answer
  ≈ 57 ms p50 / 58 ms p95; blast-radius ≈ 4 ms; typosquat ranking ≈ 72 ms; all far under the 1 s budget.

### Phase 6 — live-verified write-path facts
- **`CREATE` and `DETACH DELETE` 500 with `internal query execution error` once the store is populated**
  (verified 2026-08-19 against the full ingest; reproduced with labeled and existing edge types, e.g.
  DEPENDS_ON). The identical `CREATE ... -[:FOLLOWS]-> ...` / `DETACH DELETE` cycle passes 7/7 on a fresh
  empty store. Consequence: `scripts/smoke.sh --write-probe` must run against an empty store;
  the default mode is read-only (`healthz` + ingested-schema readability + parameterized no-injection).
- **`RETURN` accepts only `<binding>.<property>` or `count(*)`** — engine functions like `labels(x)` are
  rejected. Drop derived values from the projection and derive them client-side from traversal context
  (UI subgraph does this; see `src/graph_service.py`).
- Deterministic dataset regeneration: `scripts/gen_dataset.py` must iterate name pools in a **sorted**
  order; iterating a `set` makes the RNG stream hash-order-dependent (differs per process), which silently
  changed the generated graph and its ground truth between runs. Fixed + verified (identical SHA across 3
  runs, `seed=20260812`).

## Map of where things live in the HydraDB source (from graphify)
Key communities from `docs/research/hydradb-context-graph/GRAPH_REPORT.md`:
- `src/query/path_procedure.rs` — `algo.*` path procedures.
- `src/query/opencypher.rs` — the batch writer + `UNWIND` ingestion layer.
- `src/query/http.rs` / `src/query/query.rs` / `src/query/query_optimizer.rs` — HTTP API + planning.
- Bolt: `src/bolt/` (tests live in `src/bolt/tests.rs`).
- `src/bin/graph-node.rs` / `src/bin/graph-indexer.rs` — the two runnable binaries.
- `crates/placement/` — cell placement / heartbeat (only relevant for multi-node clusters).

> We never modify HydraDB. If something is unsupported, we work around it in our query layer.