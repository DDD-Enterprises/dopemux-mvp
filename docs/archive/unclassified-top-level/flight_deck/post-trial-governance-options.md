---
id: POST_TRIAL_GOVERNANCE_OPTIONS
title: Post Trial Governance Options
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Post Trial Governance Options (explanation) for dopemux documentation and
  developer workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Flight deck reference

## Flight Deck Post-Trial Governance Options

## Overview
Based on the evaluation of the unified flight deck (Tranche 22+), the system will adopt one of the following operational postures.

## Posture Definitions

### A. GO_SUPERVISED_ONLY
The flight deck is approved as the primary operator surface. All `MEDIUM` and `HIGH` risk patches remain human-gated.
- **Goal**: Maintain the current high-utility, high-safety balance.

### B. EXPAND_CAUTIOUSLY
The flight deck is approved, and the risk threshold for Auto-Apply may be broadened to include well-tested `MEDIUM` risk paths.
- **Goal**: Incrementally increase automation speed for trusted operators.

### C. RESTRICT_AND_HARDEN
The flight deck remains active, but specific features (like Live LLM Synthesis or Auto-Apply) are temporarily disabled.
- **Goal**: Address accuracy or safety failures before they impact production queues.

### D. NO_GO_REMAIN_SUPERVISED_MINIMAL
The rich UX and continuous loops are deprecated in favor of discrete, single-shot commands.
- **Goal**: Reduce system complexity if the interactive loops prove too fragile or confusing.

### E. ROLLBACK_SELECTED_SURFACES
Immediate disablement of the interactive wizard. Fall back to standard CLI arguments.
- **Goal**: Mitigate critical UI or State-Loop bugs preventing merges.
