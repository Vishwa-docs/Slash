"""Unit tests for the deterministic Researcher (intent classifier).

Uses real package names from the corpus; entity extraction is name-agnostic.
"""

from __future__ import annotations

import pytest

from src.intent import classify
from src.models import IntentClass

CASES = [
    (
        "which services are exposed by express",
        IntentClass.EXPOSED_SERVICES,
        {"package": "express"},
    ),
    (
        "what services can reach lodash@4.17.21",
        IntentClass.EXPOSED_SERVICES,
        {"package": "lodash", "version": "4.17.21"},
    ),
    (
        "what depends on express",
        IntentClass.BLAST_RADIUS,
        {"package": "express"},
    ),
    (
        "who transitively depends on axios 1.2.3",
        IntentClass.BLAST_RADIUS,
        {"package": "axios", "version": "1.2.3"},
    ),
    (
        "was lodash resolved while live",
        IntentClass.RESOLVED_WHILE_LIVE,
        {"package": "lodash"},
    ),
    (
        "which lockfiles resolved ws in its window",
        IntentClass.RESOLVED_WHILE_LIVE,
        {"package": "ws"},
    ),
    (
        "what packages does dev_137 maintain",
        IntentClass.MAINTAINER_CONTAGION,
        {"developer": "dev_137"},
    ),
    (
        "which packages share a maintainer with marked",
        IntentClass.MAINTAINER_CONTAGION,
        {"package": "marked"},
    ),
    (
        "show typosquat candidates near axios",
        IntentClass.TYPOSQUAT_CANDIDATES,
        {"package": "axios"},
    ),
    (
        "are there lookalike names for fastify",
        IntentClass.TYPOSQUAT_CANDIDATES,
        {"package": "fastify"},
    ),
    (
        "tell me about minimist 0.2.4",
        IntentClass.PACKAGE_LOOKUP,
        {"package": "minimist", "version": "0.2.4"},
    ),
    ("what is express", IntentClass.PACKAGE_LOOKUP, {"package": "express"}),
    # Scoped npm packages (@scope/name@version)
    (
        "which services are exposed by @pkgr/core@0.3.6",
        IntentClass.EXPOSED_SERVICES,
        {"package": "@pkgr/core", "version": "0.3.6"},
    ),
    (
        "what is the blast radius of @babel/core@7.29.0",
        IntentClass.BLAST_RADIUS,
        {"package": "@babel/core", "version": "7.29.0"},
    ),
    (
        "which services are exposed by @cacheable/memory@2.0.9",
        IntentClass.EXPOSED_SERVICES,
        {"package": "@cacheable/memory", "version": "2.0.9"},
    ),
    ("what is the weather today", IntentClass.UNSUPPORTED, {}),
    ("who won the world cup in 1998", IntentClass.UNSUPPORTED, {}),
    ("tell me a joke", IntentClass.UNSUPPORTED, {}),
    ("translate hello to spanish", IntentClass.UNSUPPORTED, {}),
    ("what is 2 + 2", IntentClass.UNSUPPORTED, {}),
]


@pytest.mark.parametrize("question,intent,expected", CASES)
def test_classify(question, intent, expected):
    plan = classify(question)
    assert plan.intent == intent, question
    for key, value in expected.items():
        assert getattr(plan, key) == value, f"{key} for {question}"
