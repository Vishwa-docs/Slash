"""Unit tests for the deterministic Researcher (intent classifier)."""

from __future__ import annotations

import pytest

from src.intent import classify
from src.models import IntentClass

CASES = [
    (
        "which services are exposed by oslo",
        IntentClass.EXPOSED_SERVICES,
        {"package": "oslo"},
    ),
    (
        "what services can reach oslo@adv-2026-01-1.0.0",
        IntentClass.EXPOSED_SERVICES,
        {"package": "oslo", "version": "adv-2026-01-1.0.0"},
    ),
    ("what is the blast radius of oslo", IntentClass.BLAST_RADIUS, {"package": "oslo"}),
    (
        "who transitively depends on oslo 1.2.3",
        IntentClass.BLAST_RADIUS,
        {"package": "oslo", "version": "1.2.3"},
    ),
    (
        "was oslo resolved while live",
        IntentClass.RESOLVED_WHILE_LIVE,
        {"package": "oslo"},
    ),
    (
        "which lockfiles resolved oslo in its window",
        IntentClass.RESOLVED_WHILE_LIVE,
        {"package": "oslo"},
    ),
    (
        "what packages does dev_137 maintain",
        IntentClass.MAINTAINER_CONTAGION,
        {"developer": "dev_137"},
    ),
    (
        "which packages share a maintainer with oslo",
        IntentClass.MAINTAINER_CONTAGION,
        {"package": "oslo"},
    ),
    (
        "show typosquat candidates near oslo",
        IntentClass.TYPOSQUAT_CANDIDATES,
        {"package": "oslo"},
    ),
    (
        "are there lookalike names for sync",
        IntentClass.TYPOSQUAT_CANDIDATES,
        {"package": "sync"},
    ),
    (
        "tell me about left-pad 1.0.0",
        IntentClass.PACKAGE_LOOKUP,
        {"package": "left-pad", "version": "1.0.0"},
    ),
    ("what is oslo", IntentClass.PACKAGE_LOOKUP, {"package": "oslo"}),
    ("what is the weather today", IntentClass.UNSUPPORTED, {}),
    ("who won the world cup in 1998", IntentClass.UNSUPPORTED, {}),
    ("tell me a joke", IntentClass.UNSUPPORTED, {}),
    ("translate hello to spanish", IntentClass.UNSUPPORTED, {}),
    ("what is 2 + 2", IntentClass.UNSUPPORTED, {}),
    # fraud lens vocabulary routes onto the same five primitives
    (
        "which merchants are exposed by makeshop@adv-2026-01-1.0.0",
        IntentClass.EXPOSED_SERVICES,
        {"package": "makeshop", "version": "adv-2026-01-1.0.0"},
    ),
    (
        "which intake events involved bexpay while it was compromised",
        IntentClass.RESOLVED_WHILE_LIVE,
        {"package": "bexpay"},
    ),
    (
        "which accounts moved funds during the compromise window",
        IntentClass.RESOLVED_WHILE_LIVE,
        {},
    ),
    (
        "who owns the accounts owned by cust_009",
        IntentClass.MAINTAINER_CONTAGION,
        {"developer": "cust_009"},
    ),
    (
        "any lookalike accounts near makeshop",
        IntentClass.TYPOSQUAT_CANDIDATES,
        {"package": "makeshop"},
    ),
    (
        "which merchants impacted when acct compromised",
        IntentClass.EXPOSED_SERVICES,
        {"package": "acct"},
    ),
]


@pytest.mark.parametrize("question,intent,expected", CASES)
def test_classify(question, intent, expected):
    plan = classify(question)
    assert plan.intent == intent, question
    for key, value in expected.items():
        assert getattr(plan, key) == value, f"{key} for {question}"
