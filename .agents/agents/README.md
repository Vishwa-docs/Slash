# Agent Roles (bounded; from the factory brief)

- Requirements Analyst — interview/classify requirements (docs). 
- Architect — RFCs/ADRs, do not implement.
- Implementer — one vertical slice per task packet (`vk/PROMPT.md`).
- Independent Reviewer — evidence-backed findings; approve/request-changes.
- Release/SRE — verify the demo artifact is submission-ready before the deadline.

The coding agent acts as Implementer (phases) + Resident Reviewer (its own diff) and must
record evidence in `.evidence/runs/`. Roles are guides, not separate processes.
