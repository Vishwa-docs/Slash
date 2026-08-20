# Features

> Source of truth: `vl/PLAN.md`. Every feature is a graph-native capability. **Must** features are
> the demo-critical core; **should** are differentiators; **could** are stretch; **won't** is explicit scope.

## Must (demo-critical core)

| ID | Feature | Graph mechanism | Notes |
|---|---|---|---|
| F1 | **Transitive blast radius** | `MATCH (up)-[:DEPENDS_ON*1..6]->(bad {name:$n, version:$v}) RETURN up.name, count(*)` | Bounded var-length reverse closure reaching internal `Service`+`Lockfile` endpoints |
| F2 | **Exposed services** | Extend F1 to `(Service)-[:USES_LOCKFILE]->(:Lockfile)-[:RESOLVES_TO]->...` | Returns the exact service set with the traversal path |
| F3 | **Resolved-while-live forensics** | `WHERE lf.resolved_at >= bad.published_at AND lf.resolved_at <= bad.valid_until` on `RESOLVES_TO` | Also flag `was_resolved_while_live` precomputed at ingest |
| F4 | **Maintainer contagion** | `MATCH (p)-[:MAINTAINED_BY]->(d:Developer {id:$did}) MATCH (q)-[:MAINTAINED_BY]->(d)` plus transitive deps | Also device/gpg/infra sharing where modeled |
| F5 | **Typosquat candidates** | Graph signals (low in-degree, no maintainer edges, recent `published_at`, orphaned) + name edit-distance vs `popular` packages | Scoring in Python; graph supplies the signals |
| F6 | **Honest abstention** | Subgraph density + intent coverage gate | First-class verdict type, UI badge |
| F7 | **Evidence chain** | Every verdict carries the Cypher + rows + latency rendered in UI | Judges see the exact traversal |
| F8 | **Reproducible real-data pipeline** | `scripts/fetch_github.py` + `ingest.py` with committed GitHub/npm/OSV snapshot | Reproducible offline, zero fabricated records |

## Should (differentiators)

| ID | Feature | Notes |
|---|---|---|
| S1 | Multi-agent pipeline (Researcher/Auditor/Adjudicator) surfaced as "thought process" in UI | Traces every decision; ported from the winning GDELT formula |
| S2 | Scoring harness (`scripts/eval.py`) | Precision/recall/f1 + latency/cost on held-out advisories → `docs/research/scoring.md` |
| S3 | Temporal contradiction resolution | Two facts conflict → show both with timestamps, prefer authoritative/newer, mark deprecated edge `valid_until` |
| S4 | README section **"How We Used HydraDB"** | The judging-critical narrative |
| S5 | Docker Compose single-command demo (`deploy/docker-compose.yml`) | "docker compose up" = full demo |
| S6 | Query budget + cost badges in UI | Tokens vs pure-graph paths; supports latency/cost scoring metric |

## Could (stretch, only if time)

| ID | Feature | Notes |
|---|---|---|
| C1 | Real SBOM ingestion (`cdxgen` output / CycloneDX) | Parse real files into the same schema; nice demo b-roll |
| C2 | 3-minute video script + storyboard template | Make the video trivial to produce |
| C3 | Graph export (SVG/PNG) screenshots for README | Visuals for the submission |

## Won't (explicit scope cuts)

| ID | Cut | Why |
|---|---|---|
| W1 | Full npm registry mirror | Time + storage; generator/reference pipeline documented instead |
| W2 | Vector/semantic search of any kind | Contradicts the graph-native story |
| W3 | Auth/multi-tenant | Not needed for the demo |
| W4 | Track 03/01 features | Distinct projects per rules; we are one project, one track |

---

## Pinned query semantics (live-verified, Phase 3)

All query steps live in `src/graph_service.py` as pure `plan_*` builders returning `(cypher, params)`.
Every query is parameterized (`$name`, `$version`, `$id`, `$dev`), bounded (`*1..6` ceiling), and
executed with per-step latency capture (evidence chain). Verified against `data/github/ground_truth.json`
in `tests/integration/test_queries.py` (7 tests green, `.evidence/runs/phase-3/`).

| Feature | Rendered query (anchored form) | Notes |
|---|---|---|
| F1 Blast radius | Level-by-level: `MATCH (u:PackageVersion)-[:DEPENDS_ON]->(v:PackageVersion {id:$id}) RETURN DISTINCT u.id, u.name, u.version` from the bad node, repeated ≤ `MAX_HOPS=6` | HydraDB rejects incoming/starred var-length and `IN $list` (hydradb-notes §Phase 3); indexed one-hop per frontier node is the fast, supported equivalent |
| F2 Exposed services | `MATCH (s:Service {name:$svc})-[:USES_LOCKFILE]->(lf:Lockfile)-[r:RESOLVES_TO]->(v:PackageVersion) RETURN lf.id, lf.app, lf.resolved_at, v.id, v.name, v.version, v.published_at, v.valid_until, r.at, r.was_resolved_while_live` per service, intersected with the blast-radius closure in Python | 15 services ⇒ ≤16 queries |
| F3 Resolved-while-live | Same edge scan; list = rows where `bad.published_at <= lf.resolved_at <= bad.valid_until`; recompute flag = `v.published_at <= r.at <= v.valid_until` compared to stored `r.was_resolved_while_live` | Recompute agrees with ingest-time flag (tested) |
| F4 Maintainer contagion | `MATCH (d:Developer {handle:$dev})<-[:MAINTAINED_BY]-(p:PackageVersion) RETURN DISTINCT p.name` | `dev_137` → 5 packages incl. all 3 planted `shared_packages` |
| F7 Evidence chain | Every `run_*` returns `steps: [(QueryStep, QueryResult)]` with `elapsed_ms` per query | Rendered verbatim in the UI console panel |

Recorded back here so README and docs stay truthful.