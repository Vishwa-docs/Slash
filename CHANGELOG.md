# Changelog

All notable changes. Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]
### Added
- **Console default project picks the newest real repo.** The React console no longer snaps
  back to the seeded demo project on refresh — it lands on the most recently added non-demo
  project (falling back to the demo repo only on a demo-only clone), so "add a repo" now
  visibly takes over the screen.
- **Onboarding tips (QTips) in the console.** A dismissible tip strip under the topbar walks a
  first-time user through «add» → «exposure scan» → "ask the graph", plus tooltip hints on both
  buttons; dismissed state is kept in localStorage and a "?" button reopens it.
- **TEAMMATES/teammates committed as a third project.** Real repo snapshot
  (`data/projects/teammates-teammates/`, OSV cache, 1,157 nodes / 1,053 versions / 51 advisories),
  registered in `data/projects.json` and synced on boot like the other projects.
### Fixed
- **Deterministic ground truth over the full committed graph, refreshed.** After adding
  TEAMMATES, `scripts/refresh_ground_truth.py` (the same computation `fetch_github.py --offline`
  runs) regenerated `ground_truth.json` over corpus + all project snapshots:
  **277 advisory records · 74 with live exposure · 12 distinct exposed services**. New pinned
  raw md5 `b7ab74be80e110c55abc55212e64023c`, verified byte-identical across repeated runs and
  identical after a second `refresh_ground_truth.py` invocation.
- **Live graph reconciles with truth after the new project.** Re-verified against the running
  HydraDB store: **0 exposure mismatches** across all 74 exposed advisory records; `debug@4.4.3`
  now correctly exposes **10** service records (TEAMMATES + demo repo + conf + 7 corpus services),
  blast radius **86** dependant versions. `tests/unit/test_ui_smoke.py` expectation updated to
  the regenerated truth (no test deleted or weakened).
- **Fresh demo numbers.** `.evidence/runs/product/` regenerated: exposure report
  **277 present · 12 services · 12 apps · 1124 live resolutions**; eval holds out the newest
  real exposed advisories (CVE-2025-24964, MAL-2025-46983) scoring **F1 1.00**, p95 ≈ 592 ms;
  scan/report/monitor/sbom/demo-qa refreshed; `vk/DEMO.md` narration updated so every number
  matches the screen.
- **GROQ key input removed from the console UI.** The console no longer asks for an LLM API key
  at first run; the backend still degrades to `GROQ_API_KEY` when present, keeping every path
  deterministic. The "dependency console" wording was dropped from the brand, tab title, and
  breadcrumb in favour of `slash / hydradb`.
- **Graph resets cleanly.** `.hydradb/store` wipe + `src/infra/hydradb-up.sh` + `python scripts/ingest.py`
  now yields a store whose live exposures EXACTLY match ground truth (0 of 33 advisory exposures
  disagree), after removing stale `DEPENDS_ON` debris left behind by superseded project
  generations. Evidence under `.evidence/runs/phase-6/`.
### Fixed
- **Fresh measured demo numbers.** After reconciling the graph with committed truth and
  re-verifying against the live store (see `.evidence/runs/product/demo-qa.txt` and
  `.evidence/runs/phase-6/eval.txt`): `debug@4.4.3` exposes **9** services (not 7) and has a
  **37**-dependant blast radius (not 15); console stats are **2,230 nodes · 217 malicious ·
  9 service repos · 238 advisory records**; eval p95 latency ≈ **200 ms** on held-out
  CVE-2026-47429 / CVE-2025-24964 (F1 1.00, 0 tokens). `vk/DEMO.md` narration updated so every
  number matches the screen.
- **README quick start matches the shipped console.** The documented console command is now
  `python scripts/serve.py --port 8501` (React SPA + product API), not `streamlit run app.py`,
  and the corpus is described as **9** real npm projects (was 12).
### Changed
- **Demo/launch hardening (React console).** Presentable state: stats row shows
  `services` (9) instead of the misleading `typosquats 0`; initial API load failures render a
  dedicated banner with a **retry** button instead of a raw `TypeError: Load failed`; health
  label degrades to "hydradb offline"; sidebar shows "resolving corpus…" while the overview loads;
  page title is now "Slash — dependency console on HydraDB".
- **Auth-token self-heal in the HTTP client.** `HydraDBClient` re-reads `.hydradb/auth.token`
  once on a 401 and retries — a stale server process can no longer wedge the demo after a
  HydraDB container/token refresh (observed live: `HTTP 401 unauthenticated` + client `Load failed`).
