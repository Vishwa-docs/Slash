# Roadmap

> Project roadmap and milestone schedule across the build window (Aug 12–20, 2026).

| Phase | Window | Deliverable | Evidence |
|---|---|---|---|
| P1 Infrastructure | Day 1–3 (or hour 1–3) | HydraDB up via Docker; `src/hydradb_client.py`; smoke test green | `.evidence/runs/phase-1/smoke.txt` |
| P2 Schema + dataset + ingest | Day 2–4 | `src/infra` schema, `scripts/gen_dataset.py`, `scripts/ingest.py`, populated graph | `.evidence/runs/phase-2/ingest.txt` |
| P3 Query layer | Day 4–6 | `src/graph_service.py` (F1–F5), integration tests green | `.evidence/runs/phase-3/` |
| P4 Agents + abstention | Day 5–6 | `src/intent.py`, `src/adjudicate.py`, abstention unit tests | `.evidence/runs/phase-4/` |
| P5 UI | Day 7–8 | `app.py` per DESIGN.md (console, evidence panel, subgraph viz) | `.evidence/runs/phase-5/` (screenshots) |
| P6 Eval + README + video | Day 8–9 | `scripts/eval.py` → scoring table; README "How We Used HydraDB"; video script; submit | `.evidence/runs/phase-6/eval.txt` |

## Done means
Working, tested, documented, scored, with the submission checklist satisfied **hours** before the
11:59 PM PT deadline on Aug 20. "Stop adding features before the deadline. Test what you already
built." — participant guide.