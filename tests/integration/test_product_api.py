"""Product API integration tests: full ask/subgraph round-trip against live HydraDB."""

from __future__ import annotations

import json
import threading
import urllib.request

import pytest

from src.api import make_server
from src.hydradb_client import HydraDBClient


@pytest.fixture(scope="module")
def base():
    client = HydraDBClient()
    if not client.healthz():
        pytest.skip("HydraDB not running")
    srv = make_server(client, port=0)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def _ask(base, question: str) -> dict:
    req = urllib.request.Request(
        base + "/api/ask",
        data=json.dumps({"question": question}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def test_ask_exposed_services_shapes(base):
    d = _ask(base, "Which services are exposed by oslo@adv-2026-01-1.0.0?")
    assert d["abstain"] is False
    assert d["intent"] == "EXPOSED_SERVICES"
    assert d["payload"]["services"] == ["gateway", "notifications"]
    assert d["payload"]["node_id"]
    assert d["payload"]["name"] == "oslo"
    assert d["query_count"] >= 1
    assert d["evidence_chain"], "must ship its evidence chain"


def test_ask_abstains_honestly(base):
    d = _ask(base, "Tell me about the weather in jakarta")
    assert d["abstain"] is True
    assert d["answer"] == ""
    assert d["reason"]


def test_subgraph_returns_graph(base):
    req = urllib.request.Request(
        base + "/api/subgraph",
        data=json.dumps({"name": "oslo", "version": "adv-2026-01-1.0.0"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    assert d["node_id"] == 17526
    assert isinstance(d["nodes"], list)
    assert isinstance(d["edges"], list)
    assert d["nodes"], "graph must know its immediate neighborhood"


def test_subgraph_unknown_node_404(base):
    req = urllib.request.Request(
        base + "/api/subgraph",
        data=json.dumps({"name": "does-not-exist-zzz", "version": "1.0.0"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as err:
        urllib.request.urlopen(req, timeout=30)
    assert err.value.code == 404