# Copilot instructions for Slash

- Read `AGENTS.md` and `vl/PLAN.md` before answering. Follow the current phase in `vk/PROMPT.md`.
- Respect the HydraDB OpenCypher subset in `docs/architecture/hydradb-notes.md`. Never invent queries.
- Follow `DESIGN.md` for UI. Keep the app working without an LLM key.
- Abstention is a feature: prefer "not enough evidence" over an invented answer.
- Save command/test output to `.evidence/runs/<phase>/` before claiming completion.
- Small diffs. Laziest correct solution (ponytail discipline).