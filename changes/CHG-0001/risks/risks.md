# Risks — CHG-0001

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | HydraDB container won't start on the judges' machine / our builder | M | H | `src/infra/hydradb-up.sh` + documented env contract; pinned Docker image; trap messages to usebolt/HTTP alternately; ASG falls back to Bolt | team |
| R2 | A pinned query is unsupported by the OpenCypher subset | M | H | Start features from the documented subset only; verify each query live in P3; never ship unverified queries | coding-agent |
| R3 | Context window too small => agent loses the plan | H | M | Phased PROMPT with files-to-read per phase; docs are the only context the agent needs; run one phase per session | team |
| R4 | Synthetic dataset feels fake to judges | M | M | Realistic topology, planted advisories mirrored from OSV-style facts, README transparency + path to real SBOM | team |
| R5 | Abstention is weak => loses points on "honesty" | M | H | Deterministic density gate + unit tests; out-of-vocabulary abstention exercised in demo script | coding-agent |
| R6 | Latency > 1 s in demo | M | M | Bounded hops (ADR-0007), batch ingest, latency captured per query; reduce hop ceiling if needed | coding-agent |
| R7 | Run out of time before README/video | H | H | P6 is scheduled with hours of buffer; "stop adding features, test what you built" rule from participant guide | team |
| R8 | Commit timestamps predate Aug 12 (inherited scaffold) | L | H | Author scaffold commits dated Aug 19 (all blacklisted work is excluded); describe inherited upstream commits in README | team |
| R9 | LLM (optional) leaks or produces garbage | L | M | Quarantined capability; OFF by default; Pydantic-validated structured outputs only | team |

## Worst case
If HydraDB cannot run in the judge environment, the repo still ships: screenshots, README, eval
table, and a clear "How We Used HydraDB" narrative demonstrate a functional build — but the live
demo is the pain point we must protect (R1).