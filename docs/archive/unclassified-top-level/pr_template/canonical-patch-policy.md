---
id: CANONICAL_PATCH_POLICY
title: Canonical Patch Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Canonical Patch Policy (explanation) for dopemux documentation and developer
  workflows.
---
# Canonical Patch Policy

## Overview
This policy governs how the `dopemux-pr-merge-specialist` applies surgical patches to the canonical repository PR template.

## Patching Principles
1. **Evidence-Oriented**: Patches must only be applied to resolve documented drift (e.g., missing safety sections).
2. **Non-Destructive**: Existing useful content (e.g., manual test instructions) must be preserved or migrated, never deleted blindly.
3. **Semantic Alignment**: Headings must be normalized to canonical forms (e.g., `Validation` -> `Verification`) to ensure reliable parsing.
4. **Hard Blocker Removal**: The primary goal of a canonical patch is to clear `DRIFTED` states by inserting missing required sections.

## Safety Constraints
- A patch must result in a content hash change only for the affected lines.
- Manual verification of the resulting `.github/pull_request_template.md` is mandatory after the first automated patch.