### Fixed
- **Honest OSV ground truth (demo-hardening).** `write_ground_truth` in `scripts/fetch_github.py`
  now filters each OSV advisory's `affected` list by the package name, matching the build path —
  killing false positives where a sibling package's range (e.g. `lodash.trimend` for
  GHSA-29mw-wpgm-hmr9) wrongly flagged the main package. Advisories drop 233 → 217, and the
  `lodash@4.18.1` chip is gone.
- **Deterministic demo chips.** `src/examples.py` sorts advisory chips by real exposed-service
  fan-out (debug@4.4.3 → 7, chalk@6.0.0 → 5) and the static blast chip now asks
  `What is the blast radius of debug@4.4.3?` (15 dependants) instead of the previously-abstaining
  `What depends on axios?`. `app.py` fallback chips match.
- **Offline manifest truthfulness.** `fetch_github.py --offline` now records the 9 real service
  repos in `manifest.repos` (was `[]`).
### Changed
- **Real-data pivot: the corpus is now the live GitHub/OSV supply chain, not synthetic.** All
  fabricated records (`scripts/gen_dataset.py`/`gen_fraud_dataset.py`, `data/generated/`,
  `data/fraud/`, `seed.toml`, the fake `oslo`/`sync@adv-*` advisories) are deleted.
  - `scripts/fetch_github.py` builds the graph from **real sources** for 12 well-known npm
    projects: npm registry versions, git-dependency names+versions+publish dates, lockfile
    pins + consumers (real repos), GitHub maintainers (via commit history from live clones),
    and real OSV advisory ranges for the actual package versions in those repos.
  - `data/github/{dataset.json,ground_truth.json,osv/}` is committed — full offline
    reproducibility via `passive --offline`, and honest advisory-derived labels
    (`malicious`, `exposed_services`, `resolved_while_live`) per snapshot version.
  - `scripts/ingest.py` defaults to the GitHub corpus (was: generated); `--offline` variants
    run with zero network; `scripts/scan.py` unused-file pruning of the corpus is retained.
  - `tests/integration/test_queries.py` and `test_product_api.py` are corpus-derived
    (assert vs `data/github/ground_truth.json`); `tests/integration/test_fraud_lens.py`
    replaced by `tests/unit/test_lens.py`; scan fixtures regenerated from real vulnerable
    pins (`data/scan-fixtures/` via `scripts/gen_scan_fixtures.py`).
  - Docs: README quick-start, this changelog. ADR-0005 (synthetic dataset) is superseded by
    ADR-0015 (real-data corpus); lens flag for the supply-chain vertical remapped to
    `dependency-graph`.
