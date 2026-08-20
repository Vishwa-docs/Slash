"""Phase 5 UI smoke: app module imports, design tokens, and deterministic AppTest renders."""

from __future__ import annotations


def test_app_module_imports():
    import app

    assert callable(app.run)
    assert app.DEMO_QUESTIONS


def test_style_assets_present():
    from pathlib import Path

    css = (
        Path(__file__).resolve().parent.parent.parent / "assets" / "style.css"
    ).read_text()
    assert "Berkeley Mono" in css
    assert "#ff3b30" in css
    assert "#fdfcfc" in css


def _history(at) -> list:
    try:
        return at.session_state["history"]
    except (KeyError, AttributeError):
        return []


def _new_app(question: str | None = None):
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(
        str(Path(__file__).resolve().parent.parent.parent / "app.py"),
        default_timeout=60,
    )
    if question:
        at.query_params["q"] = question
    at.run()
    return at


def test_app_answers_demo_questions_via_session():
    """Drive the real app headlessly (Streamlit AppTest) and assert the rendered verdicts."""

    # landing, no question
    assert _history(_new_app()) == []

    # exposed services
    at = _new_app("which services are exposed by debug@4.4.3")
    hist = _history(at)
    assert hist, "no history after seeded question"
    v = hist[-1]["verdict"]
    assert not v.abstain
    assert (
        v.answer
        == "TEAMMATES/teammates, Vishwa-docs/reefguard-coral-hackathon, axios/axios, "
        "expressjs/express, fastify/fastify, jaredhanson/passport, markedjs/marked, "
        "sindresorhus/conf, typicode/lowdb, websockets/ws"
    )
    assert len(v.evidence_chain) >= 4

    # abstention for nonsense
    at2 = _new_app("what is the meaning of life")
    v2 = _history(at2)[-1]["verdict"]
    assert v2.abstain
    assert "Not enough evidence" in v2.reason


def test_app_subgraph_payload_json():
    """The stored result round-trips to plain JSON (evidence chain rows render from it)."""
    import json

    from src.models import Evidence

    ev = Evidence(
        purpose="p",
        cypher="dummy",
        row_count=0,
        elapsed_ms=0.0,
        params={"id": 1},
    )
    as_json = json.loads(ev.model_dump_json())
    assert as_json["purpose"] == "p"
    assert as_json["params"] == {"id": 1}
