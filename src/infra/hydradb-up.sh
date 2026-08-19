#!/usr/bin/env bash
# Slash: bring up a local HydraDB dev node in Docker. Idempotent.
# Teardown: `docker stop slash-hydra` (or `bash src/infra/hydradb-up.sh stop`).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
NAME=slash-hydra
IMG=ghcr.io/hydra-db/hydradb:latest
TOKEN_FILE="$ROOT/.hydradb/auth.token"
HEALTHZ_URL=http://127.0.0.1:8443/healthz

if [[ "${1:-}" == "stop" ]]; then
  docker stop "$NAME" >/dev/null 2>&1 || true
  echo "[slash] stopped $NAME"
  exit 0
fi

mkdir -p "$ROOT/.hydradb/store" "$ROOT/.hydradb/cache"

# One random demo token (localhost only, not a secret).
if [[ ! -f "$TOKEN_FILE" ]]; then
  openssl rand -hex 16 >"$TOKEN_FILE"
fi

# Idempotent: already healthy means nothing to do — but still make sure the local
# auth token matches the running node (a clone that finds a live container from a
# different checkout must not break with 401s).
if curl -fsS "$HEALTHZ_URL" >/dev/null 2>&1; then
  if docker inspect "$NAME" >/dev/null 2>&1; then
    docker exec "$NAME" cat /var/hydradb/auth.token >"$TOKEN_FILE" 2>/dev/null || true
  fi
  echo "[slash] hydradb already up (healthz OK)"
  exit 0
fi

docker rm -f "$NAME" >/dev/null 2>&1 || true
docker pull "$IMG" >/dev/null
docker run --rm -d --name "$NAME" \
  --user "$(id -u):$(id -g)" \
  -v "$ROOT/.hydradb:/var/hydradb" \
  -e CLOUD_PROVIDER=local \
  -e LOCAL_PATH=/var/hydradb/store \
  -e GRAPH_NAMESPACE=default \
  -e GRAPH_ID=default \
  -e GRAPH_CELL_ID=cell-0 \
  -e GRAPH_CELLS=cell-0 \
  -e GRAPH_NODE_ID=node-0 \
  -e GRAPH_BOLT_NODE_ADDRESSES=node-0=127.0.0.1:7687 \
  -e GRAPH_ADVERTISED_BOLT_ADDR=127.0.0.1:7687 \
  -e GRAPH_DATA_CACHE_DIR=/var/hydradb/cache \
  -e GRAPH_AUTH_TOKEN_FILE=/var/hydradb/auth.token \
  -e GRAPH_ALLOW_PLAINTEXT=true \
  -e RUST_MIN_STACK=33554432 \
  -p 7687:7687 -p 8443:8443 -p 9090:9090 \
  "$IMG" >/dev/null

for _ in $(seq 1 60); do
  if curl -fsS "$HEALTHZ_URL" >/dev/null 2>&1; then
    echo "[slash] hydradb up (container $NAME, healthz OK)"
    exit 0
  fi
  if [[ "$(docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null)" != "true" ]]; then
    echo "[slash] FAIL: container exited" >&2
    docker logs "$NAME" >&2 || true
    exit 1
  fi
  sleep 1
done

echo "[slash] FAIL: healthz not OK after 60s" >&2
docker logs "$NAME" >&2 || true
exit 1
