# Personas

> Source of truth: `vl/PLAN.md`. Two personas drive the demo and the README narrative.

## 1. The security analyst ("Maya")
A staff SOC / AppSec engineer whose org just got caught by a supply-chain worm. Her questions:

- "Which of our services are transitively exposed by `some-lib@1.2.0`?"
- "Which apps resolved the bad version while it was live?"
- "Which packages share a maintainer with the compromised one?"
- "Are there typosquats next to `react` that we accidentally pulled in?"
- She **distrusts** confident answers -- she wants the traversal shown, and she wants the system to
  *say so* when the data isn't there (that honesty is what gets adopted by enterprises).

## 2. The tech lead / judge ("Dev")
Wants to see that this is a real graph problem with real HydraDB usage:
- "Show me the Cypher." → evidence chain panel.
- "Show me it can't be done in a vector DB." → the transitive closure story.
- "Show me scale for the demo." → the eval table (precision/recall/latency/cost) in `docs/research/scoring.md`.

## Demo script personas in action
Maya asks three questions (blast radius → temporal forensics → typosquat). Dev clicks "see query"
each time and watches the dark console panel render the traversal and the subgraph recolor.

## Key outcome metrics for both
| Metric | Target |
|---|---|
| Query latency (p95) | < 1 s on the reference dataset |
| Abstention rate on asked-out-of-domain questions | 100% -- refuses instead of inventing |
| Precision/recall on held-out advisories | measured & reported (no fabricated number) |
| Time to demo | `docker compose up` → Streamlit → answer in < 2 min |
| Time to reproduce | `pip install -r requirements.txt` + 2 commands |