---
id: codex-pr-body-blueprint
title: Codex PR Body Blueprint
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-20'
last_review: '2026-05-20'
next_review: '2026-08-18'
prelude: Reusable PR body blueprint for Codex-governed Dopemux macro-packets and same-packet fixes.
---
# Codex PR Body Blueprint

Use this body for Codex-governed macro-packet PRs. Replace every placeholder with observed evidence. Do not treat `@codex review` as proof of completion; it is a review pass request, not acceptance, runtime validation, or semantic correctness proof.

```markdown
## Summary
- <Changed outcome 1.>
- <Changed outcome 2.>

## Scope
<Describe the exact packet scope. Replace this line before opening the PR.>

In scope:
- `<changed surface or artifact>`

Allowlist:
- `<allowlisted path>`

Out of scope:
- Runtime/service behavior
- Docker startup
- Live provider calls
- Live extraction
- Account-specific checks
- Files outside `commit.allowlist`

## Validation
Include exact command outputs and exit codes.

PASS:
- `<command>` -> exit `<code>`

FAIL:
- `<command>` -> exit `<code>`
- Cause:
- Same-packet fix status:

## NOT_RUN
- Runtime/service validation: <reason>
- Docker startup: <reason>
- Live provider calls: <reason>
- Live extraction: <reason>
- Live preflight/account-specific checks: <reason>
- Secret inspection: <reason>

## Residual Risks / UNKNOWNs
- UNKNOWN: <unresolved repo/runtime/product fact>
- Risk: <remaining risk after validation>

## Same-Packet Fixes
- Finding:
- Fix:
- Proof refreshed:
- Validation rerun:

## Review Routing
@codex review

Review this PR against `AGENTS.md`, the active Task Packet, `commit.allowlist`, exact validation evidence, proof completeness, and preservation of `UNKNOWN`, `CONFLICTING`, `NOT_RUN`, and residual risk.
```

## Same-Packet Fix Section

Use the same-packet fix section whenever a reviewer finds a proof gap, validator failure, stale PR statement, or missing template requirement that stays inside the active packet target and allowlist. Keep the finding visible, update the proof artifact, rerun the relevant validation, and avoid opening a follow-on packet for a correction that belongs to the current packet.
