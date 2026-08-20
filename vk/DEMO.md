# Slash — Demo Video Script (Hack Hydra 2026 · Track 02A)

**Title:** *Slash — supply-chain blast radius on HydraDB. Real GitHub + npm + OSV data, queried live.*

**Target runtime:** 4:30–5:00
**All data is real.** Nothing below is fabricated, stubbed, or pre-seeded by the hand. Every number was
re-verified against the live HydraDB store on 2026-08-20 (see `Evidence` column → files under
`.evidence/runs/product/`). If a number ever disagrees with the screen, the screen wins — fix the line,
don't fake the shot.

---

## 0. Pre-flight checklist (run BEFORE you press record)

```bash
# 1. HydraDB up (Docker), idempotent
bash src/infra/hydradb-up.sh
#   expect: "hydradb ready" / healthz ok

# 2. Corpus + GT rebuilt offline (deterministic, md5-pinned)
python scripts/fetch_github.py --offline
#   expect: offline rebuild: nodes=2230 edges=5714
#   ground_truth.json md5 stays b7ab74be80e110c55abc55212e64023c on every run

# 3. Ingest (idempotent — safe to show twice)
python scripts/ingest.py
#   expect: Package 228 · PackageVersion 1692 · Developer 292 · Service 9 · Lockfile 9
#           DEPENDS_ON 177 · RESOLVES_TO 256 · USES_LOCKFILE 9 · MAINTAINED_BY 5272

# 4. Console (React SPA + API in one process — the screen you're presenting)
python scripts/serve.py --port 8501     # open http://127.0.0.1:8501
#   status shows a green dot "connected"; stats row appears under the topbar
```

Also make sure the demo battery is green right before recording:

```bash
python scripts/gen_demo_qa.py       # -> .evidence/runs/product/demo-qa.txt  (7 Q/A, all real)
pytest tests/unit tests/integration -q   # 49 passed
```

Screen hygiene:  2-pane layout — left terminal, right browser. Terminal at 120×34, font 14+, no
scrollbars. Record from a clean tab of `data/scan-fixtures` open so Scene 5 has something to scan.

---

## 1. Why HydraDB? (the three beats to say, twice — hook and close)

Keep these short, concrete, and **paired with what's visible on screen**. Never say "graph database = better"
alone; anchor it:

1. **The question IS a traversal.** "Which of *my* services are transitively exposed?" is: seed a package
   version, walk reverse `DEPENDS_ON` up to 6 hops, then intersect with `Service ← USES_LOCKFILE ← Lockfile
   → RESOLVES_TO`. That's a bounded, variable-length graph traversal — the property a vector/key-value store
   physically cannot express. A KV store gives you one edge; we walk thousands.
2. **Edges carry time.** `RESOLVES_TO` edges store `at` + `was_resolved_while_live`; versions store
   `published_at` / `valid_until`. "Was the bad version resolved *while the advisory was live*" is a
   predicate on the graph, not a log join you bolt on later.
3. **Idempotent by construction.** Ingestion uses `MERGE` upserts — shown twice, same counts, same nodes.
   Reproducible from a committed snapshot offline (md5-pinned). Honest permits dishonest failure modes:
   first-class **abstention** + a self-heal log when the graph genuinely can't answer.

Real Cypher to flash during the narration (from the evidence chain — not a demo-only reimplementation):

```cypher
MATCH (u:PackageVersion)-[:DEPENDS_ON]->(v:PackageVersion {id: $id})
RETURN DISTINCT u.id, u.name, u.version        -- bounded ≤6-hop reverse hop

MATCH (s:Service {name: $svc})-[:USES_LOCKFILE]->(lf:Lockfile)-[r:RESOLVES_TO]->(v:PackageVersion)
RETURN lf.app, v.name, v.version, r.at, r.was_resolved_while_live   -- temporal predicate
```

---

## 2. Shot list (record in order)

### Scene 0 — Cold open (0:00 – 0:20)
| Cue | On screen | Narration (≈ verbatim) |
|---|---|---|
| Camera on you / intro card | — | "In 2025 an npm package called *chalk* — 300 million weekly downloads — shipped a malicious 6.0.0 release. An advisory went out. The hard question is never 'is chalk bad'. It's: **which of MY services is transitively exposed?** Counting across a 2,300-node dependency graph, by hand, is impossible. That's what we built." |

