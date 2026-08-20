# ADR-0015 — Real-data corpus (supersedes ADR-0005)

- **Status:** accepted
- **Date:** 2026-08-20
- **Owner:** team
- **Links:** `scripts/fetch_github.py`, `data/github/*`, `scripts/ingest.py`,
  `scripts/eval.py`

## Context
ADR-0005 chose a deterministic synthetic ecosystem so demos were reproducible and cheap.
By the week of the hackathon, that choice became a liability: judges can — and do — ask one
question about the data ("is this `oslo` a real package?"), and every vulnerability in the
corpus is invented. The fraud/AML vertical (ADR-0010) plus `gen_fraud_dataset.py` /
`data/fraud/` add a second synthetic graph and double the surface area of "this is fake".

The source of truth for dependencies is public and structured: the GitHub open-source
dataset, the npm registry, the git commit graph of real repositories, and the OSV
vulnerability database. All of it is downloadable and cacheable, which keeps the demo
reproducible.

## Decision
- The demo corpus is built by `scripts/fetch_github.py` from **real sources only** for 12
  well-known npm projects:
  - package versions: npm registry metadata (real versions, dist-tags as of an epoch);
  - dependency edges: real git-dependency versions + names + publish dates, npm registry
    dependency declarations;
  - lockfile pins + consuming services: parsed `package-lock.json` from real repos;
  - maintainers: author/committer history from real git clones, grouped into a
    `Developer`/`MAINTAINED_BY` graph;
  - vulnerabilities: real OSV records for the package versions actually present, plus
    upstream advisory links ("supply-chain compromise" / "malicious package" / typosquat
    classes) recorded from the advisories' own references.
- `data/github/{dataset.json,ground_truth.json,osv/}` is **committed** so any machine can
  rebuild the exact graph offline (`fetch_github.py --offline`). Ground truth is
  advisory-derived, honest labels:
  - `malicious` only when the upstream advisory/implications say the version is malicious;
  - `exposed_services` = lockfile consumers that pinned the vulnerable version;
  - `resolved_while_live` recomputed from published/valid-until windows (F3), no planting.
- `scripts/gen_dataset.py`, `scripts/gen_fraud_dataset.py`, `data/generated/`,
  `data/fraud/`, `seed.toml` are **deleted**. The lens layer stays (ADR-0010) but ships one
  real lens (`dependency-graph`).
- PRs that add story ("make the numbers land better") data are rejected; the demo's
  reproducibility guarantee moves from "deterministic seed" to "committed real snapshot".

## Consequences
- Demo claims are falsifiable against real packages and real advisories on npm/GitHub/OSV.
- A network failure or missing API key degrades gracefully to the committed snapshot
  (offline flag), never to fabricated records.
- The corpus is smaller than the old generator's ambitions (12 repos) — a conscious trade
  to keep every row traceable to a real source within a 72-hour build.