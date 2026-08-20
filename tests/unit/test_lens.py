"""Lens abstraction sanity (unit): one engine, parameterized vocabulary.

The data layer ships one real lens today (the GitHub dependency graph). The lens
registry must stay self-consistent so new verticals can be added without query
engine changes (ADR-0010).
"""

from __future__ import annotations

import pytest

from src.lens import LENSES, SUPPLY_CHAIN, lens_by_id

REQUIRED_FIELDS = {
    "id",
    "title",
    "entity_node",
    "version_node",
    "resource_node",
    "consumption_node",
    "developer_node",
    "depend_rel",
    "uses_rel",
    "resolves_rel",
    "maintains_rel",
    "malicious_field",
    "exposed_noun",
    "live_noun",
    "contagion_noun",
    "lookalike_noun",
}


def test_lens_registry_is_nonempty_and_keyed_by_id():
    assert LENSES
    assert all(k == v.id for k, v in LENSES.items())


@pytest.mark.parametrize("lens", list(LENSES.values()))
def test_lens_defines_full_vocabulary(lens):
    for field in REQUIRED_FIELDS:
        assert getattr(lens, field), f"{lens.id} missing {field}"


def test_dependency_graph_lens_is_the_default():
    assert lens_by_id(None) is SUPPLY_CHAIN
    assert lens_by_id("dependency-graph") is SUPPLY_CHAIN
    assert lens_by_id("does-not-exist") is SUPPLY_CHAIN
    assert SUPPLY_CHAIN.id == "dependency-graph"
    assert SUPPLY_CHAIN.entity_node == "Package"
    assert SUPPLY_CHAIN.version_node == "PackageVersion"
    assert SUPPLY_CHAIN.exposed_noun == "services"
