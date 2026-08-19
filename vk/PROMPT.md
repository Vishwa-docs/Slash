# Slash — Coding Agent Task Packet (vk/PROMPT.md)

> **Repo root (relative paths below resolve here):** `/Users/daver/Desktop/Hackathons/Hack Hydra The HydraDB Open Source Hackathon/Slash`
>
> **How to use this file:** You will be told which **phase** to perform (e.g. "run Phase 3").
> Execute **only that phase** in this session. Each phase is self-contained: files to read,
> exact builds, verification commands, and a Definition of Done. When a phase is done, report
> the Handoff (see §4). Do **not** run other phases, and do **not** read the whole repo.

---

## 0. Standing instructions (apply to every phase)

1. **You are the Implementer** for one vertical slice of **Slash**, a Hack Hydra 2026
   (Track 02A) submission: a blast-radius intelligence console on **HydraDB**.
   Product context: `AGENTS.md` (§Mission) and `vk/PLAN.md` (§1–§2). Read AGENTS.md once — it is short.
2. **Control-plane rules** (`AGENTS.md`): smallest correct diff, no invented APIs, evidence-backed
   completion, no secrets, abstention honesty, parameterize every query (never splice user text).
3. **Ponytail discipline** (skill `.agents/skills/vendor/ponytail/SKILL.md`, default `full`):
   stdlib/native first, one line before fifty, shortest working diff, root-cause fixes.
   When you deliberately cut a corner, mark it `# ponytail: <ceiling>, add when <trigger>`.
4. **UI must follow `DESIGN.md`** whenever you touch UI (mono font, cream canvas, hairline
   sections, 4px radius, ASCII brackets, one dark surface, semantic colors for verdicts only).
5. **HydraDB facts** live in `docs/architecture/hydradb-notes.md`. If a query is unsupported
   (see the OpenCypher subset), **adjust yours — never fake a result**.
6. **Evidence rule:** save every verification output under `.evidence/runs/phase-<N>/`
   (create the dir). Completion claims without fresh evidence are rejected.
7. **Optional LLM is OFF.** The product must work with no API key. Do not write code paths that
   require a key to run the demo.
8. **Abstention is a feature.** Never answer where evidence is thin; return a first-class abstention.

---

## 1. Phase 1 — Infrastructure (timebox ≈ 2–3 h)

### Goal
HydraDB running via Docker from this repo, a typed Python client, and a green smoke test.

### Read first (exactly these; do not read `hydradb/src`, charts, or Grafa)
- `AGENTS.md`
- `docs/architecture/hydradb-notes.md` (especially "How to run it", "Two APIs", "OpenCypher subset")
- `../hydradb/README.md` — only the "Getting Started"/Docker section and the env var table
- `../hydradb/scripts/runtime_smoke.sh` — skim for the token/env contract (we will not run it directly)

### Build
1. `src/infra/hydradb-up.sh` — idempotent: write `.hydradb/auth.token` (one random line, not secret,
   localhost demo), `docker pull`, `docker run` with the documented env contract
   (`CLOUD_PROVIDER=local`, `LOCAL_PATH`, `GRAPH_NAMESPACE=default`, `GRAPH_ID=default`,
   `GRAPH_CELL_ID=cell-0`, `GRAPH_CELLS=1`, `GRAPH_NODE_ID=0`, `GRAPH_BOLT_NODE_ADDRESSES`,
   `GRAPH_ADVERTISED_BOLT_ADDR`, `GRAPH_DATA_CACHE_DIR`, `GRAPH_AUTH_TOKEN_FILE`,
   `GRAPH_ALLOW_PLAINTEXT=true`, `RUST_MIN_STACK=33554432`, ports 7687/8443/9090),
   then wait for `GET /healthz` to return OK. `docker stop slash-hydra` = teardown.
