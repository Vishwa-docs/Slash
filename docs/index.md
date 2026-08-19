# Slash — Documentation Index

**Hack Hydra 2026 · Track 02A · Supply Chain Blast Radius**

This repo is designed so you can start from the top and drill down. Read in this order:

1. **`vl/PLAN.md`** — the whole story: strategy, track choice, architecture, features, execution plan.
2. **`DESIGN.md`** — the UI design system (what the product should look like).
3. **`docs/architecture/index.md`** — system overview (context → containers → components → data).
4. **`docs/architecture/hydradb-notes.md`** — verified facts about HydraDB's API (the ground rules for every query we write).
5. **`docs/product/features.md`** — the feature set and what is deliberately out of scope.
6. **`docs/product/roadmap.md`** — what shipped when.

## Table of contents

| Area | Documents |
|---|---|
| Plan & strategy | `vl/PLAN.md`, `docs/reference/strategy-analysis.md` |
| Product | `docs/product/vision.md`, `docs/product/features.md`, `docs/product/glossary.md`, `docs/product/personas.md` |
| Architecture | `docs/architecture/index.md`, `system-context.md`, `containers.md`, `components.md`, `data-flows.md`, `trust-boundaries.md`, `hydradb-notes.md`, `decisions/` |
| Research | `docs/research/hydradb-context-graph/GRAPH_REPORT.md` (graphify graph of HydraDB), `docs/research/scoring.md` |
| UX | `docs/ux/flows/`, `DESIGN.md` |
| Security & ops | `docs/security/threat-model.md`, `docs/operations/service.md` |
| Testing | `docs/testing/strategy.md` |
| Change ledger | `changes/CHG-0001/` |
| References | `docs/reference/` (strategy analysis, factory brief, participant guide) |

## Conventions

- Docs keep a "source of truth" header that names the governing file (e.g. DESIGN.md, PLAN.md).
- Any doc that contradicts a higher-priority source of truth is a bug — fix the doc.
- Terminal / demo / CLI examples are included because a small-context agent and a human reviewer
  both need them.