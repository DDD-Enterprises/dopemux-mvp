# Evidence Ledger

Packet: `TP-DMX-MERGE-INTEGRITY-0001`

## Authority

- OBSERVED: `AGENTS.md`, `ARCHITECTURE.md`, `PROJECT.md`, `PM_PLANE.md`, and `SERVICE_CATALOG.md` were inspected from the dedicated worktree.
- OBSERVED: The attached packet is the execution-scope authority for this work.
- OBSERVED: Runtime/source truth and live GitHub state were used ahead of design inputs.

## Repository Identity

- OBSERVED: worktree path `/Users/hue/code/dopemux-merge-integrity-0001`.
- OBSERVED: branch `codex/tp-dmx-merge-integrity-0001-investigation-adr`.
- OBSERVED: base SHA `b176747b339685e781de04268c46b7ae123abfbf`.
- OBSERVED: primary checkout `/Users/hue/code/dopemux-mvp` was dirty before worktree creation and was not cleaned.
- OBSERVED: the new worktree rewrote `.claude/claude_config.json` with per-worktree MCP identity on status. The file was restored and marked skip-worktree locally in this dedicated worktree to prevent out-of-scope diff leakage.

## GitHub Evidence

- OBSERVED: GitHub auth succeeded.
- OBSERVED: repository settings captured in `raw/repository-settings.json`.
- OBSERVED: classic branch protection captured in `raw/main-protection.json`.
- OBSERVED: repository rulesets captured in `raw/rulesets.json` and `raw/ruleset-details.json`.
- OBSERVED: PR metadata, changed-file lists, local landed deltas, and file-count comparisons captured for #720, #734, #917, #932, #936, #1025, #1037, and #1038.
- OBSERVED: all GitHub reported changed-file counts matched paginated enumerated file counts.
- OBSERVED: GitHub patch retrieval for PR #1025 failed due the 20,000-line diff limit. Local git diffs are the authoritative evidence for #1025 mechanics.

## Source Evidence

- OBSERVED: `.github/workflows/ci-complete.yml` uses `--diff-filter=ACMR` for root-hygiene changed-file input.
- OBSERVED: `src/dopemux_pr_merge_specialist/validation.py` and the vendored skill copy use `--diff-filter=ACMR` for changed-file collection.
- OBSERVED: `.github/workflows/pr-steward.yml` runs PR Steward with `continue-on-error: true`, captures exit code, and exits `0`.
- OBSERVED: `.github/workflows/pr-steward.yml` invokes `scripts.audit.pr_audit_router --dry-run` before Steward.
- OBSERVED: `scripts/audit/pr_audit_router.py` emits `executed: false` and `embedded_audit.status: PASS` in dry-run proof.

## Canary Evidence

- OBSERVED: PR #1038 is open at head `283d6667933f2fd161992088731b7a6f8024f001`.
- OBSERVED: PR #1038 has four unresolved review threads and no review-thread pagination overflow.
- OBSERVED: PR Steward read-only strict run against #1038 exited `2`, readiness `BLOCKED`, and `mutation_performed: false`.

## Regression Evidence

- OBSERVED_OPEN_REGRESSION: PR #1037 review thread flags reserved-singleton port behavior in `src/dopemux/mcp/port_allocator.py`.
- OBSERVED: current code still blocks reserved-singleton allocation when the reserved port is occupied by an unknown process.
- OBSERVED: current unit test asserts the blocked behavior.
- OUT_OF_SCOPE: no runtime fix was performed.
