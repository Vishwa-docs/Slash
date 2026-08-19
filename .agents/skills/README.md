# Vendored Skills

Vendored (approved, pinned) skills live under `vendor/`. Each entry must be recorded in
`.capabilities/registry.yaml` + `.capabilities/capability.lock` before use.

| Skill | Origin | Status | Purpose |
|---|---|---|---|
| ponytail | ~/Desktop/HackCentral/skills/ponytail | approved | Lazy-but-correct engineering discipline |
| ponytail-audit / -debt / -gain / -help / -review | ~/Desktop/HackCentral/skills/ | approved | Ponytail ecosystem helpers |

## graphify
Not vendored as a skill file; installed as a CLI (`graphify 0.9.46`), documented under
capability `cap.skill.graphify`. Context graph: `docs/research/hydradb-context-graph/`.
Refresh: `graphify update <path-to-hydradb>`.
