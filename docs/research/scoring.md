# Scoring Methodology & Results

> Source of truth: `changes/CHG-0001/test-plan/` + these live numbers from `.evidence/runs/phase-6/eval.txt`.

## Ground truth
`data/generated/ground_truth.json` records, per advisory:
- the malicious `PackageVersion` (`name`, `version`, window),
- the true exposed service set (transitive reverse-dependency closure within our 6-hop ceiling),
- the true "resolved-while-live" lockfile set,
- the planted typosquats.

## Metrics
| Metric | Definition | Target |
|---|---|---|
| Precision | | predicted exposed ∩ true exposed | / | predicted exposed | | report |
| Recall | | predicted exposed ∩ true exposed | / | true exposed | | report |
| F1 | harmonic mean | report |
| Query latency p95 | wall-clock per question-phrase (client `elapsed_ms`) | < 1 s |
| Cost | queries-per-question and (if LLM on) tokens | cap + report |

## Procedure
1. Hold out a subset of advisories as "recent" (simulating the track's held-out rule).
2. Run Slash **without** ground truth visibility.
3. Compute metrics; render table into README + this file.

## Results (auto-generated 2026-08-19 10:08 UTC)
Held-out advisories: ADV-2026-02, ADV-2026-01 (2 latest by published_at).

| advisory | query_precision | query_recall | query_f1 | resolved_while_live_f1 | recompute_agrees | latency_ms | queries |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ADV-2026-02 | 1.00 | 1.00 | 1.00 | 1.00 | true | 77 | 18 |
| ADV-2026-01 | 1.00 | 1.00 | 1.00 | 1.00 | true | 56 | 18 |

### Summary
- Mean precision 1.00 · mean recall 1.00 · mean F1 1.00
- p95 per-question latency 96 ms (budget < 1 s)
- 36 queries across 2 questions (18.0 / question)
- Token cost: 0 (deterministic pipeline — no LLM in the loop)

Raw run: `.evidence/runs/phase-6/eval.txt`.
