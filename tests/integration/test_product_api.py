"""Product API integration tests: full ask/subgraph round-trip vs live HydraDB.

Assertions are derived from the committed real-GitHub ground truth so the tests
and the graph always agree.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from src.api import make_server
from src.hydradb_client import HydraDBClient

ROOT = Path(__file__).resolve().parent.parent.parent
GT = json.loads((ROOT / "data" / "github" / "ground_truth.json").read_text())
EXPOSED = [a for a in GT["advisories"] if a.get("exposed_services")]


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
    if not EXPOSED:
        return pytest.skip("no live exposures in the real corpus")
    adv = EXPOSED[0]
    d = _ask(base, f"Which services are exposed by {adv['name']}@{adv['version']}?")
    assert d["abstain"] is False
    assert d["intent"] == "EXPOSED_SERVICES"
    assert set(d["payload"]["services"]) == set(adv["exposed_services"])
    assert d["payload"]["node_id"]
    assert d["payload"]["name"] == adv["name"]
    assert d["query_count"] >= 1
    assert d["evidence_chain"], "must ship its evidence chain"


def test_ask_abstains_then_reports(base):
    d = _ask(base, "Tell me about the weather in jakarta")
    assert d["abstain"] is True
    assert d["answer"] == ""
    assert d["reason"]
    assert d["reported"] is True


def test_subgraph_returns_graph(base):
    if not EXPOSED:
        return pytest.skip("no live exposures in the real corpus")
    adv = EXPOSED[0]
    req = urllib.request.Request(
        base + "/api/subgraph",
        data=json.dumps({"name": adv["name"], "version": adv["version"]}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    assert int(d["node_id"]) == int(adv["malicious_node_id"])
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
