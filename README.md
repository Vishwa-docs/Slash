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
data/                Raw / processed / generated fixtures (.gitignored except tiny seeds)
tests/               pytest suites per risk tier
changes/             Change records (CHG-0001 …)
```

## Quick start

The full flow takes under two minutes from a clean clone against a machine with Docker and Python 3.11+.

```bash
# 1. Bring up HydraDB (Docker) — idempotent, waits for healthz
bash src/infra/hydradb-up.sh
#    (stop later with: bash src/infra/hydradb-up.sh stop)

# 2. Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Generate + ingest a reference ecosystem graph (deterministic, seed.toml)
python scripts/gen_dataset.py
python scripts/ingest.py          # idempotent — safe to re-run

# 4. Run the console
streamlit run app.py              # then open the printed URL
```

Try: `which services are exposed by oslo@adv-2026-01-1.0.0`, `what is the blast radius of
oslo@adv-2026-01-1.0.0`, `was oslo resolved while live`, `@dev_137 maintainers?`, or a nonsense
question to see first-class **abstention**.

See `docs/operations/service.md` for full setup, `docs/research/scoring.md` for eval numbers, and
`docs/architecture/hydradb-notes.md` for verified facts about HydraDB's query surface.

## How we used HydraDB

Slash is a thin analytical layer over HydraDB — every answer is produced by a live graph traversal
against a real HydraDB node, and nothing meaningful survives without it. The graph is a plain
versioned `PackageVersion → DEPENDS_ON → PackageVersion` DAG with temporal edge properties
(`published_at`, `valid_until` on versions; `resolved_at`, `at` on resolution edges) plus identity
and provenance edges (`MAINTAINED_BY`, `USES_LOCKFILE`, `RESOLVES_TO`).

- **Ingestion** — `scripts/ingest.py` pushes the 13,000+ node / 14,000+ edge dataset in batched,
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