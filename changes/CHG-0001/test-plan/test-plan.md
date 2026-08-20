# Test Plan — CHG-0001

Runs against the reference dataset and live HydraDB where marked.

| Feature | Test | Requires container |
|---|---|---|
| F1/F2 blast radius + exposed services | `tests/integration/test_queries.py::test_exposed_services_matches_ground_truth` | yes |
| F3 resolved-while-live | `test_recompute_flag_agrees` (F3 recompute vs stored flag) | yes |
| F4 maintainer contagion | `test_blast_radius_reaches_real_consumers` + demo battery | yes |
| F5 typosquat candidates | `test_typosquat_candidates_shape` (live) | yes |
| F6 abstention | `tests/unit/test_abstention.py` (5 out-of-vocab → 5 abstain) | no |
| F7 evidence chain | `test_verdict_has_query_and_rows` (unit) | no |
| F8 pipeline determinism | `fetch_github.py --offline` twice → identical ground-truth md5 | no |
| Client parsing | `tests/unit/test_client.py::test_malformed_row_fails_cleanly` | no |
| Ingestion idempotency | `tests/integration/test_ingest.py::test_reingest_no_duplicates` | yes |
| Eval harness | `tests/unit/test_eval.py` + `python scripts/eval.py` → scoring.md | yes |

## Execution order per phase
- P1 smoke: `scripts/smoke.sh` (health + roundtrip + no-injection fuzz).
- P2: ingest + counting.
- P3: integration query suite + latency capture.
- P4: intent + abstention suites.
- P5: manual e2e walkthrough (screenshots → `.evidence/runs/phase-5/`).
- P6: eval table + clean-clone re-run of README quick start.

## Success criteria
- All unit + integration tests green with fresh evidence.
- p95 latency < 1 s on reference dataset (best-effort target, report real numbers).
- 100% abstention on the out-of-vocabulary suite.
- Clean-clone instruction set in README produces the demo in under 2 minutes.