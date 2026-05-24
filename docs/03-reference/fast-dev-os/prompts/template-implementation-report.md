---
id: fast-dev-os-template-implementation-report
title: Fast Dev OS — Implementation Report Template
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Standard shape for an implementer's post-execution report. Covers what was done, what was validated, what was not run, residual risks, and unknowns — input to the auditor and operator.
---
# Fast Dev OS — Implementation Report Template

## Relationship to governance

This template **operationalizes** [`codex-authority-refresh.md`](../../governance/codex-authority-refresh.md) and AGENTS.md §9 proof requirements; it **does not override** them.

## Lane

**L0–L6** — applies to all lanes; depth of detail scales with lane.

## When to use

Immediately after the implementer completes execution (and before the operator accepts/rejects). One report per Task Packet. The report is consumed by:

- The auditor (if lane ≥ L3) — fed into [`template-audit-prompt.md`](template-audit-prompt.md).
- The operator — fed into [`template-acceptance-decision.md`](template-acceptance-decision.md).

The report should mirror but not duplicate the PROOF.json — PROOF.json is the structured contract; this report is the human-readable narrative.

## Template

```markdown
# Implementation Report — <TP-ID>

## Identity
- TP path: `<task-packets/generated/TP-*.json>`
- TP ID: `<TP-DMX-...>`
- Implementer: `<Claude Code | Codex CLI | Gemini | Grok | Jules | GitHub Copilot> (<version>)`
- Lane: `<L0|L1|L2|L3|L4|L5|L6>`
- Worktree: `<absolute path>`
- Branch: `<codex/... or feature/...>`
- Base branch: `<main or specified>`
- Starting HEAD: `<SHA>`
- Ending HEAD: `<SHA>`

## Summary (1-3 sentences)
<What changed and why, in plain terms.>

## Authority used
- AGENTS.md sections cited: `<§2 truth order, §4 lifecycle, §9 proof fields, §10 dangers, etc.>`
- Active TP: `<path>`
- Governance docs cited: `<list>`
- Specs cited: `<dopetask-canonical-spec.json, etc.>`
- Truth/PROJECT/ARCH docs cited: `<list>`

## Analysis performed
- What you inspected: `<files, configs, tests, runtime>`
- What you concluded: `<observations and inferred consequences>`

## Slices completed
| Slice | Label | Status |
|-------|-------|--------|
| S1 | preflight | PASS / FAIL / NOT_RUN |
| S2 | ... | ... |
| ... | ... | ... |

## Validations performed (bucketed; never collapse NOT_RUN into PASS)
### PASS
- `<command>` (exit code 0): `<short outcome>`

### FAIL
- `<command>` (exit code N): `<short outcome>`

### NOT_RUN
- `<what was not run>`: `<reason and residual risk>`

## Codereview status
- Tool: `<pal/codereview | other>`
- Model: `<gpt-5.2-pro | other>`
- Validation type: `<internal | external>`
- Verdict: `<LGTM | PARTIAL | FAIL>`
- Issues by severity: `{critical: 0, high: 0, medium: 0, low: N}`
- Continuation ID: `<for audit traceability>`

## Precommit status
- Tool: `<pal/precommit | other>`
- Verdict: `<SAFE TO COMMIT | UNSAFE | NEEDS_REWORK>`
- Issues found: `<N>`
- Continuation ID: `<for audit traceability>`

## Files changed
- Created: `<list of paths>`
- Modified: `<list of paths>`
- Renamed: `<old → new>`
- Deleted: `<list of paths>` (if any; should be rare)
- Allowlist compliance: PASS (`<N>` paths within TP allowlist) | FAIL (`<list of paths outside allowlist>`)

## Commit + PR
- Commit SHA: `<SHA>`
- PR URL: `<https://github.com/DDD-Enterprises/dopemux-mvp/pull/NNN>`
- PR blocker (if PR did not open): `<exact reason>`

## Residual risks
- `<RISK-ID>: <one-line description>` (`<deferred to / mitigated by>`)

## UNKNOWNs
- `<unresolved question or contradiction>` (`<recommended next action>`)

## Cleanup status
- Worktree: `<REMOVED | ACTIVE_PENDING_PR_MERGE | DEFERRED>`
- Branch: `<DELETED | RETAINED>`

## Notes for the auditor
<Anything the auditor should know before reviewing — context that didn't fit elsewhere.>

## Notes for the operator
<Anything the operator should consider before accepting — explicit asks, items needing decision.>
```

## Truth posture (applies to all reports)

> Never invent paths, commands, branches, PRs, tests, capabilities, or tool behavior. Never say done/complete/no issues without evidence. Distinguish observed vs inferred vs proposed vs unknown. If a validation did not run, mark NOT_RUN with reason — never collapse NOT_RUN into PASS.

## Anti-patterns to avoid

- "All tests pass" without listing which commands ran.
- "No issues found" without specifying what was checked.
- "Done" / "Complete" / "Ready to merge" without a complete PROOF.json.
- Marketing language ("blazingly fast", "100% secure", "magnificent").
- Inventing PR URLs or commit SHAs that don't exist.
- Glossing over `NOT_RUN` items.
- Omitting residual risks because they are inconvenient.

## After this report

- If lane ≥ L3: dispatch [`template-audit-prompt.md`](template-audit-prompt.md) for Gemini audit.
- Always: dispatch [`template-acceptance-decision.md`](template-acceptance-decision.md) for operator decision.
