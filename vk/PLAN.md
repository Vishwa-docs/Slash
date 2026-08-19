# Slash — Master Plan

**Hack Hydra 2026 · Track 02 — Repos, Dependencies + Code as Graphs (option A: Supply chain blast radius)**
Deadline: **Aug 20, 2026, 11:59 PM PT** (build window Aug 12–20; today is Aug 19 → ~36 h to go).

> This file is the product plan. The executable instruction set for the coding agent lives in
> `vk/PROMPT.md`. The UI source of truth is `DESIGN.md`. Any conflict between files → stop and report.

---

## 1. Executive summary

We build **Slash**: a blast-radius intelligence console for the software supply chain powered
by **HydraDB**. It ingests an npm-style package ecosystem (plus planted, OSV-flavored advisories)
into HydraDB, then answers the questions a security team asks in the first minutes of a
compromise — *which internal services are transitively exposed, which apps resolved the bad
version while it was live, which packages share maintainers, which names are likely typosquats,
what is the complete blast radius* — with a **traceable evidence chain** and **first-class
abstention**.

**Why this track wins:** a blast radius is a *transitive reverse-dependency closure* — a
topological query a vector database physically cannot express. That is the strongest possible
"Best Use of HydraDB" story, it has objective scoring (precision/recall/latency/cost), it does
not depend on an LLM, and the reference implementation (the GDELT GTC-2025 first-place agent)
proves the winning formula we are porting.

## 2. Track decision and rationale

