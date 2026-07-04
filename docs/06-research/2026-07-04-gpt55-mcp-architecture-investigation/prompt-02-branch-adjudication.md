---
id: gpt55-mcp-architecture-prompt-02-branch-adjudication
title: GPT55 MCP Architecture Prompt 02 Branch Adjudication
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Phase 2 GPT-5.5 prompt for branch work adjudication.
---
# Prompt 02: Branch Adjudication

You are GPT-5.5 Pro performing Phase 2 of a Dopemux MCP/service architecture review.

Use Phase 0-1 outputs and `bundle-02-branch-adjudication.md`. Decide how to treat `claude/mcp-fleet-audit-complete` and PR #1002 relative to current `origin/main`.

## Required Output

1. Commit Adjudication Table:
   - commit
   - summary
   - accept/split/modify/reject/defer
   - reason
   - tests needed
   - authority impact
2. File Adjudication Table:
   - file
   - change type
   - architecture implication
   - accept/split/modify/reject/defer
3. Decision-Needed Table:
   - PR #1002 reconcile-first vs accept-after-fixes vs advisory-only
   - Exa retire vs wire
   - PAL lifecycle model
   - Serena surface strategy
   - PM source event promotion model
   - dead-surface deletion/archive/quarantine
   - personality contract scope
4. Branch-Risk Register.
5. Live-Reconciliation Gate: exact checks needed before architecture work may depend on open PR changes.
6. Carry-Forward Decisions For Phase 3.

Do not produce the final architecture until unresolved decision-needed items are clearly marked.