2. `src/hydradb_client.py` — one class over `urllib.request` (stdlib; no `requests` yet):
   - `healthz() -> bool`, `query(cypher: str, params: dict) -> QueryResult(rows, elapsed_ms)`
     against `POST http://127.0.0.1:8443/v1/graphs/default/query` with
     `Authorization: Bearer <token>` + `X-Graph-Namespace: default` and body
     `{"cell_id": "cell-0", "query": cypher, "consistency": "causal"}` (+ `params` how the API expects).
   - Raise `HydraDBError` on non-2xx / malformed response. Never return partial rows silently.
   - Parse rows into plain dicts / small dataclasses. Add Bolt path TODO only (ADR-0003: not required yet).
3. `scripts/smoke.sh` — sequence: healthz → `CREATE` a probe node → `MATCH` it back → `DETACH DELETE`
   → **no-injection check**: run the same `MATCH` with `params` containing a Cypher injection string
   as a *value* and assert it is treated as data (no error, no extra rows). Print PASS/FAIL lines.

### Verification (save everything to `.evidence/runs/phase-1/`)
```bash
bash src/infra/hydradb-up.sh            # expect: container running, health OK
bash scripts/smoke.sh 2>&1 | tee .evidence/runs/phase-1/smoke.txt
python -c "import src.hydradb_client as c; print(c.HydraDBClient().healthz())"   # expect True
```
DoD: `smoke.txt` green; client round-trip proven; no secrets committed; `hydradb-notes.md` updated
if observed env/token behavior differs.

### Handoff → see §4.

---

## 2. Phase 2 — Schema, dataset, ingest (timebox ≈ 3–4 h)

### Goal
The HydraDB store holds a deterministic ecosystem graph + ground truth, and re-ingestion is safe.

### Read first
- `docs/architecture/hydradb-notes.md` — "OpenCypher subset", "Temporal modeling", "Implications"
- `docs/architecture/components.md` — "Graph data model"
- `docs/architecture/decisions/ADR-0004-temporal-properties.md`, `ADR-0005-dataset.md`

### Build
1. `src/schema.py` — constants only: node/edge labels, property keys, sentinel
   `VALID_UNTIL_LIVE = 9999999999`, index hints.
2. `scripts/gen_dataset.py` — seeded (fixed seed, e.g. 20260812) npm-style ecosystem:
   - ~600 packages / ~1.8k versions / ~400 developers / ~15 services / ~40 lockfiles.
   - Realistic topology: popular hubs (high in-degree), long-ish dep chains, devs maintaining
     1–5 packages, services→lockfiles→versions.
   - Plant **3–4 advisories** (malicious versions with `published_at`/`valid_until` windows),
     **5–8 typosquats** (names edit-close to popular packages, weak reputation, recent publish),
     **1–2 maintainer-contagion chains**.
   - Emit `data/generated/dataset.json` (nodes+edges in UNWIND-ready form) and
     `data/generated/ground_truth.json` (per-advisory: exposed service set, resolved-while-live
     lockfiles, true typosquats). Keep a small committed seed under `data/raw/` so anyone
     regenerates the same corpus (ADR-0005).
3. `scripts/ingest.py` — idempotent: `UNWIND $rows AS row ... MERGE` batches (≤500 rows), node
   integer ids, edge direction **dependant → dependency** for `DEPENDS_ON`, `valid_from`/`valid_until`
   on every edge, `was_resolved_while_live` precomputed on `RESOLVES_TO` (ADR-0004).

### Verification
```bash
python scripts/gen_dataset.py
python scripts/ingest.py                 # counts printed on stdout
python scripts/ingest.py                 # run again -> identical counts (idempotent)
python - <<'PY' 2>&1 | tee .evidence/runs/phase-2/ingest.txt
# print: count(PackageVersion), count(Package), count(Developer), count(Service), count(Lockfile),
#        count(malicious nodes), count(is_typosquat nodes)
PY
```
DoD: `ground_truth.json` exists; counts > 0 and match expectations; re-ingest identical;
evidence + a short note appended to `CHANGELOG.md`.

### Handoff → §4.

---

## 3. Phase 3 — Query layer (timebox ≈ 3–4 h)

### Goal
`src/graph_service.py` produces live-verified, parameterized Cypher for F1–F5; integration tests
green against ground truth.

