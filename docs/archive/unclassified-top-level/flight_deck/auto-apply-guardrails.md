---
id: AUTO_APPLY_GUARDRAILS
title: Auto Apply Guardrails
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Auto Apply Guardrails (explanation) for dopemux documentation and developer
  workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Flight deck reference

## Auto-Apply Guardrails

## Overview
This document codifies the governance constraints for automated actions within the flight deck.

## Fixed Thresholds (v0.1.0)
The following thresholds are locked and cannot be modified by the LLM or operator during a session:
- **Max Complexity**: `LOW`
- **Max Risk**: `LOW`
- **Min Confidence**: `HIGH`

## Guardrail Rules
1. **No Destructive Overwrite**: Auto-apply is forbidden if the search block cannot be uniquely identified in the file.
2. **Mandatory verification**: If an auto-apply occurs, the `[V]erify` step must be performed before `[T]hreads` sync.
3. **Incident Escalation**: Any failed auto-apply (e.g. file error) must result in an `INCIDENT` log and immediate session pause.

## Expansion Path
Broadening these thresholds requires a new `TP-PRMS` packet and validated evaluation data from 50+ runs.