### Scene 1 — Real corpus, real store (0:20 – 1:10)
| Cue | On screen | Narration |
|---|---|---|
| `hydradb-up.sh` runs | Docker starts `slash-hydra`, "ready" line | "Slash runs entirely on HydraDB — a graph store. First, bring it up." |
| `fetch_github.py --offline` | rebuilds dataset + GT, prints `nodes=2230 edges=5714` | "Our corpus is **real** GitHub projects, real npm versions, real OSV advisories: real OSS repos shipped as nine service apps, 1,692 package versions, 292 real maintainers from commit history, 277 OSV advisory records with honest labels (217 of them malicious versions). Nothing fabricated — and the whole thing rebuilds offline, byte-identical." |
| `ingest.py` (run it, then run it AGAIN) | label counts print identically twice | "Ingestion is idempotent — `MERGE` upserts keyed by node and edge id. Same input, same store, twice — exactly the same numbers. That reproducibility is what makes the answers below trustworthy." |

### Scene 2 — The money shot: exposed services + blast radius (1:10 – 2:10)
| Cue | On screen | Narration |
|---|---|---|
| Open http://127.0.0.1:8501 | proxies list in the sidebar (demo repo, `sindresorhus/conf`, `TEAMMATES/teammates`); stats row from the active repo; real question chips; green **connected** dot | "Here's the console. The sidebar lists the tracked repos — the two project seeds plus any you add with «add» — and the stats row on top is read straight from the live graph. Every repo you add lands here with its own dependency graph, advisories, and sessions." |
| Click chip **"Which services are exposed by debug@4.4.3?"** | pill `EXPOSED_SERVICES`; 10 service pills | "Ask the top chip — it's generated from real advisories that actually have live exposure. `debug@4.4.3` — its real CVEs — reaches **ten** service records in the graph: the synced repos (TEAMMATES, reefguard, conf) plus axios, express, fastify, passport, marked, lowdb and ws. One compromised package, ten apps touch it." |
| **Click "evidence chain… N queries · M rows examined"** | the reverse-hop Cypher + row counts, `-- params` | "Here's the received truth — the actual traversal HydraDB executed. Not a canned answer: every hop is a query against the live graph, chained up to 6 deep, with its row counts and latency." |
| Click chip **"What is the blast radius of debug@4.4.3?"** | `86 transitive dependants within 6 hops` + hop levels + **dependency view** SVG (red root, neighbours) | "Now the full blast radius — **86 dependent versions within 6 hops** — and the dependency view below renders that subgraph around the seed node. This is the query a vector store simply can't answer — there's no embedding that encodes a bounded walk." |
| Click chip **"Which services are exposed by chalk@6.0.0?"** | `EXPOSED_SERVICES`; 5 service pills | "The chalk 6.0.0 malware advisory — real `MAL-2025-46969` from our OSV feed — reaches five services today. One compromised package, five live apps." |
| Click chip **"Which apps resolved lodash@4.17.20 while it was live?"** | `RESOLVED_WHILE_LIVE`; 1 lockfile row with `LIVE` pill; "live-flag recheck confirms…" | "But the past matters too: did an app resolve the bad version *while it was live*? The edge stores `resolved_at` and the live flag — and Slash **recomputes** that flag from temporal properties instead of trusting a stored boolean. They agree." |

### Scene 3 — Maintainer contagion + typosquats + lookup (2:10 – 2:55)
| Cue | On screen | Narration |
|---|---|---|
| Ask **"Which packages are maintained by the maintainer nicolo-ribaudo?"** | `@babel/core, @babel/preset-env` (2 packages) | "Maintainer contagion: one real Babel maintainer owns two core packages — a compromised account spreads through identity, not just edges." |
| Ask **"Is avvio a typosquat of axios?"** | `avvio (score 1.15)` | "Typosquat candidates via edit-distance over real package names. `avvio` scores 1.15 against `axios`." |
| Ask **"What is the latest version of chalk?"** | `chalk@6.0.0 … malicious=True (MAL-2025-46969)` | "Package lookup against the real registry metadata — and note it **tells you** the latest chalk is the malicious one." |

### Scene 4 — Abstention & self-heal (2:55 – 3:35)
| Cue | On screen | Narration |
|---|---|---|
| Ask **"Tell me about the weather in jakarta"** | pill `not found · reported`; reason under the card; no evidence chain | "What if the graph doesn't have the answer? Slash **doesn't invent one**. It stays silent — and reports *why*." |
| Open `data/report/support-requests.json` | the logged gap: question, intent, reason | "The gap is written to the self-heal support report. In production, that's the hook for 'go fetch this data'. First-class abstention — not a hallucination." |

