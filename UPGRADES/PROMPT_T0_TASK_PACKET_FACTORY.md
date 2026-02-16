Goal: docs/task-packets/TP-*.md generated from truth maps + risks + repo governance rules.

Inputs:
- R backlog + R2 risks + X catalogs

Outputs:
- TP_INDEX.json
- TP_<ID>_<slug>.md (default top 10)

Stop conditions:
- Any TP missing: scope, invariants, commands, acceptance criteria, rollback, stop conditions.
- Any TP proposes refactor without evidence-driven necessity.
