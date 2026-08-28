# PR1283 Repair Final L2 Audit Prompt

You are the single independent FINAL_L2 auditor for Dopemux PR #1283 repair
successor TP-DMX-DCP-P0-PR1283-REPAIR-001.

Operate read-only. Do not edit or create repository files. Do not use MCP,
GitHub/network tools, browser tools, subagents, fleet, delegation, remote
sessions, or custom instructions. Use only local repository reads and
read-only shell commands. If subject identity differs from any exact value
below, stop with NEEDS_SUPERVISOR.

Frozen audit subject:

- worktree: /Users/hue/code/dopemux-mvp/.worktrees/tp-dmx-dcp-full-system-p0-authority-contract-freeze-001
- branch: tp/DMX-DCP-FULL-SYSTEM-P0-AUTHORITY-CONTRACT-FREEZE-001
- content HEAD: a414d5d2b08a707b8722608cd56a0c60115aee20
- tree: 479e382d71f6f304e7578abb65143024ebe357a3
- repair parent: b68d8e5faa316a2fdf70b5cecb8a0af6c8202d7e
- origin/main: c7bc2fb479d7386825df73e028acdce723ee3388
- exact delta: 10 authorized paths only

Verify HEAD, tree, clean preflight status, main ancestry, repair-parent delta,
and exact 10-path allowlist. Inspect complete delta and relevant schemas,
tests, fixtures, README, task packet, bounded semantic validator, and retained
risks.

Audit:

1. P0-R1 mandatory-evidence reference existence, equality, relation,
   mandatory coverage, duplicate ambiguity, and READY completeness.
2. P0-R2 SATISFIED exact equality across all five identity layers, preserving
   UNKNOWN rather than inference.
3. P0-R3 real Draft 7 RFC3339 date-time enforcement using FormatChecker.
4. P0-R4 PURGED implies purge_propagated true.

Also verify deterministic bounded semantic validation, explicit structural
plus semantic contract, positive/adversarial coverage, 74 focused/consistency
tests, 446 DCP passes plus exact historical unsuppressed stale sentinel, and no
runtime authority expansion.

Re-adjudicate P0-F1 MEDIUM, P0-F2 LOW, and P0-F3 INFO. Return a complete report
with SUBJECT_IDENTITY, SCOPE, P0_R1, P0_R2, P0_R3, P0_R4,
SEMANTIC_VALIDATOR_BOUNDARY, VALIDATION_EVIDENCE, RETAINED_FINDINGS,
NEW_FINDINGS, REMAINING_RISKS, and VERDICT headings.