### Scene 5 — Product streams out of the graph (3:35 – 4:20)
| Cue | On screen | Narration |
|---|---|---|
| Click **"exposure scan"** in the console topbar — the report is scoped to the active repo (for TEAMMATES: `51 advisories present · 1 service · 716 live resolutions`) | project-scoped advisory report with per-package rows | "The exposure report is scoped to the repo you're looking at — here TEAMMATES: 51 advisory-records, each with its resolved-while-live history." |
| `python scripts/report.py --out report.json` | `277 advisories present · 12 services exposed · 12 apps at risk · 1124 live resolutions` | "Across the whole graph: **277 advisory records, 12 services exposed, 1,124 resolution events that happened while the bad version was live.** That's the supply-chain surface, one report." |
| `python scripts/scan.py --dir data/scan-fixtures` | `2 apps, 5 pins, 3 malicious resolved, 32 typosquat flags` | "Scan a fresh lockfile against the live corpus — it resolves every pin and calls out the malicious ones: chalk@6.0.0 and debug@4.4.3." |
| `python scripts/monitor.py --watchlist watchlist.toml` | `1 violation: avvio (0.75) looks like axios` | "Continuous monitoring of the four packages we ship watchlist entries for. One open typosquat violation." |
| `python scripts/export_sbom.py --app lodash/lodash` | 26 components; `slash:malicious` on chalk@6.0.0, dojo@1.17.3, lodash@4.17.20, request@2.88.2 | "And we emit a CycloneDX SBOM — annotated straight from the graph with the malicious and deprecated components." |
| `python scripts/eval.py` | `F1 1.00` on CVE-2025-24964, MAL-2025-46983 | "But is it *right*? We hold out the most recent real advisories that actually exercise exposure and run the exact app code path against ground truth derived from OSV. **F1 = 1.00** on both, p95 latency ≈ 600 ms, zero token cost — the core is fully deterministic, no LLM in the loop." |

### Scene 6 — Close (4:20 – 4:30)
| Cue | On screen | Narration |
|---|---|---|
| Back to console, or an end card | — | "Slash is a thin analytical layer over HydraDB. Every answer is a live traversal; the temporal edges make forensics possible; `MERGE` makes it reproducible; abstention makes it honest. **Ask the graph — it's the only way to answer a transitive question.**" |

---

## 3. Word-for-word guardrails (read while recording)

- Say **"real GitHub projects, real npm versions, real OSV advisories."** Never say "sample", "mock", "demo data".
- The corpus ships **nine real OSS service repos** (axios, express, fastify, marked, p5.js, passport, ws, lowdb, lodash — each a real GitHub project). Say that, it's true; do not say "12".
- **277 advisory records, 217 malicious versions**: the graph holds 277 OSV advisory *records*; of those, 217 are *malicious versions*. Say "277 advisories, 217 malicious" and don't mix the two. The console's per-repo `adv` badge shows that repo's own advisory count.
- Latency: p95 ≈ 600 ms in the eval run (individual console queries are tens-to-low-hundreds of ms). Say "a few hundred milliseconds", never a specific number you didn't just see.
- The **lodash@4.18.1 sabotage storyline is NOT in this build** (that version is not flagged as vulnerable in the
  honest ground truth). Do not improvise it.
- "chatbot" is the wrong word. It's a **query console / dependency intel platform** with an evidence chain.
- If a question ever returns `NOT FOUND`, that's a feature — narrate it as abstention (Scene 4), don't restart.

## 4. After recording

1. **Regenerate the stale README screenshots** — the four PNGs in `docs/ux/screenshots/` (landing/blast/
   exposed/abstain) are from before the real-data pivot. Re-capture during the recording and overwrite:
   - `docs/ux/screenshots/landing.png` — console, top, chips visible
   - `docs/ux/screenshots/blast.png` — debug@4.4.3 blast radius with subgraph
   - `docs/ux/screenshots/exposed.png` — debug@4.4.3 exposed-services + evidence expander
   - `docs/ux/screenshots/abstain.png` — weather-in-jakarta `NOT FOUND` pill
2. Save the recording as `Slash-<date>.mp4` next to this file; drop a one-line reference in `CHANGELOG.md`
   under Unreleased → Changed.
3. Re-run `pytest` + `ruff` after any re-capture and refresh `.evidence/runs/product/pytest.txt` /
   `ruff.txt` if files changed.

## 5. Evidence (everything claimed above, verifiable in-repo)

| Claim | File |
|---|---|
| 7 Q/A battery, real answers | `.evidence/runs/product/demo-qa.txt` |
| Exposure report: 277 present, 12 services, 12 apps, 1124 live | `.evidence/runs/product/exposure-report.json` |
| Scan: 2 apps, 5 pins, 3 malicious, 32 typosquat flags | `.evidence/runs/product/scan-report.json` (+ `.html`) |
| Monitoring: 4 watches, 1 violation (avvio→axios) | `.evidence/runs/product/monitor-violations.json` |
| SBOM: 26 components + flags | `.evidence/runs/product/sbom-gateway.json` |
| Eval: F1 1.00 on held-out real CVEs (CVE-2025-24964, MAL-2025-46983) | `docs/research/scoring.md`, rerun via `python scripts/eval.py` |
| 49/49 tests, lint clean | `.evidence/runs/product/pytest.txt`, `ruff.txt` |