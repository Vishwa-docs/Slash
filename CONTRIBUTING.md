# Contributing

Hack Hydra contribution lanes (all work is new code after Aug 12, 2026):

## How a change flows
1. Open a pull request or file a `changes/CHG-XXXX/change.yaml`.
2. Read the governing docs (`AGENTS.md`, `DESIGN.md`, `docs/architecture/hydradb-notes.md`).
3. Implement one vertical slice; run the checks; **save output to `.evidence/runs/`**.
4. Update `CHANGELOG.md`, `.state/task-graph.json`, and any doc that drifted.
5. PR with the `PULL_REQUEST_TEMPLATE.md`.

## Reviewer rules (borrowed from the factory brief)
- Assume claims are false until evidence is shown (command output, test run, screenshot).
- Check scope, duplication, DESIGN.md fidelity, HydraDB-notes fidelity, and abstention honesty.
- No rewriting patches during review; report BLOCKER/HIGH/MEDIUM/LOW/QUESTION.
- Approve only with fresh evidence.

## Before you open the repo to judges
- `scripts/smoke.sh` passes end to end.
- `README.md` setup instructions work from a clean clone.
- No `TODO`/`FIXME` in the demo-critical path without a `ponytail:` note explaining the ceiling.