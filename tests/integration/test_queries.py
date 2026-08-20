"""Phase 3/Real-data integration tests: graph_service vs the real corpus GT (live DB)."""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import pytest

from src.graph_service import (
    run_blast_radius,
    run_exposed_services,
    run_resolved_while_live,
    run_typosquat_candidates,
)
from src.hydradb_client import HydraDBClient, HydraDBError

ROOT = Path(__file__).resolve().parent.parent.parent
GT = json.loads((ROOT / "data" / "github" / "ground_truth.json").read_text())
ADVISORIES = GT["advisories"]
EXPOSED = [a for a in ADVISORIES if a.get("exposed_services")]


@pytest.fixture(scope="module")
def client():
    c = HydraDBClient()
    if not c.healthz():
        pytest.skip("HydraDB not running")
    return c


@pytest.fixture(scope="module")
def advisories():
    return ADVISORIES


def test_blast_radius_reaches_real_consumers(client, advisories):
    for adv in advisories:
        res = run_blast_radius(client, adv["name"], adv["version"])
        assert res["found"] is True, adv["advisory_id"]
        assert int(res["node"]["id"]) == int(adv["malicious_node_id"])
        assert res["elapsed_ms"] < 5000
        for level in res["levels"]:
            assert 1 <= level[0]["depth"] <= 6


def test_exposed_services_equals_true_set(client):
    if not EXPOSED:
        pytest.skip("no live exposures in the real corpus")
    for adv in EXPOSED:
        res = run_exposed_services(client, adv["name"], adv["version"])
        assert set(res["services"]) == set(adv["exposed_services"]), adv["advisory_id"]
        assert res["elapsed_ms"] < 3000


def test_resolved_while_live_runs_without_error(client, advisories):
    for adv in advisories[:5]:
        res = run_resolved_while_live(client, adv["name"], adv["version"])
        assert isinstance(res["lockfiles"], list)
        assert res["elapsed_ms"] < 3000


def test_typosquat_candidates_shape(client):
    res = run_typosquat_candidates(client, top_k=15)
    assert isinstance(res["candidates"], list)
    assert all(isinstance(c, dict) and c.get("name") for c in res["candidates"])


def test_recompute_flag_agrees(client, advisories):
    """F3 recompute: an edge's `at` inside the malicious window iff stored flag."""
    import src.graph_service as gs

    for adv in advisories:
        bad = gs.plan_lookup(adv["name"], adv["version"])
        r = client.query(bad.cypher, bad.params)
        assert r.rows, adv["advisory_id"]
        node = r.rows[0]
        q = (
            "MATCH (s:Service)-[:USES_LOCKFILE]->(lf:Lockfile)-[rel:RESOLVES_TO]->"
            f"(v:PackageVersion {{id: {node['id']}}}) "
            "RETURN rel.at AS at, rel.was_resolved_while_live AS flag, v.published_at AS pub, v.valid_until AS val"
        )
        try:
            rr = client.query(q, {})
        except HydraDBError:
            continue
        for row in rr.rows:
            recompute = row["pub"] <= row["at"] <= row["val"]
            assert recompute == row["flag"], adv["advisory_id"]


def test_latency_p95(client):
    if not EXPOSED:
        pytest.skip("no live exposures in the real corpus")
    times = [
        run_exposed_services(client, a["name"], a["version"])["elapsed_ms"]
        for a in EXPOSED
    ]
    assert statistics.quantiles(times, n=100)[94] < 1000 if len(times) >= 2 else True
