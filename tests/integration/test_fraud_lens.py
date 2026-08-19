"""Lens abstraction integration tests: FRAUD graph_service vs planted ground truth.

The SAME five primitives query the fraud/AML graph — only the Lens swaps node
labels, relations, and the "compromised" property. Ground truth is planted in
data/fraud/ground_truth.json by scripts/gen_fraud_dataset.py (ADR-0010).
"""

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
from src.hydradb_client import HydraDBClient
from src.lens import FRAUD

ROOT = Path(__file__).resolve().parent.parent.parent
GT = json.loads((ROOT / "data" / "fraud" / "ground_truth.json").read_text())


@pytest.fixture(scope="module")
def client():
    c = HydraDBClient()
    if not c.healthz():
        pytest.skip("HydraDB not running")
    return c


@pytest.fixture(scope="module")
def advisories():
    return GT["advisories"]


def test_fraud_blast_radius_reaches_planted_consumers(client, advisories):
    for adv in advisories:
        res = run_blast_radius(client, adv["name"], adv["version"], lens=FRAUD)
        assert res["found"] is True
        assert int(res["node"]["id"]) == int(adv["malicious_node_id"])
        assert res["dependant_count"] >= 1, adv["advisory_id"]
        assert res["elapsed_ms"] < 5000
        assert res["node"]["malicious"] is True, adv["advisory_id"]


def test_fraud_exposed_merchants_equals_true_set(client, advisories):
    for adv in advisories:
        res = run_exposed_services(client, adv["name"], adv["version"], lens=FRAUD)
        assert set(res["services"]) == set(adv["exposed_merchants"]), adv["advisory_id"]
        assert res["elapsed_ms"] < 3000


def test_fraud_resolved_while_live_matches_apps(client, advisories):
    for adv in advisories:
        res = run_resolved_while_live(client, adv["name"], adv["version"], lens=FRAUD)
        got_apps = {r["app"] for r in res["lockfiles"]}
        expected_apps = {r["app"] for r in adv["resolved_while_live_lockfiles"]}
        assert got_apps == expected_apps, adv["advisory_id"]
        assert res["recompute_agrees"] is True, adv["advisory_id"]


def test_fraud_customer_contagion_matches(client):
    for entry in GT["contagion"]:
        res = run_maintainer_contagion(client, entry["developer_handle"], lens=FRAUD)
        assert set(entry["shared_packages"]) <= set(res["packages"]), entry[
            "advisory_id"
        ]
        assert res["found"] is True


def test_fraud_typosquat_recall(client):
    res = run_typosquat_candidates(client, top_k=15, lens=FRAUD)
    planted = {t["name"] for t in GT["typosquats"]}
    top = {c["name"] for c in res["candidates"]}
    recall = len(planted & top) / len(planted)
    assert recall >= 0.8, f"fraud typosquat recall {recall:.2f} < 0.8 in top-15"


def test_fraud_lookup_uses_compromised_property(client, advisories):
    import src.graph_service as gs

    for adv in advisories:
        node = gs.run_package_lookup(client, adv["name"], adv["version"], lens=FRAUD)
        assert node["found"] is True
        assert node["node"]["malicious"] is True, adv["advisory_id"]
        assert node["node"]["advisory_id"] == adv["advisory_id"]