"""Abstention unit tests: Auditor + Adjudicator, no DB required."""

from __future__ import annotations

import pytest

from src.adjudicate import Adjudicator, Auditor
from src.intent import classify
from src.models import IntentClass

UNSUPPORTED_QUESTIONS = [
    "what is the weather today",
    "capital of france",
    "tell me a joke",
    "who are you",
    "recommend a good restaurant",
]


@pytest.mark.parametrize("question", UNSUPPORTED_QUESTIONS)
def test_out_of_vocabulary_abstains(question):
    plan = classify(question)
    assert plan.intent == IntentClass.UNSUPPORTED
    verdict = Adjudicator().verdict(Auditor().evaluate(plan, {}))
    assert verdict.abstain is True
    assert "can answer" in verdict.reason


def test_empty_evidence_abstains():
    plan = classify("what depends on express")
    audit = Auditor().evaluate(plan, {"found": False, "steps": [], "elapsed_ms": 1.0})
    verdict = Adjudicator().verdict(audit)
    assert verdict.abstain is True
    assert "Not enough evidence" in verdict.reason


def test_valid_exposed_answer_not_abstained():
    plan = classify("which services are exposed by express")
    result = {
        "found": True,
        "services": ["gateway", "notifications"],
        "path_rows": [],
        "steps": [(_step("svc"), _res(2))],
        "elapsed_ms": 12.0,
        "query_count": 3,
    }
    verdict = Adjudicator().verdict(Auditor().evaluate(plan, result))
    assert verdict.abstain is False
    assert verdict.answer == "gateway, notifications"
    assert len(verdict.evidence_chain) == 1
    assert verdict.latency_ms == 12.0


def test_contradiction_surfaces_both_facts():
    plan = classify("was lodash resolved while live")
    result = {
        "found": True,
        "lockfiles": [{"app": "expressjs/express"}],
        "contradictions": [
            {
                "name": "lodash",
                "version": "4.17.21",
                "at": 100,
                "stored_flag": False,
                "recomputed_flag": True,
            }
        ],
        "steps": [],
        "elapsed_ms": 5.0,
        "query_count": 1,
    }
    audit = Auditor().evaluate(plan, result)
    assert len(audit.contradictions) == 1
    verdict = Adjudicator().verdict(audit)
    assert verdict.abstain is False
    assert "stored=False" in verdict.answer
    assert "recomputed=True" in verdict.answer


def _step(purpose):
    from src.graph_service import QueryStep

    return QueryStep("MATCH (n) RETURN n", {}, purpose)


def _res(rows):
    from src.hydradb_client import QueryResult

    return QueryResult(rows=[{}] * rows, elapsed_ms=4.0, columns=[])
