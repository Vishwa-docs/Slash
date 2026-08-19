# Architecture Overview

> Source of truth: this stack (index → context → containers → components → data flows → trust boundaries),
> then `docs/architecture/decisions/` (ADRs) for significant choices.

## The one-paragraph story

Slash is a **read-mostly analytics console** over a large software-ecosystem graph held in
HydraDB. Raw ecosystem data (packages, versions, maintainers, services, lockfiles, advisories)
is normalized into HydraDB via batched `UNWIND` Cypher. At query time, a small orchestration
layer ("the agents") turns a natural-language request into a small set of **parameterized graph
traversals**, runs them against HydraDB, checks the retrieved evidence (density, temporal
consistency, contradiction), and returns either an answer with a **traceable evidence chain** or
an explicit **abstention**. A Streamlit console renders the queries, evidence, subgraph, and verdict.

## Reading order

| Doc | Answers |
|---|---|
| `system-context.md` | What sits around the system (users, HydraDB, datasets, LLM optionality) |
| `containers.md` | The runtime pieces (HydraDB container, Python app, Streamlit) |
| `components.md` | Internal modules and their responsibilities |
| `data-flows.md` | Ingestion + query lifecycles, traceability, abstention path |
| `trust-boundaries.md` | What is trusted vs. untrusted input, and why |
| `decisions/` | ADR-0001 … — why we chose what we chose |

## Core architectural principles

1. **Graph-native first.** Every user-visible answer is produced by an actual traversal against a
   live HydraDB node. If a feature could be answered by a vector lookup, it is out of scope.
2. **Evidence over confidence.** Every answer renders the Cypher + rows that produced it.
   When evidence is thin, the system abstains instead of hallucinating.
3. **Optional-LLM.** All LLM call sites have deterministic fallbacks; the product must run fully
   with a free tier (no API key).
4. **Small, testable cores.** Query building and adjudication logic are pure functions with unit
   tests; the UI is a thin shell over them.
5. **Temporal as data.** Time is modeled as edge/node properties (`valid_from`, `valid_until`,
   `published_at`, `resolved_at`), never via destructive updates.