| Criterion | 02A Supply chain | 01 Ontology | 03 Memory |
|---|---|---|---|
| Pure graph problem (vector can't do it) | ★★★ (transitive closure) | ★★ (mostly LLM entity resolution) | ★★ (LLM-centered) |
| Objective score to show judges | ★★★ precision/recall/latency/cost | ★★ vibes | ★★ LongMemEval (heavily LLM) |
| Self-contained / offline / cheap | ★★★ (synthetic dataset) | ★★ 500K docs, big LLM bill | ★★ long histories, big LLM bill |
| "What would we lose without HydraDB" clarity | ★★★ | ★★★ | ★★★ |
| Build risk in remaining hours | ★★ | ★★ | ★★ |

**Decision: Track 02A.** (ADR-0001)

## 3. Competitive strategy (prior art → mechanics)

From the strategy analysis and the deconstructed GDELT first-place winner, the winning mechanics are:

1. **Dynamic tool routing** — one natural-language query maps to multiple analytic engines. Ours:
   Researcher routes to graph traversals (blast radius / forensics / contagion / typosquat).
2. **Deep technical moat** — recursive graph traversal & topological analysis a vector DB can't do.
3. **Reliability via abstention** — refuse to answer when the data isn't there.
4. **Verifiable evidence** — show the Cypher + rows behind every verdict.
5. **Polished UI** — Streamlit console with a live "thought process" + subgraph visualization
   (port the GDELT formula), rendered in `DESIGN.md`'s terminal-native aesthetic.
6. **Enterprise anchor** — supply-chain security is 2026 VC gravity (NetRise $10M, SAFE $70M+).

## 4. Feature set

Must (F1–F8), Should (S1–S6), Could (C1–C3), Won't (W1–W4). **Full table: `docs/product/features.md`.**
The demo-critical core:

| Feature | What it proves |
|---|---|
| F1 Transitive blast radius | The graph traversal a vector DB cannot perform |
| F2 Exposed services | End-to-end: `Service→Lockfile→RESOLVES_TO→…→compromised` |
| F3 Resolved-while-live forensics | Temporal edges + window filtering (live-ness) |
| F4 Maintainer contagion | Human/infra identity edges |
| F5 Typosquat candidates | Reputation + name-similarity signals |
| F6 Honest abstention | "Not in the data" as a first-class result |
| F7 Evidence chain | Cypher + params + rows + latency, always rendered |
| F8 Deterministic pipeline | Regenerable dataset + ground truth, offline |

## 5. Architecture

Diagrams: `docs/architecture/index.md`, `system-context.md`, `containers.md`, `components.md`.

```
Streamlit console (app.py)
   │  NL question
   ▼
Researcher (intent.py) ──► QueryPlan (labeled, params, budget)
   ▼
graph_service.py         ──► parameterized OpenCypher builders (F1–F5)
   ▼
hydradb_client.py        ──► POST /v1/graphs/default/query  (127.0.0.1:8443)
   ▼
Auditor (adjudicate.py)  ──► density / temporal / contradiction checks
   ▼
Adjudicator              ──► Verdict + evidence chain  |  abstention
   ▼
app.py                   ──► verdict badge, dark console-panel (live query), subgraph plot
```

**Design docs:** `docs/architecture/hydradb-notes.md` (verified HydraDB surface),
`docs/architecture/decisions/ADR-0001…0007`.

### 5.1 HydraDB data model

```
Service -[:USES_LOCKFILE]-> Lockfile -[:RESOLVES_TO]-> PackageVersion <-[:DEPENDS_ON]- PackageVersion ... 
PackageVersion -[:MAINTAINED_BY]-> Developer
```

- Edge + node properties carry time: `valid_from`, `valid_until` (sentinel 9999999999 = live),
  `published_at`, `resolved_at`. Deprecation = SET, never DELETE.
- Booleans (`malicious`, `popular`, `is_typosquat`, `deprecated`) filter via `= true` (no `IS NULL`).
- Traversal: bounded `[:DEPENDS_ON*1..6]` (ADR-0007); aggregates `count/collect`; `UNWIND` batches for ingest.

### 5.2 The five core queries (to be finalized & live-verified in Phase 3)

1. **Blast radius / exposed services** — reverse closure from the compromised version up through
   `RESOLVES_TO` to `USES_LOCKFILE`, dedup services, count.
2. **Resolved-while-live** — `WHERE lf_resolved_at >= bad.published_at AND lf_resolved_at <= bad.valid_until`,
   with a precomputed `was_resolved_while_live` flag as belt-and-suspenders.
3. **Maintainer contagion** — developers shared with the compromised package + all packages they maintain + transitive deps.
4. **Typosquat candidates** — graph signals (in-degree, maintainers, recency, orphaned) joined with
   name edit-distance against `popular` packages (scoring in Python).
5. **Package lookup / abstention gate** — does the entity exist, how dense is the neighborhood.

## 6. Data & ground truth

- `scripts/gen_dataset.py` produces a seeded, reproducible npm-style ecosystem and
  `data/generated/ground_truth.json` (advisories + true exposed sets + typosquats).
- Scale target: ~600 packages / ~1.8k versions / ~400 developers / ~15 services / ~40 lockfiles →
  enough that the blast radius is non-trivial, small enough for sub-second latency.
- Planted: 3–4 advisories, 5–8 typosquats, 1–2 contagion chains. Held-out subset = "recent advisories".
- Ingest = `UNWIND` batches (500 rows) with `MERGE` by integer `id`; idempotent (re-run safe).
- The schema mirrors what a real CycloneDX/SBOM pipeline would produce, so C1 (real SBOM ingest)
  drops into the same store. README discloses synthetic provenance (ADR-0005).

## 7. Multi-agent design (Researcher / Auditor / Adjudicator)

Ported from the LegalGraphRAG + GDELT pattern, kept deterministic-first (ADR-0006):

| Agent | Job | Implementation |
|---|---|---|
| Researcher | NL → ordered query plan | `intent.py`: keyword/entity classification → six intent classes → `QueryPlan`; optional Pydantic-validated LLM refine (OFF by default) |
| Auditor | Prove or refute the evidence | density threshold, temporal consistency, contradiction detection |
| Adjudicator | Verdict or abstain | `Verdict` model with `abstain:bool`, `reason`, `evidence_chain[]` |

Abstention paths: (a) intent not in vocabulary → decline; (b) evidence too sparse → abstain;
(c) contradiction → show both + authority/temporal reasoning; (d) budget exceeded → abstain with cost note.

## 8. UI design (DESIGN.md)

`DESIGN.md` (from `getdesign opencode.ai`) is the source of truth: 100% monospace (Berkeley Mono →
JetBrains Mono → ui-monospace stack), cream canvas `#fdfcfc`, ink `#201d1d`, hairline sections,
4px radius interactive, ASCII bracket bullets, one dark "console" surface. We apply it as a
**security console**:

- Dark `/hero-tui-mockup` → the **live-query console panel** (last Cypher, streaming, metrics).
- Semantic colors only for verdicts: danger `#ff3b30` (exposed), warning `#ff9f0a` (typosquat/abstain),
  success `#30d158` (clean), accent `#007aff` (links).
- Thought-process panel (Researcher→Auditor→Adjudicator traces) + Plotly subgraph (nodes colored by
  class/path). Streamlit realized via a small `assets/style.css` + `st` components (`docs/ux/flows/index.md`).

## 9. Execution plan (compressed to the remaining ~36 h)

Real window: **Phase 1 → now; Phase 6 → before ~20:00 PT Aug 20.** Each phase has full task detail
+ Definition of Done in `vk/PROMPT.md`.

| Phase | Scope | Timebox | Where |
|---|---|---|---|
| **P1 Infra** | Docker HydraDB up; `src/hydradb_client.py`; smoke green | 2–3 h | `src/infra/hydradb-up.sh`, `src/hydradb_client.py`, `scripts/smoke.sh` |
| **P2 Data** | Schema; `gen_dataset.py`; `ingest.py`; graph populated | 3–4 h | `scripts/`, `data/generated/` |
| **P3 Queries** | `graph_service.py` F1–F5 + integration tests | 3–4 h | `src/graph_service.py`, `tests/integration/` |
| **P4 Agents** | `intent.py`, `adjudicate.py`, abstention tests | 2–3 h | `src/`, `tests/unit/` |
| **P5 UI** | `app.py` per DESIGN.md; console, evidence, subgraph | 4–6 h | `app.py`, `assets/`, `docs/ux/` |
| **P6 Ship** | eval → scoring.md; README "How We Used HydraDB"; video script; clean-clone re-run; submit | 3–5 h | `scripts/eval.py`, `README.md`, `.evidence/` |

Ordering rules when time is short (from participant guide): *"Stop adding features before the
deadline. Test what you already built."* Priority: P1→P3 (the queries are the product) → P5 lite
(working console) → P6 (submission win). P4 agents are a differentiator, never a blocker.

## 10. Definition of done (submission checklist)

From `docs/reference/hack-hydra-participant-guide.txt` + our plan:

- [x] Public GitHub repo, open-source license, `README.md` with setup + HydraDB usage + env + attribution.
- [ ] No participant-authored commits before **Aug 12, 2026** — repo currently uncommitted; first commit is
      Aug 2026 (after the freeze date), pending the team's commit/push.
- [x] HydraDB **meaningfully integrated**: every answer is a live graph traversal w/ evidence chain.
- [x] Working demo (quick-start reproduces in < 2 min) — verified from a clean clone (`.evidence/runs/phase-6/clean-clone.txt`).
- [ ] ≤ 3-min video: problem → project → live demo → "where HydraDB is used & why it matters" — script
      written (`docs/product/video-script.md`); recording + upload is a team/device step.
- [ ] Google Form before deadline; submit hours early (buffer for platform latency) — human step; file it early.
- [x] `scripts/smoke.sh` + unit/integration tests green; eval table real (from `.evidence/runs/phase-6/` +
      `docs/research/scoring.md`).
- [x] "How We Used HydraDB" README section + traversal screenshots (`docs/ux/screenshots/`).

## 11. How to navigate this repo

```
README.md                → quick start + one-paragraph story
vl/PLAN.md               → this file (strategy → execution)
vk/PROMPT.md             → the coding agent's phased task packet
DESIGN.md                → UI design system
docs/architecture/       → context → containers → components → data flows → trust boundaries
docs/architecture/hydradb-notes.md  → the verified HydraDB API subset (rules of the road)
docs/architecture/decisions/        → ADRs
docs/product/            → vision, features, personas, glossary, roadmap, requirements
docs/research/hydradb-context-graph/GRAPH_REPORT.md → graphify knowledge-graph of HydraDB source
docs/research/scoring.md → eval methodology (numbers land in Phase 6)
docs/security/ · docs/ux/ · docs/testing/ · docs/operations/ → per-area
changes/CHG-0001/        → change record, risks, test plan
.capabilities/ · .state/ · .evidence/ · .agents/ · .radar/  → control plane (factory-brief system)
```