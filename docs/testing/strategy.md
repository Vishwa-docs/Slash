# Testing Strategy

> Source of truth: `docs/architecture/index.md`, `changes/CHG-0001/test-plan/`.

Tests are chosen by **evidence value for the demo**, not ceremony. Priority order for the build:

| Priority | Test | Files | Why |
|---|---|---|---|
| 1 | **Query correctness against live HydraDB** | `tests/integration/test_queries.py` (`scripts/smoke.sh` bootstraps) | The demo IS the queries — they must be proven against the real container |
| 2 | **Intent classification** | `tests/unit/test_intent.py` | Deterministic router is a core differentiator |
| 3 | **Abstention decisioning** | `tests/unit/test_abstention.py` | A first-class feature; must not drift |
| 4 | **HydraDB client parsing** | `tests/unit/test_client.py` | Malformed rows must not crash the app |
| 5 | **Eval harness** | `tests/unit/test_eval.py`, `tests/integration/test_eval_integration.py` | Precision/recall/latency numbers shown to judges |
| 6 | **Ingest idempotency** | `tests/integration/test_ingest.py` | Admin/dev trust: re-running ingest must not duplicate |

## Test data
- Unit tests use small in-memory fixtures (no HydraDB).
- Integration/e2e require the running container (marked with `@pytest.mark.integration`).
- The reference dataset (generated, committed seed) is shared by ingest + eval + e2e.

## Commands (to be wired as the build lands)
```bash
pytest tests/unit -q              # fast, no container
pytest tests/integration -q       # requires HydraDB up (src/infra/hydradb-up.sh)
python scripts/eval.py            # scoring table -> docs/research/scoring.md
```

## Traceability
- F1–F8 (features) map to at least one test.
- Each phase in `vk/PROMPT.md` ends with a Definition of Done that includes specific test evidence
  stored under `.evidence/runs/<phase>/`.