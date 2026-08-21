---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-13'
last_review: '2026-08-13'
next_review: '2026-11-11'
prelude: Readme (explanation) for dopemux documentation and developer workflows.
---
# Jules Adapter for PR-Prep-Specialist

Superseded by [`../../operator-contract.md`](../../operator-contract.md).

This file previously claimed `Contract: TP-PRPS-000-1.0.0`, a "7-step
canonical workflow", "Identical decision logic", a "Uniform handoff
structure", and `IMPLEMENTED AND COMPLIANT` status via
`platform: jules, method: task_templates`. That contract, its seven-step
ceremony, and its compliance claim are retired.

## Current behavior

Jules invokes `pr-prep-specialist` via task templates. All prep behavior
— the conditional S0-S8 workflow, `L0-L3` risk lanes, prep states, and the
V2 handoff schema — is defined once, canonically, in
[`operator-contract.md`](../../operator-contract.md). This adapter does
not define its own workflow steps, decision logic, or handoff structure;
it does not claim compliance against a retired contract, and it never
grants non-draft or merge-ready PR creation authority independent of the
operator contract's `DRAFT_ONLY` default (§S4) and explicit
operator/Task Packet authorization.

## Platform-specific notes

- **Invocation**: task templates (`platform: jules, method: task_templates`).
- **Docs**: [`../../../../../pr_prep/adapters/jules/readme-2.md`](../../../../../pr_prep/adapters/jules/readme-2.md)
  (compatibility pointer only).

This stub is kept only so existing links into this filename keep resolving.