### Read first
- `docs/product/features.md` — the "Pinned query semantics" section (target semantics)
- `docs/architecture/hydradb-notes.md` — "OpenCypher subset", "Path procedures", "Performance ground rules"
- `tests/integration/test_queries.py` (if it exists from a prior session — extend)

### Build
1. `src/graph_service.py` — pure functions returning `(cypher, params)` (never call the client):
   - `blast_radius(name, version, max_hops=6)` → reverse closure (F1)
   - `exposed_services(name, version)` → service set via `USES_LOCKFILE→RESOLVES_TO→…` (F2)
   - `resolved_while_live(name, version)` → lockfiles within advisory window; also recompute the flag (F3)
   - `maintainer_contagion(developer_id_or_name, max_hops)` (F4)
   - `typosquat_candidates(seed_names) -> list[ranked]` — query graph signals in Cypher, score
     edit-distance in Python (stdlib `difflib`) (F5)
   - `fetch_subgraph(node_id, depth=2)` for the UI
   - Every builder bounds paths (`*1..6`), parameterizes ids/names, uses only the documented subset.
2. `tests/integration/test_queries.py` — parametrized vs `ground_truth.json`:
   - exposed set == true set (F1/F2), recompute agrees with flag (F3), contagion matches (F4),
     typosquat recall ≥ 0.8 (F5). Capture `elapsed_ms`.
