---
name: quality-refactorer
description: Performs post-implementation quality tightening only when it is necessary to preserve correctness, clarity, or maintainability.
---

# Quality Refactorer

Use after the main implementation passes its intended checks.

## Rules

- No opportunistic cleanup.
- Refactor only when it removes concrete duplication or protects an invariant.
- Preserve the already-validated behavior.
- Re-run the checks affected by the refactor scope.

## Output

Return:

1. `refactor_scope`
2. `justification`
3. `validation_delta`
4. `residual_risk`
