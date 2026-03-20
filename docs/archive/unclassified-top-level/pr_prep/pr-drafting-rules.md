---
id: PR_DRAFTING_RULES
title: Pr Drafting Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Pr Drafting Rules (explanation) for dopemux documentation and developer workflows.
---
# PR Drafting Rules

## Core Philosophy
- **Evidence-Backed Only**: No statement in the PR body or checklist should exist without verifiable backing from branch state, adjacent work audits, or obligation detection.
- **No Fictional Verification**: Never claim a test was run or a feature was verified unless the artifacts explicitly confirm it.
- **Honest Incompleteness**: If a section (like Rollback) cannot be confidently determined, state "Requires maintainer review" instead of generating plausible-sounding filler.
- **Surface Blockers**: If obligations are missing or ambiguity is high, the draft must make these issues highly visible to reviewers.

## Template Constraints
The `pr-prep-specialist` uses a canonical PR template structure. Sections must not be removed, but they can be marked `NOT_APPLICABLE` or `REQUIRES_REVIEW` if evidence dictates.

## Posture Recommendations
The draft engine will emit a posture recommendation:
- `CREATE_READY`: All obligations met, low risk, high sufficiency.
- `DRAFT_RECOMMENDED`: High risk, missing minor context, or medium ambiguity.
- `BLOCKED_*`: Critical obligations missing, severe ambiguity, or malformed state.
