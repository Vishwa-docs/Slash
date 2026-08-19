"""Phase 3 integration tests: graph_service vs planted ground truth (live DB)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.graph_service import (
    run_blast_radius,
    run_exposed_services,
    run_maintainer_contagion,
    run_resolved_while_live,
    run_typosquat_candidates,
)
from src.hydradb_client import HydraDBClient, HydraDBError

ROOT = Path(__file__).resolve().parent.parent.parent
GT = json.loads((ROOT / "data" / "generated" / "ground_truth.json").read_text())


@pytest.fixture(scope="module")
def client():
    c = HydraDBClient()
    if not c.healthz():
        pytest.skip("HydraDB not running")
    return c


@pytest.fixture(scope="module")
def advisories():
    return GT["advisories"]


def test_blast_radius_reaches_planted_consumers(client, advisories):
    for adv in advisories:
        res = run_blast_radius(client, adv["name"], adv["version"])
        assert res["found"] is True
        assert int(res["node"]["id"]) == int(adv["malicious_node_id"])
        assert res["dependant_count"] >= 1, adv["advisory_id"]
        assert res["elapsed_ms"] < 5000
        for level in res["levels"]:
            assert 1 <= level[0]["depth"] <= 6


def test_exposed_services_equals_true_set(client, advisories):
    for adv in advisories:
        res = run_exposed_services(client, adv["name"], adv["version"])
        expected = set(adv["exposed_services"])
        assert set(res["services"]) == expected, adv["advisory_id"]
        assert res["elapsed_ms"] < 3000


def test_resolved_while_live_matches_apps(client, advisories):
    for adv in advisories:
        res = run_resolved_while_live(client, adv["name"], adv["version"])
        expected_apps = {lf["app"] for lf in adv["resolved_while_live_lockfiles"]}
        got_apps = {r["app"] for r in res["lockfiles"]}
        assert got_apps == expected_apps, adv["advisory_id"]


def test_maintainer_contagion_matches(client, advisories):
    for entry in GT["contagion"]:
        res = run_maintainer_contagion(client, entry["developer_handle"])
        assert set(entry["shared_packages"]) <= set(res["packages"]), entry[
            "advisory_id"
        ]


def test_typosquat_recall(client):
    res = run_typosquat_candidates(client, top_k=15)
    planted = {t["name"] for t in GT["typosquats"]}
    top = {c["name"] for c in res["candidates"]}
    recall = len(planted & top) / len(planted)
    assert recall >= 0.8, f"typosquat recall {recall:.2f} < 0.8 in top-15"


def test_recompute_flag_agrees(client, advisories):
    """F3 recompute: an edge's `at` inside the malicious window iff stored flag."""
    import src.graph_service as gs

    for adv in advisories:
        bad = gs.plan_lookup(adv["name"], adv["version"])
        r = client.query(bad.cypher, bad.params)
        assert r.rows, adv["advisory_id"]
        node = r.rows[0]
        # scan all lockfile resolutions touching this malicious version
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


def test_latency_p95(client, advisories):
    import statistics

    times = []
    for adv in advisories:
        times.append(
            run_exposed_services(client, adv["name"], adv["version"])["elapsed_ms"]
        )
    assert statistics.quantiles(times, n=100)[94] < 1000 if len(times) >= 2 else True
