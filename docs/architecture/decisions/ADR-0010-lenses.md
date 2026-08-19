# ADR-0010 — Domain lenses: one query engine, many connected graphs

- **Status:** accepted
- **Date:** 2026-08-19
- **Owner:** team
- **Links:** `src/lens.py`, `scripts/gen_fraud_dataset.py`, `src/schema.py` (fraud
  section), `tests/integration/test_fraud_lens.py`

## Context
Slash's five answer primitives (blast radius, exposed surfaces, resolved-inside-a-
suspicious-window, shared-owner contagion, name lookalikes) are structurally identical
across domains. Supply-chain exposure and fraud/AML intake follow the same shape:
`AssetState ─consumes/transfers→ AssetState`, `Surface ─uses/feeds→ Observation ─involves→
AssetState`, `AssetState ─maintained_by/owne→ Actor`. Copy-pasting the query layer per
vertical duplicates hundreds of lines and lets the two copies drift.

## Decision
- Introduce `src/lens.py`: the `Lens` dataclass parametric over node labels, relation
  types, the amenability property (`malicious` / `compromised`), and answer vocabulary.
- Every `plan_*` / `run_*` in `src/graph_service.py` takes `lens: Lens = SUPPLY_CHAIN`.
  The default keeps the flagship supply-chain behaviour byte-identical (verified by a
  cypher-string diff against the pre-lens plans).
- One search/pipeline layer: `src/intent.py` and `src/adjudicate.py` accept a lens and
  pick vocabulary from it; no new query primitives were added for fraud.
- Fraud ships its own dataset generator (`scripts/gen_fraud_dataset.py`,
  `data/fraud/{dataset,ground_truth}.json`) and schema property sets
  (`src/schema.py` FRAUD_* maps) consumed by the existing idempotent ingester.
- The web console (`app.py`) and product API (`src/api.py`, `scripts/serve.py --lens`)
  expose a lens selector; `/api/ask` and `/api/subgraph` accept an optional `lens`.

## Consequences
- New verticals are a Lens + dataset + example questions; no query engine changes.
- The supply-chain path keeps its exact SQL/Cypher and answers (zero-regression
  verified against the pre-lens captured queries).
- A lens is selected per request, not per engine; runs against one live graph namespace.
- Honest abstention is preserved per lens: "we couldn't tell the weather from the
  supply-chain graph" still abstains.