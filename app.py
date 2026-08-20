"""Slash console — Streamlit UI (DESIGN.md: mono, cream canvas, hairline, one dark panel).

`streamlit run app.py`; works without any key, LLM-assisted when a
GROQ_API_KEY / per-request key is supplied. Guarded under __main__ so
tests/unit/test_ui_smoke.py can import this module without launching.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Slash — dependency intelligence on HydraDB", layout="wide"
)

CSS = (Path(__file__).parent / "assets" / "style.css").read_text()
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

from src.examples import demo_examples
from src.lens import LENSES, lens_by_id

# Keep the demo chips anchored to the checked-in real corpus.
DEMO_QUESTIONS = [e["question"] for e in demo_examples()[:3]] or [
    "Which services are exposed by debug@4.4.3?",
    "Is there a typosquat near axios?",
    "What is the blast radius of debug@4.4.3?",
]
VERDICT_COLORS = {"danger", "warning", "success", "neutral"}


def _client():
    from src.hydradb_client import HydraDBClient

    return HydraDBClient()


def _pill(verdict) -> tuple[str, str]:
    if verdict.abstain:
        return "NOT FOUND", "warning"
    if verdict.intent.value == "TYPOSQUAT_CANDIDATES":
        return "TYPOSQUAT RISK", "warning"
    if verdict.intent.value == "EXPOSED_SERVICES":
        return (
            "EXPOSED" if "No services" not in verdict.answer else "CLEAN",
            "danger" if "No services" not in verdict.answer else "success",
        )
    if verdict.intent.value == "RESOLVED_WHILE_LIVE":
        return "FORENSICS", "neutral"
    return "VERDICT", "neutral"


def _render_verdict(question: str, verdict, result: dict | None) -> None:
    label, color = _pill(verdict)
    st.markdown(
        f'<span class="verdict-pill pill-{color}">{label}</span> '
        f'<span class="bullet">[?]</span> {question}',
        unsafe_allow_html=True,
    )
    if verdict.abstain:
        st.markdown(f"**{verdict.reason}**")
    else:
        st.markdown(f"**{verdict.answer}**")
        if verdict.reason:
            st.markdown(
                f"<span class='bullet'>[!]</span> {verdict.reason}",
                unsafe_allow_html=True,
            )
    if verdict.summary:
        st.markdown(
            f"<div class='console-panel' style='margin-top:6px'><span class='q'>› llm summary</span>{verdict.summary}</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        f"<span class='section-label'>[{verdict.query_count} queries · {verdict.latency_ms:.0f} ms]</span>",
        unsafe_allow_html=True,
    )


def _render_evidence(verdict, result: dict | None) -> None:
    if not result:
        return
    for ev in verdict.evidence_chain:
        with st.expander(
            f"{ev.purpose} — {ev.row_count} rows · {ev.elapsed_ms:.0f} ms"
        ):
            st.markdown(
                f'<div class="console-panel"><pre>{ev.cypher}</pre></div>',
                unsafe_allow_html=True,
            )
            if ev.params:
                st.markdown(
                    f"<span class='bullet'>params:</span> `{ev.params}`",
                    unsafe_allow_html=True,
                )
            _rows_table(result, ev.purpose)


def _rows_table(result: dict | None, purpose: str) -> None:
    """Render up to 8 rows of the step that produced this evidence."""
    if not result:
        return
    for step, res in result.get("steps", []):
        if step.purpose != purpose:
            continue
        if not res.result.rows:
            st.markdown(
                "<span class='bullet'>[ ] 0 rows</span>", unsafe_allow_html=True
            )
            return
        rows = [_stringify(r) for r in res.result.rows[:8]]
        cols = rows[0].keys()
        header = "| " + " | ".join(cols) + " |"
        sep = "|" + "|".join("---" for _ in cols) + "|"
        body = ["| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows]
        st.markdown("\n".join([header, sep, *body]))
        if len(res.result.rows) > 8:
            st.markdown(
                f"<span class='bullet'>[+] …{len(res.result.rows) - 8} more rows</span>",
                unsafe_allow_html=True,
            )
        return


def _stringify(row: dict) -> dict:
    out: dict = {}
    for k, v in row.items():
        if isinstance(v, dict):
            v = v.get("value", "")
        out[k] = str(v)[:60]
    return out


def _render_subgraph(result: dict | None, lens=None) -> None:
    if not result:
        return
    node_id = None
    if result.get("node"):
        node_id = result["node"]["id"]
    elif "blast_radius" in result and result["blast_radius"].get("node"):
        node_id = result["blast_radius"]["node"]["id"]
    if node_id is None:
        st.markdown(
            "<span class='bullet'>[x] no subgraph for this intent</span>",
            unsafe_allow_html=True,
        )
        return
    from src.graph_service import run_fetch_subgraph

    sg = run_fetch_subgraph(
        _client(), node_id, depth=2, lens=lens or lens_by_id("dependency-graph")
    )
    if not sg["nodes"]:
        st.markdown(
            "<span class='bullet'>[x] no neighbouring nodes for the seed</span>",
            unsafe_allow_html=True,
        )
        return
    _plot(sg, node_id)


def _plot(sg: dict, seed_id: int) -> None:
    import networkx as nx
    import plotly.graph_objects as go

    g = nx.DiGraph()
    g.add_node(seed_id, label="seed")
    for n in sg["nodes"]:
        g.add_node(n["id"], label=n.get("name", str(n["id"])))
    for e in sg["edges"]:
        g.add_edge(e["src"], e["dst"])
    pos = nx.spring_layout(g, seed=7, k=0.7, iterations=60)
    names = {n["id"]: n.get("name", str(n["id"])) for n in sg["nodes"]}
    names[seed_id] = f"seed #{seed_id}"

    edge_trace = go.Scatter(
        x=[],
        y=[],
        mode="lines",
        line={"width": 1, "color": "#9a9898"},
        hoverinfo="none",
    )
    for u, v in g.edges():
        edge_trace["x"] += (pos[u][0], pos[v][0], None)
        edge_trace["y"] += (pos[u][1], pos[v][1], None)

    node_x, node_y, node_t, node_c = [], [], [], []
    for nid, (x, y) in pos.items():
        node_x.append(x)
        node_y.append(y)
        node_t.append(names.get(nid, str(nid)))
        node_c.append(_node_color(sg, nid, seed_id))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_t,
        textposition="bottom center",
        marker={"size": 10, "color": node_c, "line": {"width": 0}},
        textfont={"size": 9, "color": "#201d1d"},
    )
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False,
        paper_bgcolor="#fdfcfc",
        plot_bgcolor="#fdfcfc",
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        xaxis={"visible": False},
        yaxis={"visible": False},
        font={"family": "Berkeley Mono", "size": 10},
    )
    st.plotly_chart(fig, width="stretch")


def _node_color(sg: dict, nid: int, seed_id: int) -> str:
    if nid == seed_id:
        return "#ff3b30"
    for n in sg["nodes"]:
        if n["id"] != nid:
            continue
        return "#30d158"
    return "#30d158"


def _stream_console(verdict, result: dict | None) -> None:
    st.markdown(
        '<div class="section-block"><div class="section-label">live query console</div>'
        '<div class="console-panel">'
        '<span class="m">$ slash --ask</span>',
        unsafe_allow_html=True,
    )
    if result:
        for step, _ in result.get("steps", []):
            st.markdown(
                f'<div class="console-panel" style="margin-top:2px"><span class="q">› {step.purpose}</span><pre>{step.cypher}</pre></div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div class="console-panel" style="margin-top:2px"><span class="m">'
            "no query issued — the answer was reported as not-found after the graph "
            "could not be healed</span></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def _thought_process(verdict) -> None:
    with st.expander(
        "thought process — Researcher → Auditor → Adjudicator", expanded=True
    ):
        st.markdown(
            f"<span class='bullet'>[r]</span> <b>Researcher</b> (base resolver "
            f"+ optional LLM refinement): intent <code>{verdict.intent.value}</code><br>"
            f"<span class='bullet'>[a]</span> <b>Auditor</b>: density, temporal recompute, contradictions<br>"
            f"<span class='bullet'>[h]</span> <b>Healer</b>: attempts to construct/fix the "
            f"missing graph data before answering<br>"
            f"<span class='bullet'>[j]</span> <b>Adjudicator</b>: "
            f"{'NOT FOUND (reported)' if verdict.abstain else 'VERDICT'} — {verdict.reason or 'evidence sufficient'}",
            unsafe_allow_html=True,
        )


def run() -> None:
    lens_label = st.selectbox(
        "lens",
        list(LENSES),
        format_func=lambda lid: {k: v.title for k, v in LENSES.items()}[lid],
        label_visibility="collapsed",
    )
    lens = lens_by_id(lens_label)
    st.markdown(
        f"<h1 style='margin-bottom:0'>Slash <span style='color:#646262'>· {lens.title.lower()} on HydraDB</span></h1>"
        "<div class='section-label'>github + npm + osv · graph-derived core "
        "· llm-assisted when GROQ_API_KEY is set</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([3, 2])
    with left:
        st.markdown('<div class="section-label">ask</div>', unsafe_allow_html=True)
        q = st.text_input(
            "question",
            placeholder="ask about the real dependency corpus…",
            label_visibility="collapsed",
        )
        asked = False
        llm_on = st.checkbox(
            "llm summary (groq)",
            value=bool(__import__("os").environ.get("GROQ_API_KEY")),
        )
        if st.button("⏎ run", type="primary"):
            asked = True
        for i, dq in enumerate(DEMO_QUESTIONS):
            if st.button(dq, key=f"demo{i}"):
                q = dq
                asked = True
        if not st.session_state.get("history") and st.query_params.get("q"):
            q = st.query_params["q"]
            asked = True
        if q and asked:
            from src.pipeline import answer_with_result

            try:
                verdict, result = answer_with_result(_client(), q, lens, llm=llm_on)
            except Exception as exc:  # noqa: BLE001 - the console must surface any backend error
                verdict = None
                st.error(f"query failed: {exc}")
            if verdict is not None:
                st.session_state.setdefault("history", []).append(
                    {"q": q, "verdict": verdict, "result": result, "lens": lens.id}
                )

        for item in list(st.session_state.get("history", [])):
            st.markdown("---")
            _render_verdict(item["q"], item["verdict"], item["result"])
            _render_evidence(item["verdict"], item["result"])

    with right:
        last = st.session_state.get("history", [])
        if last:
            item = last[-1]
            _thought_process(item["verdict"])
            _stream_console(item["verdict"], item["result"])
            _render_subgraph(
                item["result"], lens_by_id(item.get("lens", "dependency-graph"))
            )
        else:
            st.markdown(
                "<span class='bullet'>[x] ask a question to see the pipeline.</span>",
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    run()
