# Containers & Runtime

> Source of truth: `docs/architecture/index.md`.

## Runtime pieces

```
┌─────────────────────────── Slash runtime ───────────────────────────┐
│                                                                          │
│  ┌─────────────────┐      ┌──────────────────────────────────────────┐  │
│  │ Streamlit app   │─────▶│ Python orchestration                    │  │
│  │ (app.py)        │      │  intent.py  → graph_service.py          │  │
│  │ UI per DESIGN.md│      │  adjudicate.py → hydradb_client.py      │  │
│  └─────────────────┘      └───────────────────┬──────────────────────┘  │
│                                               │ HTTP (8443) — primary    │
│                                               │ Bolt (7687) — fallback   │
└───────────────────────────────────────────────┼──────────────────────────┘
                                                v
                        ┌────────────────────────────────────────┐
                        │ HydraDB graph-node (official image)    │
                        │  ports: 8443 HTTP · 7687 Bolt · 9090   │
                        │  object store: LOCAL_PATH volume       │
                        └────────────────────────────────────────┘
```

| Container | Image / runtime | Purpose |
|---|---|---|
| `hydradb` | `ghcr.io/hydra-db/hydradb:latest` | Graph storage + query execution. Started by `src/infra/hydradb-up.sh` |
| Python backend | venv in this repo | Client, query builders, adjudication, dataset scripts |
| Streamlit | venv | The console UI (`streamlit run app.py`) |

## HydraDB container contract
- Run with the env block in `docs/architecture/hydradb-notes.md` (local object storage, plaintext
  allowed for localhost demo, own auth token file, ports 7687/8443/9090).
- Data persists to a named volume / local dir under `.hydradb/` (gitignored).
- The container is thrown away freely; `scripts/ingest.py` can repopulate it in minutes.

## Python module boundaries (component → file)
| Component | File | Responsibility |
|---|---|---|
| HydraDB client | `src/hydradb_client.py` | HTTP query API wrapper: `query()` returns typed rows + latency |
| Query builders | `src/graph_service.py` | Pure functions generating Cypher for the 5 core questions (+ subgraph fetch) |
| Intent / Researcher | `src/intent.py` | Classify NL question → query plan (deterministic keywords + optional LLM refine) |
| Auditor | `src/adjudicate.py` | Validate evidence (subgraph density, temporal consistency, contradiction) |
| Adjudicator | `src/adjudicate.py` | Verdict + evidence chain, or structured abstention |
| UI | `app.py` | Streamlit console per DESIGN.md |

## Deployment
Single node local demo is the target. `deploy/` holds a `docker-compose.yml` (HydraDB + app) once
the build lands — the demo can then run end-to-end (`docker compose up`). A deployed link is
optional for judging but strongly nice-to-have.