# Glossary

> Source of truth: domain terms as used across `src/`, `docs/`, and the UI. Keep in alphabetical order.

| Term | Meaning | Notes |
|---|---|---|
| **Abstention** | A first-class verdict meaning "the graph does not contain enough evidence to answer" | Never an error; rendered with a warning badge in the UI |
| **Advisory** | A security event: a package version flagged malicious with a time window it was live | Field: `advisory_id`, `published_at`, `valid_until` |
| **Blast radius** | The full set of nodes transitively reachable from a compromised node via dependency edges | Computed with bounded `*1..6` reverse traversal |
| **Edge** | A directed relationship in HydraDB | Patterns are directed; both endpoints typed |
| **Evidence chain** | The ordered list (Cypher + params + rows + elapsed) that produced a verdict | Always rendered, never summarized away |
| **Ground truth** | The planted, known-correct answers (`ground_truth.json`) used to score the system | Held-out subset for eval |
| **Lockfile** | An application's pinned dependency resolution at a point in time | `resolved_at` edge timestamp vs the advisory window |
| **Maintainer contagion** | Exposure that spreads through shared human/infra identity, not just dependency edges | `MAINTAINED_BY` traversal |
| **PackageVersion** | A specific version node of a package | `name + version`, `published_at`, flags |
| **QueryPlan** | The ordered set of concrete graph queries chosen for a user question | Output of the Researcher; validated by Auditor |
| **Reputation** | Graph-derived trust signal (popularity, in-degree, maintainer history) | Used for typosquat scoring |
| **Service** | An internal application we protect | Connected via `USES_LOCKFILE → Lockfile` |
| **Subgraph density** | Fraction of expected evidence actually present in a retrieval | Low density ⇒ abstain |
| **Temporal edge** | Edge carrying `valid_from`/`valid_until` (or event timestamps) | Our convention; sentinel `9999999999` = live |
| **Typosquat** | A package whose name is adversarially close to a popular one, with weak reputation | Scored by edit-distance + graph signals |
| **UNWIND batch** | HydraDB bulk-write path: `UNWIND $rows AS row ... MERGE` | Our ingestion mechanism |