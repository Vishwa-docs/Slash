# Data Flows

> Source of truth: `docs/architecture/index.md`.

## A. Ingestion flow (batch, offline)

```
ecosystem definition (JSON)            ground_truth.json (advisories, blast radii, typosquats)
      │                                        │
      v                                        v
scripts/fetch_github.py  ──────────────────►   data/github/{dataset,ground_truth,manifest}.json + osv/
      │
      v
scripts/ingest.py   (UNWIND $rows AS row ... MERGE ...; 500 rows/batch; idempotent)
      │
      v
  HydraDB graph (nodes: Service/Lockfile/PackageVersion/Developer;
                 edges: DEPENDS_ON / RESOLVES_TO / MAINTAINED_BY / USES_LOCKFILE)
```

- Every edge carries `valid_from`; deprecated facts carry `valid_until` (sentinel for live).
- Advisory events are ingested as node flags (`malicious`, `advisory_id`) **plus** a temporal edge
  window so "was it live when this lockfile resolved?" is answerable from properties alone.

## B. Query / question flow (online)

```
user question (Streamlit)
   ──► intent.py (Researcher): classify → QueryPlan (1..4 concrete Cypher builds)
   ──► graph_service.py: generate Cypher with params
   ──► hydradb_client.query(): run against HydraDB (capped: max queries, max hops, time budget)
   ──► adjudicate.py (Auditor): density / temporal / contradiction checks
   ──► adjudicate.py (Adjudicator): verdict OR abstention
   ──► app.py: evidence chain (Cypther + rows + latency), subgraph plot, verdict badge
```

The evidence chain is **rendered, not summarized away** — the judge sees exactly which traversal
produced the answer.

## C. Abstention path (first-class)

| Condition | Behavior |
|---|---|
| intent `UNSUPPORTED` (out of vocabulary) | Verdict abstains: "I can answer blast-radius / exposure / forensics / contagion / typosquat questions." |
| zero or sparse evidence (< density threshold) | Auditor lowers confidence; Adjudicator abstains: "Not enough evidence in the graph." |
| contradiction detected | Adjudicator reports both facts + temporal/source reasoning, then answers with the authoritative one or abstains. |
| query budget exceeded | Abstain with cost note (never return a half-traversed answer as complete). |

## D. Ground truth and scoring (eval flow)

```
held-out advisories from ground_truth.json
   ──► run Slash queries (without ground truth visible)
   ──► compare predicted exposed sets vs ground-truth exposed sets
   ──► precision / recall / F1, p95 latency, queries-per-question, token cost
   ──► docs/research/scoring.md  (rendered table for demo + README)
```