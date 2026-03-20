---
id: IMPLICIT_ACTION_POLICY
title: Implicit Action Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Implicit Action Policy (explanation) for dopemux documentation and developer
  workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Flight deck reference

## Implicit Action Policy

## Purpose

This document explicitly enumerates which actions in the flight deck fire automatically
(implicitly) versus which require operator staging before execution.

## Automatic Actions (No Operator Staging Required)

These actions are safe to execute on every cycle without operator intervention:

| Action | Trigger Condition | Rationale |
|--------|-------------------|-----------|
| `REFRESH_STATE` | Every cycle start | Read-only; never mutates PR state |
| `SELECT_TACTIC` | After refresh | Pure computation; no side effects |
| `RECOMPUTE_SUMMARY` | After any meaningful event | Read-only state derivation |
| `EMIT_TRACE` | End of cycle | Append-only audit log |

## Conditional-Automatic Actions (Fire Only When Posture Permits)

These actions fire automatically only when ALL conditions are met:

| Action | Required Posture | Required in allowed_actions | Patch Class |
|--------|------------------|-----------------------------|-------------|
| `APPLY_FIX` (local) | GO_SUPERVISED_ONLY or GO_FULL_AUTO | Yes | SAFE_LOCAL_EDIT |
| `APPLY_FIX` (meta) | GO_SUPERVISED_ONLY or GO_FULL_AUTO | Yes | SAFE_METADATA_EDIT |

## Staged Actions (Always Require Operator Approval)

These actions are NEVER executed implicitly:

| Action | Why Staged |
|--------|-----------|
| `MERGE` | Irreversible; highest-risk mutation |
| `APPROVE` | Operator intent required |
| `APPLY_FIX` (SIGNOFF_REQUIRED_PATCH) | Risk class mandates human gate |
| `APPLY_FIX` (LOW_RISK_PATCH_PROPOSAL cross-file) | Cross-file scope requires staging |
| `CLOSE` | Terminal PR state change |
| `REQUEST_CHANGES` | Operator communication requiring review |

## Invariants

1. An action classified as NEVER-IMPLICIT cannot be promoted to automatic execution by any posture change.
2. MERGE is always staged, even in GO_FULL_AUTO posture.
3. All staged actions generate a `SignoffPacket` or `DeferPacket` before execution.
