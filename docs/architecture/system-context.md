# System Context

> Source of truth: `docs/architecture/index.md`.

```
                            ┌────────────────────────────┐
                            │   Security analyst / demo   │
                            │   (human in the loop)      │
                            └─────────────┬──────────────┘
                                          │ natural-language question, click-through review
                                          v
                          ┌───────────────┴────────────────┐
                          │      Slash (this repo)     │
                          │  Streamlit console              │
                          │  + orchestration ("agents")     │
                          └───────────────┬────────────────┘
                                          │ OpenCypher over HTTPS/Bolt
                                          v
                          ┌───────────────┴────────────────┐
                          │  HydraDB graph node (Docker)    │
                          │  -> object storage (local path) │
                          └───────────────────────────────┘
                                          ^
                          ┌───────────────┴────────────────┐
                          │  Ecosystem data               │
                          │  (dataset generator / SBOM /   │
                          │   OSV-style advisories)        │
                          └───────────────────────────────┘
```

## External actors

| Actor | Interaction |
|---|---|
| **Analyst/user** | Asks NL questions; reads verdict + evidence chain; approves/drills into subgraph; sees query latency & cost |
| **HydraDB (sibling repo, unchanged)** | Stores the graph; executes Cypher. We ship install scripts that pull the official Docker image |
| **Ecosystem data** | Deterministic synthetic npm-style ecosystem + planted advisories/typosquats with a ground-truth manifest (optionally: real SBOM via `cdxgen`, OSV advisories) |
| **LLM (optional)** | Optional augmentation of the adjudicator with structured output (JSON mode / Pydantic). **Never required for the core demo** |

## External services we explicitly do NOT use
- No hosted vector DB, no external RAG service, no cloud graphDB. Everything lives in HydraDB locally.
- No secrets: the auth token is a local file; no production credentials anywhere.

## Key quality attributes
- **Latency**: p95 < 1s for blast-radius queries (measured in `scripts/eval.py`).
- **Reliability**: abstain when evidence is thin; never present an invented dependency edge.
- **Cost**: query budget cap per question; token cost visible in the console.
- **Portability**: one `docker run` + `pip install` to demo; dataset generator is reproducible.