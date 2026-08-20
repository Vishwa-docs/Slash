# Operations & Service Notes

> Source of truth: `docs/architecture/containers.md`, `docs/architecture/hydradb-notes.md`.

## Topology (local demo)
- One HydraDB container (`slash-hydra`) + one Python process serving the React console + product
  API on `8501` (`scripts/serve.py`).
- Deployed link (optional, strongly nice): single host via `deploy/docker-compose.yml`.

## Start / stop
```bash
# HydraDB
bash src/infra/hydradb-up.sh          # pull + run with the documented env contract
docker stop slash-hydra

# App (React SPA + product API in one process)
python scripts/serve.py --port 8501    # open http://127.0.0.1:8501

# Reset the graph deterministically (removes stale nodes/edges from earlier runs),
# then re-ingest the committed corpus (+ project snapshots on next serve.py boot):
bash src/infra/hydradb-up.sh stop && rm -rf .hydradb/store/* .hydradb/cache/*
bash src/infra/hydradb-up.sh && python scripts/ingest.py

# All-in-one (once composed)
docker compose -f deploy/docker-compose.yml up
```

## Health checks
- `curl localhost:9090/healthz` or `GET /healthz` (public) — HydraDB alive.
- `scripts/smoke.sh` — health + round trip + a T1 no-injection fuzz check; save output to
  `.evidence/runs/<phase>/smoke.txt`.

## Recovery / troubleshooting
| Symptom | Action |
|---|---|
| HydraDB container won't start | Check `GRAPH_AUTH_TOKEN_FILE` exists with one-line token; `GRAPH_ALLOW_PLAINTEXT=true`; ports free (7687/8443/9090) |
| Query fails with "unsupported" | Consult `docs/architecture/hydradb-notes.md` subset; adjust the query; never fake a result |
| Slow queries | Reduce hop ceiling (`*1..6` → `*1..4`), batch ingest, check `/metrics` |
| App crashes on a row | That's a bug in `src/hydradb_client.py` parsing — fix client, not the data |
| Everything broken after a demo edit | `just`-style: run smoke.sh first; HydraDB is stateless — repopulate with `scripts/ingest.py` |

## Observability
- HydraDB Prometheus metrics on 9090 (`/metrics`).
- Client captures `elapsed_ms` per query; the console shows latency + cost badges.
- `.evidence/runs/` accumulates command outputs for every phase.

## Cost posture
- No cloud spend by default (local object storage).
- Optional LLM: capped, keyed, and OFF by default.
- The evaluation table (latency/cost) is part of the submission narrative.