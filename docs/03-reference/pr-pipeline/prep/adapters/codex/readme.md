---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Readme (explanation) for dopemux documentation and developer workflows.
---
# Codex Adapter for PR-Prep-Specialist

Superseded by [`operator-contract.md`](../../operator-contract.md).

This file previously documented an exact 7-step `INSPECT_BRANCH_STATE →
... → HANDOFF_TO_PRMS` workflow, a fixed eight-artifact bundle (including
`BRANCH_STATE.json` and `PR_HANDOFF_BUNDLE.json` as mandatory outputs), a
`risk_hint: LOW|MEDIUM|HIGH` posture, and `CREATE_READY`/governance-approval
language implying independent merge-ready PR creation authority. That
ceremony is retired.

## Current behavior

Codex invokes `pr-prep-specialist` as a skill (`skill_call("pr-prep-specialist", ...)`,
configured under `AGENTS.md`). All prep behavior — the conditional S0-S8
workflow, `L0-L3` risk lanes, prep states, and the V2 handoff schema — is
defined once, canonically, in
[`operator-contract.md`](../../operator-contract.md). This adapter does not
define its own artifacts, risk vocabulary, or creation posture; it does not
require any fixed number of artifacts, and it never grants non-draft or
merge-ready PR creation authority independent of the operator contract's
`DRAFT_ONLY` default (§S4) and explicit operator/Task Packet authorization.

## Platform-specific notes

- **Invocation**: `skill_call("pr-prep-specialist", context=repository_context, params={})`.
- **Configuration**: `AGENTS.md` skill registration (`enabled`, `version`, `description`).
- **Output format**: whatever the actual run produces per the V2 handoff
  schema (`operator-contract.md` §9) — not a fixed artifact list.

This stub is kept only so existing links into this filename keep resolving.
