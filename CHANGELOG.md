# Changelog

All notable changes to Dopemux (including the PR Merge Specialist) will be documented in this file.

## [Unreleased]
### Added
- Consolidated V5 extraction engine and validation toolchain (PR #313).
- Run ID propagation across `queue-drain` and `flight` to ensure consistent artifact grouping.
- Persistent `RUN_SUMMARY.md` writing at the end of `queue-drain` execution.
- Git case-insensitivity warning in `preflight` for macOS environments.
- Phase S prompt rendering for SP placeholders in the v5 runner, with stub rules config scaffolding.
- Promptset audit now supports `--population` for Phase S, S_INT, FL_INT, prescan, and all.

### Changed
- `stage_and_push_if_needed` now uses `git add -A` to detect case-only renames on macOS.
- `pr_merge_loop.sh` updated with progress-based exit logic to prevent infinite retries on stuck PRs.
- The speculative train now rebases each candidate against `origin/main` instead of chaining later PRs onto earlier speculative branches.
- The flight dashboard passes its active `Console` into the renderer so viewport sizing reflects the live terminal instance.
- `flight-deck` now delegates to the authoritative `flight` dashboard path so autopilot, remediation, and merge execution share the same runtime.
- The docs workflow now runs on pull requests and `main` pushes only, preventing PR-branch push runs from re-failing on unrelated legacy docs debt.
- Active extractor docs now describe the validated bounded v5 lane, the current reliability contract, and the upgrade-design reality check for this branch.
- S_INT and FL_INT prompt files now use the `PROMPT_` filename prefix and registries reference the renamed files.

### Fixed
- Validation-only PRs are no longer shown as queued-for-merge before local verification is complete.
- A single failed speculative rebase or push no longer aborts the rest of the train pass.
- Flight dashboard arrow-key navigation now accepts Kitty/application-cursor escape sequences instead of treating Down Arrow as an exit.
- Queue rescans now preserve prior executed local validation results for unchanged PR `head_sha`/`base_sha` pairs instead of resetting them to `not_executed`.
- Queue-drain now treats already queued or merged PRs as processed state instead of re-entering patch loops on later passes.
- Dashboard autopilot no longer treats monitor tactic `S` as queue navigation and no longer resets to the top PR after every reassessment.
- Queue planning no longer downgrades failing required GitHub checks to warnings after a local validation pass; those PRs remain `apply_blocked` until the remote required checks actually clear.
- `queue-drain --max-prs` now stops the execute loop at the requested bound instead of continuing through additional PRs in the same pass.
- Docs template assets now use `template-*` filenames so the `docs-prohibited-patterns` hook no longer blocks active PRs on legacy template path names.
- Repo-truth extractor docs now reflect `config/pricing.yaml` as cost authority, explicit output sanitization at the JSON sink, redacted auth-missing logging, and non-silent coverage parse warnings.

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
