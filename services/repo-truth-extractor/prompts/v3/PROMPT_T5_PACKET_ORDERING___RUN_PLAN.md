# PROMPT_T5 — PACKET ORDERING / RUN PLAN

TASK: Build the execution order for Task Packets using dependency-aware planning.

OUTPUTS:
- TP_RUN_PLAN.json
- TP_BACKLOG_TOPN.json

Rules:
- Build a dependency graph across packets and topologically sort the plan.
- Default precedence: control plane -> extraction -> arbitration -> synthesis.
- Produce a runnable sequence with blocking dependencies, parallel-safe groups, and gate checks.
- Include explicit prerequisites and postconditions per packet.
