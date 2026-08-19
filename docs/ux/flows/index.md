# UX Flows

> Source of truth: `DESIGN.md` (visual system) and `docs/product/features.md` (F1–F8).
> Implementation detail: Streamlit maps well to these flows via `st.session_state` + reruns.

## Screens
| Screen | Purpose | Key elements |
|---|---|---|
| **Console (home)** | Ask a question; see the verdict + evidence | Query input, dark "console" panel (live Cypher), thought-process panel, verdict badge, subgraph plot |
| **Scoring** | Show eval table | Precision/recall/F1, latency, cost; ground-truth provenance note |
| **About / How we used HydraDB** | The judging narrative | README-adjacent content, traversal-gif/screenshot |

## Primary flow — "Is my org exposed?"
1. Analyst types: "Which services are exposed by `some-lib@1.2.0`?"
2. Researcher classifies → plan [blast radius → service set].
3. Dark console panel streams the two queries; metrics tick.
4. Subgraph renders: services (blue), lockfiles (grey), packages (green), compromised (red),
   typosquats (amber). Path highlighted.
5. Verdict card: exposed services list + count + latency; "see evidence" renders rows + Cypher.
6. If evidence is thin → **abstention card** (warning color): "Not enough evidence in the graph."

## Secondary flow — forensics
1. "Which apps resolved `evil-lib@0.9.0` while it was live?"
2. Traversal filters `RESOLVES_TO.at` within the advisory window (precomputed flag + recompute).
3. Verdict: lockfile/app list + per-row `resolved_at` vs window.

## Interaction principles (from DESIGN.md, adapted)
- Monospaced everywhere; cream canvas; hairline sections; ASCII bracket markers `[+]` `[-]`.
- One dark surface ingredient: the live-query console panel (not body content).
- Semantic color only for verdicts: danger `#ff3b30` exposed, warning `#ff9f0a` typosquat/abstain,
  success `#30d158` clean, accent `#007aff` links.
- 4px radius on interactive elements; no shadows anywhere.

## Widget inventory (mapped to DESIGN.md components)
| DESIGN.md component | Streamlit realization |
|---|---|
| `button-primary` / `button-secondary` | `st.form_submit_button` styled via CSS |
| `text-input` / `textarea` | `st.text_input` / `st.text_area` styled input |
| `badge-section-label` | `st.caption` + hairline divider, mono font |
| `hero-tui-mockup` / `tui-prompt-row` | dark `st.container` card streaming last-query (CSS `.console-panel`) |
| `list-row` | `st.markdown("- [x] ...")` rendered as ASCII-bracket rows |
| semantic badges | `st.markdown` colored pills (danger/warning/success) |