### Added
- **Domain lenses: one query engine, many connected graphs (ADR-0010).** The five
  primitives now run on any graph shape parameterized by `src/lens.py` — a fresh
  vertical is a Lens + dataset, not another query engine.
  - `src/lens.py` — `Lens` dataclass (node/relation labels, amenability property,
    answer vocabulary) with `SUPPLY_CHAIN` (flagship, byte-identical output) and
    `FRAUD` (AML/intake) shipped.
  - `src/graph_service.py` — all `plan_*`/`run_*` take `lens: Lens = SUPPLY_CHAIN`;
    the flagship's Cypher strings are unchanged (verified by diff against the
    pre-lens capture in `.evidence/runs/product/cypher-before.txt`).
  - `src/pipeline.py`, `src/adjudicate.py`, `src/intent.py` — lens-aware; intent
    scoring is now weighted (2× strong signal + 1× weak) so ambiguous phrasing
    ("during the intake window") no longer outranks a strong one ("which merchants
    were exposed").
  - `scripts/gen_fraud_dataset.py` + `data/fraud/` — deterministic fraud/AML graph
    (AccountState / Merchant / IntakeEvent / Customer; TRANSFERS_TO / FEEDS_INTO /
    INVOLVES / OWNS) with planted ground truth; `src/schema.py` gains FRAUD_* prop
    sets consumed by the existing idempotent `scripts/ingest.py --dataset fraud`.
  - Surfaces: `app.py` lens selector + fraud demo questions; `src/api.py` `/api/ask`
    & `/api/subgraph` accept `lens`; `scripts/serve.py --lens fraud`; `overview()`
    includes fraud stats + examples.
  - `tests/integration/test_fraud_lens.py` — fraud ground-truth suite (blast /
    exposed merchants / while-live recompute / customer contagion / typosquat
    recall / `compromised` lookup). 58 passed (41 unit + 17 integration);
    touched files ruff-clean.
  - Verified live on a fresh store: fraud blast `dependant_count=2` per advisory,
    exposed merchants == planted set, while-live recompute agrees, typosquat
    recall 1.00. Evidence: `.evidence/runs/product/{fraud-gt.txt,
    pipeline-fraud.txt, cypher-after.txt}`.
- **Product-grade console (Phase 8): stdlib JSON API + React frontend.** The Streamlit
  shell is superseded by a real product UI in the style of past DB-hackathon winners
  (Haven, CockroachDB×AWS winners).
  - `src/api.py` — zero-new-Python-deps HTTP server over the deterministic pipeline:
    `GET /api/health`, `GET /api/overview`, `POST /api/ask` (verdict + evidence chain +
    per-intent render payload), `POST /api/subgraph` (SVG-friendly neighborhood), plus
    static + SPA-fallback serving of `assets/app/dist` from one process.
  - `src/examples.py` — 9 live-validated demo questions + dataset overview stats read
    from the committed generated corpus (instantly, no traversal).
  - `scripts/serve.py` — `python scripts/serve.py [--port 8501]` runs the whole product.
  - `assets/app/` — React 18 + TypeScript + Vite + lucide-react, DESIGN.md tokens as CSS
    vars (Berkeley Mono, cream `#fdfcfc`, ink `#201d1d`, 4px radius, accent/danger/
    warning/success palette): sidebar sessions, curated question chips, evidence-chain
    expander, verdict cards per intent (exposed services / resolved-while-live /
    contagion / typosquat scoring bars / blast-radius hops / package lookup), and an SVG
    dependency-view panel. Build: `npm --prefix assets/app install && npm run build`.
  - `tests/unit/test_api.py` (degrades cleanly without HydraDB) +
    `tests/integration/test_product_api.py` (full ask/subgraph round-trip). 46 passed
    total (35 unit + 11 integration); `ruff check` clean.
  - Verified: demo battery through the product API on live HydraDB — oslo/base/ioauth/
    sync exposed services match ground truth, resolved-while-live recompute_agrees=true,
    typosquat scoring, blast radius, honest abstention. Evidence:
    `.evidence/runs/product/` (demo-qa.txt, pytest.txt, ruff.txt).
  - `.capabilities/registry.yaml` — added `cap.dev.node` and `cap.dev.react` (active);
    flagged Streamlit entry as superseded. No new Python runtime deps.
- **Real data feed (Track 02A challenge extension).** `scripts/fetch_real.py` + committed
  `data/real/` build the graph from live sources instead of the synthetic corpus:
  npm registry full docs (125 packages → 3,182 PackageVersions), real `npm install
  --package-lock-only` lockfiles for 5 apps (182 pins), and OSV API advisories (178
  real CVE/GHSA matches, per-version fix versions, publish timestamps). Same
  HydraDB shape as `scripts/gen_dataset.py`; `scripts/ingest.py real` loads it on an
  empty store (writes are already documented as empty-store-only). Verified live:
  `ws@6.2.2 → api-gateway, metrics-exporter`; `axios@0.21.1 → api-gateway,
  metrics-exporter`; `minimist@0.0.8 → data-ingest`; `jsonwebtoken@8.5.1 → auth-api`;
  `lodash@4.17.20` resolved-while-live recompute + contradiction detection. Evidence:
  `.evidence/runs/real-data/` (ingest + pipeline).
- Bug fixed while building the feed: advisory `fixed_version` was taken from the first
  range seen instead of the smallest fix above the vulnerable version (now correct:
  `express@4.17.1 → 4.19.2`, `lodash@4.17.20 → 4.17.21`, `axios@0.21.1 → 0.21.2`).
- Bug fixed: `(name, ver) in pkg_versions` always failed (tuple lookup against a
  str-keyed dict), silently dropping every DEPENDS_ON/RESOLVES_TO edge on real data.

### Added (Scaffold)
- Scaffold + control plane (AGENTS.md, docs, capabilities registry, state, CHG-0001).
- DESIGN.md design system installed (`getdesign` → terminal-native monospace aesthetic).
- HydraDB context graph built with graphify (`docs/research/hydradb-context-graph/`).
- Reference materials archived under `docs/reference/`.
- `vl/PLAN.md` and `vk/PROMPT.md` authored for the phased build.

### Phase 1 — Infrastructure (completed)
- `src/infra/hydradb-up.sh` — idempotent Docker bring-up (container `slash-hydra`, `.hydradb/auth.token`, healthz wait) + `stop` subcommand.
- `src/hydradb_client.py` — stdlib `urllib` HTTPS client: `healthz()`, `query()` with `parameters` body key, `QueryResult(rows, elapsed_ms)`, `HydraDBError`. Bolt path TODO noted (ADR-0003).
- `scripts/smoke.sh` — healthz → CREATE labeled probe → MATCH back → DETACH DELETE → no-injection check; all PASS (see `.evidence/runs/phase-1/`).
- `docs/architecture/hydradb-notes.md` — live-verified env/param/query deviations recorded (GRAPH_CELLS string values, `parameters` key, aggregates-on-property, labeled DELETE, CREATE one-hop only).

### Phase 3 — Query layer (completed)
- `src/graph_service.py` — pure `plan_*` builders + live `run_*` executors for F1–F5/F7: `blast_radius`, `exposed_services`, `resolved_while_live`, `maintainer_contagion`, `typosquat_candidates`, `fetch_subgraph`; every query parameterized + latency-captured, evidence-chain steps returned.
- `tests/integration/test_queries.py` — 7 tests vs `ground_truth.json`: exposed-set equality (F1/F2), while-live app match + recompute-flag agreement (F3), contagion (F4), typosquat recall ≥ 0.8 (F5), latency p95. All green (`.evidence/runs/phase-3/`).
- Live-verified HydraDB constraints recorded (hydradb-notes.md §Phase 3 + features.md pinned queries): 1024-row result cap, `IN $list` and UNWIND→node-lookup rejected, variable-length requires fixed source id (outgoing only), `count(DISTINCT …)` rejected.
- Latency: exposed-services 57 ms p50 / 58 ms p95; blast 4 ms; typosquat 72 ms — well under the 1 s budget.

### Phase 4 — Agents + abstention (completed)
- `src/models.py` — Pydantic `IntentClass`/`QueryPlan`/`Evidence`/`Verdict`.
- `src/intent.py` — deterministic Researcher: tokenized keyword/entity classifier → 6 intents + params (package/version/@dev_handle/seed names); `NON_PACKAGE` common-word guard keeps OOV questions UNSUPPORTED.
- `src/adjudicate.py` — Auditor (density + temporal recompute + contradiction detection) and Adjudicator (Verdict or first-class abstention, always with evidence chain).
- `src/pipeline.py` — `answer(client, question)` orchestrates classify → resolve version → run → audit → verdict.
- `tests/unit/test_intent.py` (17 cases) + `tests/unit/test_abstention.py` (5 OOV → 5 abstentions, empty-evidence → abstain, contradiction surfaces both facts). 25 green (.evidence/runs/phase-4/agents.txt).
- Verified live: all 6 intents answer; nonsense abstains with the capability message.

### Phase 6 — Eval, README, video, submission readiness (completed)
- `scripts/eval.py` — holds out the 2 most recent advisories, runs the exact app code path
  (`run_exposed_services` / `run_resolved_while_live`), and emits precision/recall/F1, p95 latency,
  queries-per-question, and token cost into `docs/research/scoring.md`. Result (live): F1 1.00 / 1.00,
  recall 1.00, p95 102 ms, 18 queries/question, 0 tokens (no LLM). Evidence: `.evidence/runs/phase-6/eval.txt`.
- **Bug fixed: dataset generator was not deterministic.** `pick_version` iterated a `set` (`self.names`),
  whose order is per-process hash-randomized, so the "seeded" RNG produced different graphs (and even
  different advisories) across runs. Fixed by iterating `sorted(self.names)`; verified identical SHA across
  3 consecutive runs (seed 20260812). Older recorded counts (phase-2/3/4 evidence, "notifications, search"
  demo text) referenced the pre-fix dataset; the regenerated dataset is now the single source of truth and
  the demo advertises the reproducible answer (`oslo@adv-2026-01-1.0.0` → exposed `gateway, notifications`).
- **Bug fixed: `resolved_while_live` recompute manufactured false contradictions.** The Auditor compared the
  stored live-flag (which exists only on the malicious version's RESOLVES_TO edge) against a transitive
  dependent's own publish/validity window. Recomputation is now restricted to direct resolutions of the
  malicious node; full suite re-verified (ADV-2026-03 recompute_agrees=true).
- **Bug fixed: `hydradb-up.sh` could leave a fresh clone 401-unauthenticated.** The "already up" path now
  refreshes the local `auth.token` from the running node; verified in the clean-clone run.
- **Verified `CREATE`/`DETACH DELETE` are an empty-store-only write path** (500 internal error on a populated
  store; 7/7 PASS on a fresh store). `scripts/smoke.sh` split into default read-only mode and `--write-probe`
  mode; documented in `docs/architecture/hydradb-notes.md` §Phase 6.
- `README.md` — final quick start (clean-clone reproducible, `hydradb-up.sh`), full "How We Used HydraDB"
  section with the vector-store-can't-do-this argument, traversal screenshots.
- `docs/product/video-script.md` — 3-minute script: problem → project → demo → HydraDB story.
- Clean-clone verification (`.evidence/runs/phase-6/clean-clone.txt`): fresh copy → up → pip install → gen
  (deterministic) → ingest → pipeline answers → 36 tests green → Streamlit HTTP 200.
- Final verification: `pytest tests/unit tests/integration` 36 passed; `scripts/smoke.sh` read-only 3/3 PASS;
  `scripts/smoke.sh --write-probe` 7/7 PASS on empty store; UI smoke via Streamlit AppTest renders
  exposed-services verdict + abstention deterministically (`tests/unit/test_ui_smoke.py`).

### Phase 5 — UI + console (completed)
- `assets/style.css` — DESIGN.md tokens as CSS vars: Berkeley Mono stack, cream canvas `#fdfcfc`, ink `#201d1d`, hairline sections, 4px radius, dark `.console-panel`, verdict pills (`#ff3b30`/`#ff9f0a`/`#30d158`/`#007aff`), ASCII bracket bullets.
- `app.py` — Streamlit console: left = question + verdict/evidence chain (Cypher + params + rows table + latency), right = thought-process + live-query console + Plotly subgraph (seed red, blast-green). `st.session_state` history; `?q=` query-param seeding for shareable/scriptable demos; runs fully without an LLM key; `UNSUPPORTED`/`abstain` render a warning pill.
- `src/pipeline.py` — added `answer_with_result(client, question) -> (Verdict, result)` so the UI can render the real rows (no fake/empty evidence); `answer()` kept for tests.
- `src/graph_service.py` — subgraph queries no longer ask RETURN for `labels(...)` (unsupported: only `<binding>.<property>` or count(*)); label derived from traversal context instead.
- `tests/unit/test_ui_smoke.py` — app module imports + CSS tokens present; green.
- Verified: headless end-to-end (verdict `notifications, search` · 18-step chain · 1-neighbour subgraph), Streamlit server HTTP 200 + health ok, 4 screenshots (landing / exposed / blast / abstain) under `.evidence/runs/phase-5/`.
### Phase 2 — Schema, Dataset, Ingest (completed)
- `src/schema.py` — single source of truth: node/edge labels + property sets, `valid_until` timestamp added to `PackageVersion` for window semantics.
- `scripts/gen_dataset.py` — deterministic synthetic npm-style dataset (seed.toml): 4 distinct malicious-version advisories with direct + multi-hop exposure, 7 typosquats (deprecated, `is_typosquat=true`, false-positive safe), tight blast radii, giant false-friendly `left-pad` sink, lockfiles pinned to 2026-07-11.
- `data/generated/{dataset.json,ground_truth.json,seed.toml}` — reproducible artifacts; ground truth is honest (recency-filtered, ≥2 severity consumers, ≤6 hop radius).
- `scripts/ingest.py` — idempotent UNWIND batch upserts via `MERGE` by node id / edge id; re-runnable without duplicates.
- Evidence: `.evidence/runs/phase-2/` (ingest counts, re-ingest idempotency, spot-check). Counts: 607 Package / 2001 PackageVersion / 400 Developer / 15 Service / 40 Lockfile; 12160 DEPENDS_ON / 311 RESOLVES_TO / 40 USES_LOCKFILE / 2105 MAINTAINED_BY; 4 malicious, 7 typosquats.
- Live-verified HydraDB constraints recorded for Phase 3: `count(DISTINCT ...)` and node-only `MATCH (n)` rejected; variable-length paths require a fixed literal source id with outgoing-only traversal — reverse (incoming) blast radius must be computed level-by-level (see `.evidence/runs/phase-2/closure-note.txt`).