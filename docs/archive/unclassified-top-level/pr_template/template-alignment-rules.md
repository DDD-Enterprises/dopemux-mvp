---
id: TEMPLATE_ALIGNMENT_RULES
title: Template Alignment Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Template Alignment Rules (explanation) for dopemux documentation and developer
  workflows.
---
# PR Template Alignment Rules

## Purpose
This document defines how `dopemux-pr-merge-specialist` evaluates, classifies, and safely updates repository pull request templates.

## Alignment States
- **ALIGNED**: All required sections are present and sufficiently populated.
- **PARTIALLY_ALIGNED**: Most required sections exist, but some are missing or weak.
- **PRESENT_BUT_WEAK**: Template is too sparse or placeholder-heavy.
- **DRIFTED**: Template has materially diverged from the canonical spine.
- **AMBIGUOUS**: Multiple templates make safe patching uncertain.
- **MISSING**: No detectable PR template exists.

## Canonical Required Spine
1. `Summary`
2. `Context`
3. `Verification`
4. `Risks`
5. `Rollback`
6. `Reviewer Notes`
7. `Checklist`
8. `High-Risk Integration Notes` (Conditional)

## Drift Scoring Model
- `90–100` → `ALIGNED`
- `70–89` → `PARTIALLY_ALIGNED`
- `50–69` → `PRESENT_BUT_WEAK`
- `1–49` → `DRIFTED`
- `no template found` → `MISSING`

## Hard Blockers
Regardless of score, force downgrade if:
- `Verification` missing.
- `Rollback` missing.
- `Risks` missing.
- Template is mostly placeholders.
- Checklist is absent.
