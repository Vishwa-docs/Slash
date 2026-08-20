# Video script — Slash (≤ 3 min)

Purpose: problem → project → live demo → "where HydraDB is used & why it matters".
Segment timings are targets; the whole thing must fit in 180 seconds.

## 0:00–0:35 — Problem

> 09:00. A maintainer account gets phished and a poisoned `chalk` version ships to your internal
> registry. At 09:06 your security team asks: *which services are exposed?* — and they need the
> answer in seconds, with evidence, or they are guessing.
>
> "Which services are transitively exposed by a compromised package" is a **reverse-dependency
> closure over a dependency graph**. It is a traversal problem. A vector store cannot answer it at
> all — embeddings don't tell you who depends on whom.

## 0:35–1:30 — Project (Slash on HydraDB)

> Slash ingests an npm-style ecosystem into **HydraDB**, a graph database on object storage, and
> answers supply-chain questions live, with zero LLM tokens:
>
> - Which internal services are transitively exposed?
> - Which apps resolved the bad version while it was live?
> - Which maintainers/infrastructure are shared with the compromised package?
> - Which nearby names are likely typosquats?
> - And the complete blast radius — with an **evidence chain**: the exact Cypher, params, rows,
>   and latency that produced each answer.
>
> The architecture is three tiny deterministic agents: a **Researcher** that classifies the
> question, an **Auditor** that recomputes temporal flags and checks for contradictions, and an
> **Adjudicator** that renders a verdict — or **abstains explicitly** when the graph doesn't have
> the evidence.

## 1:30–2:30 — Live demo (on screen)

> `streamlit run app.py`. We ask: *which services are exposed by chalk@6.0.0?*
>
> - Left panel: verdict pill `EXPOSED` → `gateway, notifications`, and the evidence chain — each
>   expander shows the parameterized Cypher, the rows, row count and latency.
> - Right panel: the live query console streaming each traversal step, the thought process
>   (Researcher → Auditor → Adjudicator), and the Plotly subgraph with the seed marked red.
> - *what is the blast radius?* → the closed set with hop levels.
> - *was lodash@4.17.20 resolved while live?* → forensics: the app that resolved it inside the advisory window.
> - A nonsense question → the system says it can't answer, instead of making something up.

## 2:30–3:00 — Why HydraDB + close

> HydraDB is load-bearing here, not decorative: the blast radius is a bounded variable-length
> traversal, forensics is temporal filtering over live edge properties, and ingestion is batched
> `UNWIND`/`MERGE` upserts routed straight into the object store.
>
> We hit real engine constraints and honoured them — the reverse closure is walked level-by-level
> because HydraDB's variable-length paths are outgoing-only, and every query we ship uses the
> documented cypher subset. Every number in the eval table comes from a live run; scores are
> precision 1.00 / recall 1.00 / F1 1.00 on the held-out advisories.
>
> *Slash — blast-radius intelligence computed natively in HydraDB. Proof that graph databases do
> the work vector indices can't.*