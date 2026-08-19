# Security, Privacy & Threat Model

> Source of truth: `docs/architecture/trust-boundaries.md`. Tier: T2/T3 (public repo, local demo,
> no production data). This is a hackathon project — the model is about not embarrassing ourselves
> and not shipping a vulnerability fashionable to show off.

## Assets
- The HydraDB auth token (local file, `.gitignore`d).
- The synthetic dataset + ground truth (public by design).
- The app (Streamlit) runs on localhost by default.

## Threat model (top table entries)

| # | Threat | Mitigation | Boundary |
|---|---|---|---|
| T1 | Prompt/code injection into Cypher | Cypher is built by builders only; user strings are parameters (`$name`, `$version`), never spliced. Fuzz test `intent.py` boundaries | B1/B2 |
| T2 | Sample question text that looks like code | Classifier is deterministic; it extracts entities via safe regexes; LLM refine is schema-validated | B1/B5 |
| T3 | Malformed HydraDB response breaks the app | Client parses rows into strict Pydantic models; failure surfaces as error + abstention, not a crash | B4 |
| T4 | Token leakage into logs/screenshots | Token read from file only; `scripts/smoke.sh` redacts; never echoed in README/demo | all |
| T5 | Ingest of untrusted SBOM/advisory files | Validate schema, cap record counts, reject unknown labels before creating nodes | B3 |
| T6 | LLM (optional) returns garbage JSON | Pydantic-schema validation; on failure fall back to deterministic path; never trust free text | B5 |
| T7 | Repo accidentally committed with secrets | `.gitignore` (`.env`, `*.token`, `.hydradb/`); secret-scan before submission | CI |

## Data classification
- **Public:** source code, docs, synthetic dataset, ground truth, README.
- **Internal-source:** the exact eval numbers (publish only final table; keep intermediate raw in
  `.evidence/`).
- **Prohibited (none planned):** real customer data, real credentials, real npm registry secrets.

## Privacy
- No PII ingested. "Maya/Dev" personas are fictional. No telemetry beyond local latency/cost logs.

## Abuse cases
- Someone pastes a huge query / thousands of names → query budget + batch caps reject.
- Someone asks about a fake package → empty evidence → abstention (correct behavior, not a leak).
- Someone asks "what would we lose without HydraDB" → README answers it; demo shows a vector DB
  cannot express the closure.

## Explicit non-goals (out of scope for a 36-hour build)
- No authN/authZ (localhost demo).
- No encryption at rest (local demo data only).
- No pen-testing sprint; do the T1 fuzz smoke (`scripts/smoke.sh` includes it).