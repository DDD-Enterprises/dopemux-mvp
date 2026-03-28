# Changelog

All notable changes to the PR Merge Specialist will be documented in this file.

## [Unreleased]
### Added
- Queue-wide CI remediation via failure fingerprinting, `global-ci-fix` PR detection, and the `ci-remediation-specialist` runbook.
- Dashboard state distinctions for validation-pending, approval-required, and queued-for-merge PRs.
- Targeted unit coverage for dashboard console rendering and speculative train continuation behavior.
- Regression coverage for queue-wide required-check failures, prompt-only Gemini remediation, and bounded queue-drain execution.

### Changed
- The speculative train now rebases each candidate against `origin/main` instead of chaining later PRs onto earlier speculative branches.
- The flight dashboard passes its active `Console` into the renderer so viewport sizing reflects the live terminal instance.
- `flight-deck` now delegates to the authoritative `flight` dashboard path so autopilot, remediation, and merge execution share the same runtime.
- The docs workflow now runs on pull requests and `main` pushes only, preventing PR-branch push runs from re-failing on unrelated legacy docs debt.

### Fixed
- Validation-only PRs are no longer shown as queued-for-merge before local verification is complete.
- A single failed speculative rebase or push no longer aborts the rest of the train pass.
- Flight dashboard arrow-key navigation now accepts Kitty/application-cursor escape sequences instead of treating Down Arrow as an exit.
- Queue rescans now preserve prior executed local validation results for unchanged PR `head_sha`/`base_sha` pairs instead of resetting them to `not_executed`.
- Queue-drain now treats already queued or merged PRs as processed state instead of re-entering patch loops on later passes.
- Dashboard autopilot no longer treats monitor tactic `S` as queue navigation and no longer resets to the top PR after every reassessment.
- Queue planning no longer downgrades failing required GitHub checks to warnings after a local validation pass; those PRs remain `apply_blocked` until the remote required checks actually clear.
- `queue-drain --max-prs` now stops the execute loop at the requested bound instead of continuing through additional PRs in the same pass.
- Skill template parity is restored for the mirrored `cli.py`, `policy.py`, `runtime.py`, and `validation.py` modules so the full unit suite agrees with the runtime PR Merge specialist implementation.

## [0.1.0] - 2026-03-14
### Added
- **Tranche 1**: Core GraphQL Control Plane, Merge Queue support, and CI Triage.
- **Tranche 2**: Feedback Ingestion and Classification (Must-Fix, Optional, Question).
- **Tranche 3**: PR Body/Checklist Enforcement and Metadata Hygiene.
- **Tranche 4**: Review Reply Composer and Guarded Thread Resolution.
- **Tranche 5**: Multi-surface Instruction Pack (Codex, Claude, Copilot, Cursor, Vibe, Gemini, Jules).
- **PR Prep Specialist**: Automated branch preparation, audit, and drafting (packets 001-006).
- **Metrics**: Real-time rollups for throughput, duration, and cost proxies.
- **Orchestration**: Staged End-to-End Remediation workflow.
