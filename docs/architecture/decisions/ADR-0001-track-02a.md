# ADR-0001 — Compete on Track 02A (Supply Chain Blast Radius)

- **Status:** accepted
- **Date:** 2026-08-19
- **Owner:** team
- **Links:** `docs/reference/strategy-analysis.md`, `vl/PLAN.md`, `changes/CHG-0001/change.yaml`

## Context
The strategy document found two heavy metals: agentic-memory infra (Track 03) and supply-chain
security (Track 02). Both are venture-backed and both have public datasets. We must pick ONE
(per-track discipline: distinct projects per track, one prize per team).

## Considered options
| Option | Pros | Cons |
|---|---|---|
| 02A Supply chain blast radius | Purest graph problem (transitive closure — trivially impossible for vector DBs); objective scoring (precision/recall/latency); self-contained dataset; strongest "Best Use of HydraDB" story; least LLM-dependent | Needs a credible ecosystem dataset; blast-radius traversal depth matters |
| 01 Enterprise ontology (500K docs) | Massive opportunity | Entity resolution is heavy, fuzzy, LLM-costly; ingestion of 500K docs is a project of its own; weaker objective score |
| 03 Agent memory (LongMemEval) | Aligns with mem0/Cognee narrative | Fuzzy scoring; correctness depends heavily on abstention tuning & LLM evals; more moving parts |
| 02B Code graphs for IDE | Cool | Needs SWE-bench eval loop + embedding comparison; longer tail to a compelling demo |

## Decision
**Track 02A.** Rationale: it is the most *impossible-for-a-vector-database* problem, it has an
objective, demoable score (precision/recall/latency/cost), it has the most direct
"what does the project lose without HydraDB" answer, and it can be built to a compelling working
product in the remaining hours without depending on an LLM.

## Consequences
- Data pipeline (synthetic ecosystem + ground truth) is a first-class deliverable.
- Traversal primitives (`*1..6` bounded closure, temporal properties) are the product.
- LLM agents are an augmentation layer, never the core.