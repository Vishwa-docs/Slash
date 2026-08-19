# ADR-0002 — Python + Streamlit + Plotly (port the GDELT winning formula)

- **Status:** accepted
- **Date:** 2026-08-19
- **Owner:** team
- **Links:** `docs/reference/strategy-analysis.md` (GDELT first-place decomposition), `DESIGN.md`

## Context
The highest-probability UI formula from the prior art (`GDELT-AQL-NetworkX-Agent`, 1st place at
ArangoDB/NVIDIA GTC) is: Streamlit chat + a live "agent thought process" panel + interactive
network visualization, backed by a tool-routing agent. We also have a `DESIGN.md` (terminal-native
monospace) and tight time.

## Considered options
| Option | Pros | Cons |
|---|---|---|
| **Streamlit + Plotly (chosen)** | One language; fastest to a beautiful interactive demo; Plotly subgraph viz proven in the winner; DESIGN.md maps cleanly onto it | Streamlit styling is global-CSS-driven (needs careful custom CSS for DESIGN.md fidelity) |
| Next.js + react-force-graph | More "wow" | Two stacks in the remaining hours; heavier; slower to iterate |
| Streamlit + react-force-graph via component | Nice graph | Extra component boundary; more risk |
| CLI-only | Shipped | Strategy doc explicitly warns: *do not submit a CLI* |

## Decision
Python 3.11, Streamlit (`app.py`), Plotly for subgraph rendering, Pydantic for typed schemas,
pytest for tests. Custom CSS implements the DESIGN.md design language (mono font stack,
cream canvas, 4px radius, hairline sections, ASCII brackets, dark console panel, semantic colors).

## Consequences
- UI tokens live in `DESIGN.md`; `docs/ux/` holds the mapping to Streamlit components.
- Graph analysis beyond `algo.*` runs client-side in `networkx` (same pattern as the winner).
- Deploy demo = `streamlit run app.py` after `docker compose up`.