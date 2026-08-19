# ADR-0005 — Deterministic synthetic ecosystem + planted ground truth

- **Status:** accepted
- **Date:** 2026-08-19
- **Owner:** team
- **Links:** `docs/product/features.md` (F8), `docs/research/scoring.md`

## Context
Track 02A says ground truth is "free from OSV and the GitHub Advisory Database; recent advisories
are held out and teams get an older ecosystem graph." We cannot count on receiving a specific file
by the deadline, and a live crawl of npm would be slow, non-reproducible, and expensive.

## Decision
- `scripts/gen_dataset.py` generates a **deterministic** npm-style ecosystem (seeded RNG) with
  realistic topology: ~600 packages / ~1.8k versions / ~400 developers / ~15 services / ~40
  lockfiles. It plants:
  - 3–4 advisories (malicious versions with `published_at`/`valid_until` windows),
  - known blast radii (which services are transitively exposed),
  - 5–8 typosquats (names close to popular packages, weak reputation),
  - 1–2 shared-maintainer contagion chains.
- Outputs `data/generated/dataset.json` + `ground_truth.json` (advisory, exposed sets, typosquats).
- The evaluator treats a held-out subset of advisories as "recent" and scores predictions of
  exposed sets with precision/recall/f1 + query latency + cost.
- Ingest schema is identical to what a real `cdxgen`/CycloneDX pipeline would produce, so real
  SBOM ingestion (C1 stretch) drops into the same HydraDB schema with a small adapter.

## Consequences
- Fully reproducible, offline, no keys — demo-safe.
- `data/` is gitignored for generated artifacts; a small committed seed (`data/raw/seed.toml`)
  pins the RNG so anyone can regenerate the same ecosystem.
- The README discloses that the demo ecosystem is synthetic, with the path to real data.