# Scoring Methodology & Results

> Source of truth: `changes/CHG-0001/test-plan/` + these live numbers from `.evidence/runs/phase-6/eval.txt`.

## Ground truth
`data/github/ground_truth.json` records, per advisory (all labels derived from real
GitHub/OSV data — nothing planted):
- the malicious `PackageVersion` (`name`, `version`, node id, OSV/CVE advisory id),
- the true exposed service set = services whose lockfile resolves the malicious
  version or a transitive dependent of it (the same reverse-closure semantics the
  query engine uses, within its 6-hop ceiling),
- the true "resolved-while-live" recompute flag (F3), verified at query time.

## Metrics
| Metric | Definition | Target |
|---|---|---|
| Precision | | predicted exposed ∩ true exposed | / | predicted exposed | | report |
| Recall | | predicted exposed ∩ true exposed | / | true exposed | | report |
| F1 | harmonic mean | report |
| Query latency p95 | wall-clock per question-phrase (client `elapsed_ms`) | < 1 s |
| Cost | queries-per-question and (if LLM on) tokens | cap + report |

## Procedure
1. Close over a subset of advisories as "recent" to simulate the track's held-out rule
   (preferring advisories the corpus actually exposes, so P/R has a real truth set).
2. Run Slash **without** ground truth visibility.
3. Compute metrics; render table into README + this file.

## Results (auto-generated 2026-08-20 12:56 UTC)
Held-out advisories: CVE-2025-24964, MAL-2025-46983 (2 latest by version).

| advisory | query_precision | query_recall | query_f1 | resolved_while_live_f1 | recompute_agrees | latency_ms | queries |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CVE-2025-24964 | 1.00 | 1.00 | 1.00 | - | true | 437 | 14 |
| MAL-2025-46983 | 1.00 | 1.00 | 1.00 | - | true | 521 | 57 |

### Summary
- Mean precision 1.00 · mean recall 1.00 · mean F1 1.00
- p95 per-question latency 592 ms (budget < 1 s)
- 71 queries across 2 questions (35.5 / question)
- Token cost: 0 (deterministic pipeline — no LLM in the loop)

Raw run: `.evidence/runs/phase-6/eval.txt`.
