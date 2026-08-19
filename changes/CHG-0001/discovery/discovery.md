# Discovery — CHG-0001

## What we know (evidence-backed)
- HydraDB: Rust graph db on object storage; Docker image `ghcr.io/hydra-db/hydradb:latest`; ports Bolt 7687 / HTTP 8443 / admin 9090; OpenCypher subset per `hydradb/cypher-compat.md`; bulk-write via `UNWIND ... MERGE`; `algo.*` path procedures; WHERE limited to comparisons + STARTS WITH (no IN/IS NULL/CONTAINS/ENDS WITH). Source: exploration + graphify context graph + hydradb README.
- Winning prior art: GDELT Open Intelligence Agent (ArangoDB/NVIDIA GTC 2025) = Streamlit + ReWOO planner + thought-process panel + Plotly subgraph. Source: `docs/reference/strategy-analysis.md`, `GDELT-AQL-NetworkX-Agent/`.
- Rules: work must start on/after Aug 12, 2026; submission = form + ≤3-min video + public licensed repo; submission deadline Aug 20, 11:59 PM PT. Source: `docs/reference/hack-hydra-participant-guide.txt`.
- Today's date: Aug 19, 2026 → remaining window ~36h; the plan compresses phases.

## Confirmed decisions (see .state/decision-index.json)
Track 02A · Python+Streamlit+Plotly · HTTPS client primary · temporal-as-properties ·
deterministic dataset+ground truth · deterministic intent router · bounded traversal.

## Open questions
1. Official dataset file availability from organizers.
2. Whether to enable optional LLM (requires team approval, stays OFF by default).
3. Deployed link vs local demo (local is acceptable per rules).