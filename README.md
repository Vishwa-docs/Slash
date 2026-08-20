# Slash

> **Blast-radius intelligence for the software supply chain, computed natively in HydraDB.**

Slash ingests an npm-style package ecosystem into [HydraDB](https://github.com/hydra-db/hydradb)
(a graph database on object storage) and answers, in real time, the questions a security
team needs when a package is compromised at 09:00 and services are exposed by 09:06:

- Which internal services are **transitively exposed**?
- Which apps **resolved the bad version while it was live**?
- Which packages share **maintainers** or infrastructure with the compromised one?
- Which nearby names are likely **typosquats**?
- What is the **complete blast radius**?

Answers arrive with a **traceable evidence chain** — the exact Cypher query and subgraph that
produced the result — and the system **abstains explicitly** when the data is not in the graph.

Built for **Hack Hydra 2026, Track 02 — Repos, Dependencies + Code as Graphs (option A)**.

## Why a graph database

Blast-radius is a **transitive reverse-dependency closure** over a graph of tens of millions
of versioned nodes. That is a topological traversal a vector index cannot perform at all.
This project exists to show HydraDB doing exactly the traversal a vector database physically
cannot.

## Highlights

| Capability | How it uses HydraDB |
|---|---|
| Transitive blast radius | Bounded variable-length reverse `DEPENDS_ON` traversal |
| "Resolved while live" forensics | Temporal edge properties (`resolved_at`, `published_at`) filtered in `WHERE` |
| Maintainer contagion | Traversal through `MAINTAINED_BY` identity nodes |
| Typosquat hunting | Graph signals (reputation, maintainers, in-degree) + name-similarity scoring |
| Abstention | Subgraph density gate before any answer is rendered |

## Repository map

```
vl/PLAN.md           Full plan (strategy, architecture, features, execution)
vk/PROMPT.md         Phased task packet for the coding agent
DESIGN.md            UI design system (terminal-native monospace aesthetic)
docs/                Architecture, product, security, ADRs, research
docs/research/hydradb-context-graph/  Graphify knowledge graph of the HydraDB codebase
src/                 Application code (client, query service, agents, UI)
scripts/             Dataset generation, ingestion, eval, smoke tests
data/                Committed real corpus (data/github) + scan fixtures
tests/               pytest suites per risk tier
changes/             Change records (CHG-0001 …)
```

## Quick start

The full flow takes under two minutes from a clean clone against a machine with Docker and Python 3.11+.

```bash
# 1. Bring up HydraDB (Docker) — idempotent, waits for healthz
bash src/infra/hydradb-up.sh
#    (stop later with: bash src/infra/hydradb-up.sh stop)

# 3. Fetch & ingest the REAL GitHub/OSV corpus (no fabricated records)
python scripts/fetch_github.py     # commits data/github/ (dataset, ground truth, OSV advisories)
python scripts/ingest.py           # idempotent — safe to re-run
#    (offline variant — a committed snapshot ships in this repo, byte-identical:
#     python scripts/fetch_github.py --offline && python scripts/ingest.py)

# 4. Run the console (React SPA + product API in one process)
python scripts/serve.py --port 8501   # open http://127.0.0.1:8501
```

All data is real: package versions, dependency edges, maintainers, and vulnerability
advisories are pulled from GitHub's public dataset + OSV for 9 well-known npm projects
(npm registry + GitHub API + OSV need `GH_TOKEN`; `data/github/` restores the exact corpus
offline). Ask real questions, e.g. `which services are exposed by chalk@6.0.0`,
`what is the blast radius of lodash@4.16.6`, `was debug@4.4.3 resolved while live`,
`who maintains express`, or a nonsense question to see first-class **abstention**.

See `docs/operations/service.md` for full setup, `docs/research/scoring.md` for eval numbers, and
`docs/architecture/hydradb-notes.md` for verified facts about HydraDB's query surface.

## How we used HydraDB

Slash is a thin analytical layer over HydraDB — every answer is produced by a live graph traversal
against a real HydraDB node, and nothing meaningful survives without it. The graph is a plain
versioned `PackageVersion → DEPENDS_ON → PackageVersion` DAG with temporal edge properties
(`published_at`, `valid_until` on versions; `resolved_at`, `at` on resolution edges) plus identity
and provenance edges (`MAINTAINED_BY`, `USES_LOCKFILE`, `RESOLVES_TO`).

- **Corpus** — `scripts/fetch_github.py` builds a real dependency graph from GitHub's public
  dataset: 9 real npm projects, real package versions (npm registry versions + lockfile pins),
  real maintainers, and real OSV vulnerability ranges — read from the live packages, not
  hand-authored. `data/github/ground_truth.json` records the advisory-derived truth so scoring
  is honest. After adding a committed project snapshot, regenerate it deterministically with
  `python scripts/refresh_ground_truth.py`. Ingest additionally restores the committed project
  snapshots (e.g. the demo repo) on server boot via `projects.sync_all()`.
- **Ingestion** — `scripts/ingest.py` pushes the 2,230-node / 5,714-edge dataset in batched,
  parameterized `UNWIND` + `MERGE` upserts keyed by node/edge id, so reruns are idempotent.
- **Blast radius** — HydraDB's bounded variable-length path traversal computes the transitive
  closure; the reverse (incoming) direction is walked level-by-level because the engine's
  variable-length support is outgoing-only from a fixed source id (verified empirically,
  `docs/architecture/hydradb-notes.md`).
- **Forensics & exposure** — lockfile resolution timestamps are compared in `WHERE` against the
  advisory window; service exposure is the intersection of the closure with `Service ← USES_LOCKFILE ← Lockfile → RESOLVES_TO` provenance.
- **Agent layer** — a deterministic Researcher classifies the question, an Auditor recomputes the
  live-flag and cross-checks for contradictions, and an Adjudicator renders a verdict or abstains.
- **No vector store can do this**: a reverse-dependency closure is a topological traversal, not a
  nearest-neighbour search — replacing HydraDB with embeddings would make every "blast radius"
  answer physically impossible rather than merely slower.

Traversal screenshots (console + evidence chain + subgraph):

![Exposed services verdict](docs/ux/screenshots/exposed.png)
![Blast radius](docs/ux/screenshots/blast.png)
![Abstention](docs/ux/screenshots/abstain.png)

## License

MIT — see `LICENSE`.