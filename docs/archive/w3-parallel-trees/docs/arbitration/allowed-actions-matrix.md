---
id: ALLOWED_ACTIONS_MATRIX
title: Allowed Actions Matrix
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Allowed Actions Matrix (explanation) for dopemux documentation and developer
  workflows.
---
# Allowed Actions Matrix

## Purpose
This matrix defines the boundaries of automation for the High-Risk Arbitration Lane.

## Authorization Matrix

| Action Class | Mode: ADVISORY | Mode: LIVE_SAFE | Mode: AUTONOMOUS |
| :--- | :---: | :---: | :---: |
| **Evidence Pack Generation** | ✅ | ✅ | ✅ |
| **Role Arbitration** | ✅ | ✅ | ✅ |
| **Consensus Decision** | ✅ | ✅ | ✅ |
| **Defer Packet Generation** | ✅ | ✅ | ✅ |
| **Merge Plan Generation** | ✅ | ✅ | ✅ |
| **Synthesized Patch Proposal** | ✅ | ✅ | ✅ |
| **Patch Application** | ❌ | ⚠️ (Human Sign-off) | ❌ |
| **Queue Enqueue** | ❌ | ⚠️ (Human Sign-off) | ❌ |

## Legend
- ✅: Fully Authorized.
- ⚠️: Permitted only with explicit, logged human sign-off.
- ❌: Explicitly Forbidden.

## Current v0.1.0 Status
The lane is locked to **ADVISORY** or **LIVE_SAFE** modes only. **AUTONOMOUS** mode is disabled by policy.
