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
# Flight Deck Allowed Actions Matrix

## Purpose
This matrix defines the boundaries of automation for the flight deck tactical controls.

## Authorization Matrix

| Action | Mode: ADVISORY | Mode: LIVE_SAFE | Mode: SUPERVISED |
| :--- | :---: | :---: | :---: |
| **Mission Intelligence** | ✅ | ✅ | ✅ |
| **Remediation Sequencing** | ✅ | ✅ | ✅ |
| **Gating Refresh** | ✅ | ✅ | ✅ |
| **Low-Risk Auto-Apply** | ❌ | ✅ | ✅ |
| **Metadata Patching** | ❌ | ⚠️ Sign-off | ✅ |
| **Code Implementation** | ❌ | ❌ | ⚠️ Sign-off |
| **Thread Sync/Resolve** | ❌ | ❌ | ✅ |

## Legend
- ✅: Fully Authorized.
- ⚠️: Permitted only with explicit human sign-off.
- ❌: Explicitly Forbidden.

## Current v0.1.0 Status
The flight deck is locked to **SUPERVISED** mode. **AUTONOMOUS** operation is disabled.
