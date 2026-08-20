# Trust Boundaries

> Source of truth: `docs/architecture/index.md` + `docs/security/threat-model.md`.

## Boundaries

| # | Boundary | Trusted side | Untrusted side | Notes |
|---|---|---|---|---|
| B1 | User input → Intent | Our prompt template + classifier | Free-text question | Classifier is deterministic; LLM refine runs only on already-classified params, wrapped by Pydantic validation |
| B2 | Cypher → HydraDB | Cypher produced by `graph_service.py` builders only | Never user text spliced into Cypher | No f-string interpolation of user input into queries — strictly parameterized |
| B3 | Dataset files → Ingest | `scripts/fetch_github.py` output (`data/github`) | Imported SBOM/advisory files, if used | Validate schema before ingest; cap record counts |
| B4 | HydraDB → Client | HydraDB node | Query results (potentially malformed) | Client parses rows with strict schemas; a malformed row fails the query, not the app |
| B5 | Optional LLM → Adjudicator | Structured-output contract (Pydantic schema) | Raw LLM text | Re-validate LLM JSON against the verdict schema; on failure, fall back to the deterministic path |

## Rules that hold everywhere
- User text is **data**, never code/queries. All Cypher is generated, then parameterized.
- The auth token lives in a local file; the repo contains no secrets (`GRANT_NONE` on token scope is
  impossible, but the token only authorizes the local demo instance; do not copy it into logs).
- Introspection endpoints are local-only (`127.0.0.1`).
- An abstention is never an error — it is the correct, honest output. Hiding a failed query behind a
  fake answer is the only forbidden behavior.

## What "what would we lose without HydraDB" means here
- Without HydraDB, the transitive closure (the blast radius) has no home. A vector/relational
  substitute either cannot express the traversal or cannot do it at query time. The trust boundary
  story is: the graph *is* the source of truth, and the console proves each claim with the
  traversal that produced it.