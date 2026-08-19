"""Product API unit tests: overview, static/SPA serving, graceful failures.

These must pass WITHOUT a live HydraDB, so the client points at an unreachable
port and we assert the server degrades cleanly instead of crashing.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from src.api import make_server
from src.hydradb_client import HydraDBClient

DEAD_CLIENT = HydraDBClient(base_url="http://127.0.0.1:59999")


@pytest.fixture(scope="module")
def server():
    srv = make_server(DEAD_CLIENT, port=0)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield srv
    srv.shutdown()


@pytest.fixture(scope="module")
def base(server):
    return f"http://127.0.0.1:{server.server_address[1]}"


def _get(base, path):
    with urllib.request.urlopen(base + path, timeout=10) as r:
        return r.status, dict(r.headers), r.read()


def _post(base, path, payload):
    req = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, json.loads(r.read())


def test_overview_reports_curated_corpus(base):
    status, _, body = _get(base, "/api/overview")
    assert status == 200
    data = json.loads(body)
    assert data["total_nodes"] > 0
    assert data["malicious_versions"] >= 4
    assert len(data["examples"]) >= 8
    assert all(e["question"] for e in data["examples"])


def test_health_degrades_when_db_down(base):
    status, _, body = _get(base, "/api/health")
    assert status == 200
    data = json.loads(body)
    assert data["ok"] is False


def test_ask_requires_question(base):
    with pytest.raises(urllib.error.HTTPError) as err:
        _get(base, "/api/ask")
    assert err.value.code == 404
    with pytest.raises(urllib.error.HTTPError) as err:
        _post(base, "/api/ask", {})
    assert err.value.code == 400


def test_ask_fails_cleanly_when_db_down(base):
    with pytest.raises(urllib.error.HTTPError) as err:
        _post(base, "/api/ask", {"question": "What is the blast radius of oslo?  "})
    assert err.value.code == 503
    body = json.loads(err.value.read())
    assert "error" in body


def test_static_serves_index_and_spa_fallback(base):
    from pathlib import Path

    dist = Path(__file__).resolve().parent.parent.parent / "assets" / "app" / "dist"
    if not dist.exists():
        return pytest.skip("frontend not built")
    status, headers, body = _get(base, "/")
    assert status == 200
    assert "text/html" in headers["Content-Type"]
    assert b"<div id=\"root\">" in body
    fallback_status, _, fallback_body = _get(base, "/supply-chain/blast")
    assert fallback_status == 200
    assert b"<div id=\"root\">" in fallback_body


def test_unknown_api_returns_json_404(base):
    with pytest.raises(urllib.error.HTTPError) as err:
        _get(base, "/api/nope")
    assert err.value.code == 404
    assert json.loads(err.value.read())["error"]