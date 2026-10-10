---
id: USAGE_PATTERNS
title: Usage Patterns
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Usage Patterns (explanation) for dopemux documentation and developer workflows.
---
# PR Merge Specialist: Usage Patterns

## When to Use
- **Diagnosis**: Analyzing why a PR is blocked or its current position in the Merge Queue.
- **Intake**: Normalizing and classifying feedback from threads, comments, and PR bodies.
- **Planning**: Generating a deterministic remediation plan for code, tests, and metadata.
- **Verification**: Running requested local checks (pytest, lint, etc.) and capturing evidence.
- **Enforcement**: Updating PR body checklists and sections based on actual outcomes.
- **Hygiene**: Cleaning up PR titles and descriptions to match conventional standards.
- **Communication**: Drafting evidence-backed replies to reviewers and resolving eligible threads.
- **Closure**: Transitioning a PR into the Merge Queue once all conditions are met.

## When NOT to Use
- **Architectural Design**: Do not use the skill to design new systems or major features from scratch.
- **Semantic Product Decisions**: Do not resolve disagreements on product direction or user experience.
- **Policy Bypass**: Do not use the skill to override CODEOWNERS or skip required CI gates.
- **Unverifiable Claims**: Never claim a fix is "tested" if the local verification engine did not run.
- **Unsafe Rewrites**: Do not rebase or rewrite shared history on protected branches.

## Preferred Operating Sequence
1. **Inspect**: `queue-scan` and `pr-fix --id <id>` (Dry-Run) to map the current state.
2. **Plan**: Analyze the generated `REMEDIATION_PLAN` and `VERIFICATION_EXECUTION_PLAN`.
3. **Execute**: Apply safe, policy-approved changes (code fixes, local tests, metadata cleanup).
4. **Recompute**: Run `pr-fix` again to verify that changes have moved the PR toward readiness.
5. **Finalize**: Enqueue the PR or escalate remaining manual blockers.
