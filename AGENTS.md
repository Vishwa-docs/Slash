# Slash — Repository Operating Contract

## Mission
Ship **Slash**, a Track 02A (Supply Chain Blast Radius) submission for Hack Hydra 2026.
It ingests an npm-style dependency ecosystem into **HydraDB** and answers, in real time:
which internal services are transitively exposed by a compromised package, which apps
resolved the bad version while it was live, which packages share maintainers /
infrastructure, which nearby names are likely typosquats, and what the complete blast
radius is — with correct, first-class **abstention** when the data isn't there.

Everything below is written for the **small-context coding agent**. Read AGENTS.md fully
once (it is short), then follow the task packet exactly. Do **not** scan the whole repo.

## Source Of Truth
1. `README.md` — project overview, architecture, and quickstart.
2. `DESIGN.md` — UI design tokens and visual system.
3. `docs/architecture/hydradb-notes.md` — verified facts about HydraDB's API surface.
4. `docs/reference/hack-hydra-participant-guide.txt` — the official rules (read once, skim).
5. `AGENTS.md` — this contract.
6. Existing implementation + tests.

Stop and report conflicts. Do not silently choose between documentation and the code.

## Context Diet (very important for a small context window)
Do **not** read these unless a phase tells you to:

- The HydraDB Rust source: `hydradb/` (parent directory) is 156 tracked files. **Only read** the
  files a phase points you at (`hydradb/README.md` Getting Started, `hydradb/cypher-compat.md`,
  `hydradb/scripts/runtime_smoke.sh`). Everything else — query engine internals, GraphBLAS,
  SlateDB, placement — you do not need.
- `docs/research/hydradb-context-graph/GRAPH_REPORT.md` — you may read the "God Nodes" +
  "Communities" sections as a map of where things live; do not read it line by line.
- `docs/reference/strategy-analysis.md` and `agentic-software-factory-brief.md` — reference only.
  Read them only when a phase explicitly requests context from them.

When in doubt about HydraDB behavior, prefer **empirical verification** (run a query against
the live container) over reading source.

## Required Workflow
1. Map affected files, queries, data, contracts, tests, and docs for your task.
2. Search for existing reusable behavior in `src/` and `scripts/` before adding code.
3. State a small file-by-file plan before editing.
4. Implement one reviewable vertical slice. Keep the diff small.
5. Run the required checks and **save command output under `.evidence/runs/`**.
6. Review your diff: no unnecessary code, no duplication, no drift from DESIGN.md.
7. Append to `CHANGELOG.md` and update `.state/task-graph.json`.

## Commands (intended, fill in as the project is built)
- Setup: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Format: `ruff format .`   ·   Lint: `ruff check .`
- Type-check: `mypy src` (if added to requirements)  ·  Unit tests: `pytest tests/unit -q`
- Integration tests: `pytest tests/integration -q` (requires HydraDB running)
- HydraDB up: `docker run --rm -d --name slash-hydra ...` (exact flags: `src/infra/hydradb-up.sh`)
- Ingest: `python scripts/ingest.py`
- Eval: `python scripts/eval.py`
- App: `python scripts/serve.py`
- Local run: see `docs/operations/service.md`

## Constraints
- No invented APIs, packages, files, commands, or environment variables. If HydraDB rejects a
  query, adjust the query to the documented subset in `hydradb/cypher-compat.md`; never fake a result.
- No dependency addition without approval and a `.capabilities/registry.yaml` update.
- No skipped, weakened, or deleted tests to get a passing build.
- No unrelated refactoring; no speculative abstractions; no duplicate implementation.
- No secrets or production data in prompts, code, fixtures, logs, screenshots, or traces.
- Preserve the DESIGN.md visual system when building UI. Keep the product working without an LLM
  API key (deterministic fallbacks every place an LLM is optional).
- Abstention is a feature: when the graph lacks the evidence, the product must say so — never invent.

## Stop Conditions
Stop and reopen design when:
- a query the product depends on is unsupported by HydraDB and no documented equivalent exists;
- a public contract (schema, README guarantees) must change;
- a new external service / API key / network dependency would be required beyond the plan;
- the expected diff substantially exceeds the phase estimate;
- HydraDB stops responding and the runbook (`docs/operations/service.md`) does not cover recovery.

## Completion
Never claim completion without fresh verification evidence stored under `.evidence/runs/`.