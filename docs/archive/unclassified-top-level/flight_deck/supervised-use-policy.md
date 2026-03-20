---
id: SUPERVISED_USE_POLICY
title: Supervised Use Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Supervised Use Policy (explanation) for dopemux documentation and developer
  workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Flight deck reference

## Flight Deck Supervised Use Policy

## Overview
This policy governs the interaction between human operators and the interactive flight deck in production environments.

## Operating Principles
1. **Pilot in Command**: The operator has final authority to accept, modify, or reject any recommendation.
2. **Audit Before Sync**: All synthesized code or metadata must be reviewed before synchronizing with GitHub.
3. **Explicit Sign-off**: Actions marked as HIGH or MEDIUM risk require a formal rationale entry.
4. **Verification Requirement**: Local verification (`pytest`, `lint`) must pass before a thread is resolved.

## Approved Operational Actions
- **Metadata Patching**: Injecting missing canonical sections (`P`).
- **Code Implementation**: Applying synthesized surgical patches (`I`).
- **Thread Sync**: Posting replies and resolving conversations (`T`).
- **Verification**: Running the local validation suite (`V`).

## Forbidden Actions
- Lowering risk thresholds without a formal evaluation packet.
- Bypassing the verification step for `MUST_FIX_CODE` items.
- Silent autonomous merging of high-risk integrations.
