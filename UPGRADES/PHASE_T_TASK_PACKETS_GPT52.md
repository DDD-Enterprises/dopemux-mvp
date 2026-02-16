# Phase T (GPT-5.2): Task Packet factory (implementation-ready, but still separate from Opus)

## Purpose
Turn R/R2/X outputs into bounded Task Packets you can hand to Codex/Claude Code implementers.

## Output artifacts
TASK_PACKET_QUEUE.md (ordered)
TP_* stubs in markdown format (no code changes automatically)

## Prompt
ROLE: Task Packet author (Supervisor).
INPUTS:
- BACKLOG_FROM_GAPS.md
- INVARIANTS_AND_BREAKPOINTS.md
- DEV_CHANGE_GUIDE.md
- FEATURE_PHASE_MATRIX.md
- PORTABILITY_AND_MIGRATION_RISK_LEDGER.md

GOAL:
Generate a sequence of minimal Task Packets that:
- resolve UNKNOWNs first
- enforce boundaries (Trinity, determinism, append-only)
- isolate control plane dependencies (repo vs home)
- support MCP->hooks migration safely
- strengthen workflow tests

OUTPUT:
1) TASK_PACKET_QUEUE.md
   - prioritized list with rationale

2) For the top N=10 packets: output each as TP markdown:
   - Objective
   - Scope (in/out)
   - Invariants
   - Plan (numbered)
   - Exact commands to run
   - Output capture rules
   - Acceptance criteria
   - Rollback steps
   - Stop conditions
   - Files likely touched (from breakpoints), but mark UNKNOWN if not evidenced

RULES:
- No refactors unless required.
- Prefer mechanical changes.
- Every TP references evidence from earlier phases.
