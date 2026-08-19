# Requirements Index

> Source of truth: `docs/product/features.md`. Each top-level requirement is a feature ID.
> Acceptance preconditions are written so a judge — or a testing bot — can check them.

## Must (M), Should (S), Could (C), Won't (W)
- M‑F1 Transitive blast radius — exposed service set returned with traversal evidence.
- M‑F2 Exposed services — service-level list, deduplicated, count included.
- M‑F3 Resolved-while-live — lockfile set with both extracted and recomputed flags.
- M‑F4 Maintainer contagion — packages sharing a mantainer (+ transitive deps) listed.
- M‑F5 Typosquat candidates — ranked list with graph signals shown.
- M‑F6 Honest abstention — out-of-vocabulary or low-evidence → abstention verdict.
- M‑F7 Evidence chain — every verdict renders Cypher + params + rows + latency.
- M‑F8 Deterministic data pipeline — regenerable dataset + ground truth.
- S‑S1 Multi-agent trace surfaced in UI.  S‑S2 Scoring harness.  S‑S3 Temporal contradiction handling.
- S‑S4 "How We Used HydraDB" README section.  S‑S5 Docker Compose demo.  S‑S6 Budget/cost badges.
- C‑C1 Real SBOM ingest adapter. C‑C2 Video script. C‑C3 Graph screenshots for README.

## Acceptance preconditions (sample; full set in `changes/CHG-0001/`)
- **M‑F1/F2:** given a planted malicious version, running the question returns exactly the
  ground-truth exposed set (within 6 hops) with `elapsed < 1s`.
- **M‑F3:** for every lockfile flagged `was_resolved_while_live=true`, the recomputed comparison
  (`resolved_at` within advisory window) agrees.
- **M‑F6:** 5 out-of-vocabulary questions → 5 abstentions, 0 invented answers.
- **M‑F8:** fresh clone + 2 commands reproduces the same dataset + graph counts.