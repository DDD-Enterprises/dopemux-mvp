# DMX-DCP-MODEL-ROUTING-MVP-0000 — WORKFLOW_INVENTORY.md

## GitHub Workflows

| Workflow | Trigger | Permissions | Mutating? | Required? | Advisory? | Evidence | Risks |
|----------|---------|-------------|-----------|-----------|-----------|----------|-------|
| ci-complete.yml | push, PR | read + write (status) | Yes (status) | Yes (CI gate) | No | .github/workflows/ | Status mutation on failure |
| pr-steward.yml | PR events | read + write (PR) | Yes (PR labels/comments) | Yes (PR governance) | No | .github/workflows/ | PR mutation surface |
| gemini-*.yml (7 workflows) | schedule, dispatch, PR | read + write (PR) | Yes (PR review/comment) | Mixed | Mixed | .github/workflows/ | Gemini dispatch/plan/execute/review |
| security-*.yml | push, PR, schedule | read + write (security) | Yes (security alerts) | Yes (security gate) | No | .github/workflows/ | Security review/scan |
| embedded-audit.yml | push, PR | read | No | Yes (audit gate) | No | .github/workflows/ | Embedded audit execution |
| docs.yml | push to docs/ | read | No | No | Yes | .github/workflows/ | Docs build only |
| containers.yml | push, schedule | read + write (packages) | Yes (package publish) | No | Yes | .github/workflows/ | Container build/publish |
| preflight.yml | PR | read | No | Yes (preflight gate) | No | .github/workflows/ | Repo identity + preflight |
| repo-identity.yml | push | read | No | Yes (identity gate) | No | .github/workflows/ | Repo identity verification |

## Pre-commit Hooks

| Hook | Trigger | Permissions | Mutating? | Required? | Advisory? | Evidence | Risks |
|------|---------|-------------|-----------|-----------|-----------|----------|-------|
| ruff | pre-commit | read + write (format) | Yes (format) | Yes | No | .pre-commit-config.yaml | Auto-format mutation |
| mypy | pre-commit | read | No | Yes | No | .pre-commit-config.yaml | Type check only |
| markdownlint | pre-commit | read | No | Yes | No | .pre-commit-config.yaml | Lint only |
| filename-hygiene | pre-commit | read | No | Yes | No | .pre-commit-config.yaml | Audit only |
| pytest (unit) | pre-commit | read | No | Yes | No | .pre-commit-config.yaml | Test only |
| coverage gate | pre-commit | read | No | Yes | No | .pre-commit-config.yaml | Coverage check |

**Total Workflows**: 18
**Total Pre-commit Hooks**: 8+
**Mutating Workflows**: 6 (ci-complete status, pr-steward, gemini-*, security-*, containers, ruff format)
**Red Lane Risk**: pr-steward.yml + gemini-review.yml (currently modified in worktree)