3. Record the **live-verified reference queries** into `docs/product/features.md` ("Pinned query
   semantics") and `docs/architecture/hydradb-notes.md` performance notes if you found surprises.

### Verification
```bash
pytest tests/integration/test_queries.py -q 2>&1 | tee .evidence/runs/phase-3/integration.txt
# latency: ensure the integration tests print per-query elapsed_ms; capture a p50/p95 summary
```
DoD: all tests green; latency p95 < 1 s (report real numbers; if over 1 s, reduce `max_hops` or
tune, document the change); queries documented where claimed.

### Handoff → §4.

---

## 4. Phase 4 — Researcher / Auditor / Adjudicator + abstention (timebox ≈ 2–3 h)

### Goal
A natural-language question reliably becomes a `QueryPlan`, and the pipeline returns either a
`Verdict` with evidence or an abstention — all deterministic, no LLM key.

### Read first
- `docs/architecture/decisions/ADR-0006-agents.md` (the design contract)
- `docs/architecture/components.md` — `src/intent.py`, `src/adjudicate.py`, `src/models.py`
- `docs/architecture/data-flows.md` — "Query / question flow", "Abstention path"
- `docs/product/glossary.md`

### Build
1. `src/models.py` — Pydantic: `IntentClass` (enum: BLAST_RADIUS, EXPOSED_SERVICES,
   RESOLVED_WHILE_LIVE, MAINTAINER_CONTAGION, TYPOSQUAT_CANDIDATES, PACKAGE_LOOKUP, UNSUPPORTED),
   `QueryPlan`, `QueryResult`, `Evidence`, `Verdict {answer, evidence_chain[], abstain:bool, reason}`.
2. `src/intent.py` — deterministic classifier: normalized tokens + entity regexes → intent class +
   params (`package`, `version`, `developer`, seed names). 6→N tests in `tests/unit/test_intent.py`.
3. `src/adjudicate.py`:
   - `Auditor.evaluate(plan, results)` → density score (evidence present vs expected), temporal
     consistency (resolved_at within window; recompute agrees), contradictions.
   - `Adjudicator.verdict(audit)` → answer or `abstain=True` with reason.
4. Abstention tests (`tests/unit/test_abstention.py`): 5 out-of-vocabulary questions → 5
   abstentions; empty-evidence → abstain; contradiction → both facts surfaced, then verdict/abstain.

### Verification
```bash
pytest tests/unit/test_intent.py tests/unit/test_abstention.py -q 2>&1 | tee .evidence/runs/phase-4/agents.txt
```
DoD: classification + abstention suites green; no LLM import required at runtime; `CHANGELOG` updated.

### Handoff → §4.

---

## 5. Phase 5 — UI + console (timebox ≈ 4–6 h)

### Goal
`streamlit run app.py` gives a judge a working console that takes a question and shows: the dark
live-query console panel (last Cypher, streaming), the thought-process traces, the verdict with
evidence chain, latency/cost badges, and a Plotly subgraph.

### Read first
- `DESIGN.md` — the full design language (colors, typography, components, do's/don'ts)
- `docs/ux/flows/index.md` — flow + DESIGN.md→Streamlit mapping
- `docs/product/features.md` — evidence chain / verdict rendering needs
- (skim) `GDELT-AQL-NetworkX-Agent/app.py` if available in the parent folder — port the
  thought-process + subgraph pattern, not the code

### Build
1. `assets/style.css` — mono stack (Berkeley Mono, JetBrains Mono, IBM Plex Mono, ui-monospace…),
   cream canvas, hairline sections, 4px radius, ASCII bracket bullets, dark console panel class,
   verdict color pills (#ff3b30 / #ff9f0a / #30d158 / #007aff).
2. `app.py` — Streamlit, `st.session_state` for conversation; left = question + verdict/evidence,
   right = thought-process + subgraph; the console panel renders the exact parameterized Cypher.
   Works fully without an LLM key. Plotly for subgraph (nodes colored by class; path highlighted).
   Handles `UNSUPPORTED` and `abstain` clearly (warning card).
3. Small `tests/unit/test_ui_smoke.py` if feasible (imports app module without launching).

### Verification
```bash
streamlit run app.py   # manual walkthrough; save 3+ screenshots to .evidence/runs/phase-5/
```
DoD: console answers the 3 demo questions; abstention visible for a nonsense question; DESIGN.md
fidelity (mono, canvas, hairline, one dark surface, semantic colors only for verdicts).

### Handoff → §4.

---

## 6. Phase 6 — Eval, README, video, submission readiness (timebox ≈ 3–5 h)

### Goal
Numbers a judge can trust, a repo a judge can run, and a submission that cannot be disqualified.

### Write
1. `scripts/eval.py` — hold out a subset of advisories; run queries with the same code paths as the
   app; compute precision / recall / F1 on exposed sets, p95 latency, queries-per-question, and
   (LLM off ⇒ 0) token cost. Emit a table into `docs/research/scoring.md`.
2. `README.md` — finalize quick start (must work from a clean clone), add the **"How We Used HydraDB"**
   section (what we lose if HydraDB were replaced by a vector store), attribution, license.
3. `docs/product/video-script.md` — 3-minute script: problem → project → live demo → HydraDB story.
4. Clean-clone verification: `git clone` fresh → `src/infra/hydradb-up.sh` → `pip install -r
   requirements.txt` → `python scripts/ingest.py` → `streamlit run app.py`. Capture the log.
5. Submission checklist in `vk/PLAN.md` §10 — check every box; file the Google Form hours early.

### Verification
```bash
python scripts/eval.py 2>&1 | tee .evidence/runs/phase-6/eval.txt
bash scripts/smoke.sh 2>&1 | tee .evidence/runs/phase-6/smoke-final.txt
pytest tests/unit tests/integration -q 2>&1 | tee .evidence/runs/phase-6/tests-final.txt
```
DoD: README instructions reproduce the demo; eval table real from `.evidence/`; no disqualified-flag.

---

## 7. Handoff report format (end of every phase)

```
PHASE: <N>
CHANGED FILES: <paths>
WHAT SHIPPED: <2-3 lines>
CHECKS RUN: <commands + PASS/FAIL>
EVIDENCE: <paths under .evidence/runs/phase-N/>
DEVIATIONS: <from DESIGN.md / PLAN.md / hydradb-notes.md, if any>
RESIDUAL RISKS: <max 3>
NEXT ACTION: <what Phase N+1 should start with; or STOP>
```

## 8. Rules of engagement (read once)
- One phase per session. Never scaffold "for later". Delete over accumulate.
- If HydraDB rejects something, adjust the query to `hydradb-notes.md` and note it — never fake.
- Never claim completion without fresh evidence files.
- If any stop condition in `AGENTS.md` fires, halt, and report it in the Handoff.