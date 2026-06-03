# Changelog

All notable changes to Dopemux (including the PR Merge Specialist) will be documented in this file.

## [Unreleased]
### Added
- Autoreview platform integration stack: task packets, PAL clink audit verdict capture, read-only PR Action Bridge CLI, Copilot repair packet rendering, embedded-audit provenance workflow, offline autoreview loop fixtures, PR steward merge gates, PR steward CLI/package/scaffold/doctor flows, and final ops hardening docs.
- Restored task-orchestrator Claude-surface infrastructure (17 `/dx:` slash commands, `.taskorchestrator/config.yaml` schema, ADR, reference docs, and external MCP wrapper snapshots) that was removed by the stale-branch merge in PR #720. Unblocks PR #724 (TP-CS-101 plugin hooks). Added `.taskorchestrator` to the root-hygiene allowlist.
- Consolidated V5 extraction engine and validation toolchain (PR #313).
- Run ID propagation across `queue-drain` and `flight` to ensure consistent artifact grouping.
- Persistent `RUN_SUMMARY.md` writing at the end of `queue-drain` execution.
- Git case-insensitivity warning in `preflight` for macOS environments.
- Production certification audit artifacts and a machine-readable certification status for the repo-truth extractor and Dopemux operator surfaces.
- A provider-override step in the extraction wizard for session-local API key overrides per supported model provider.
- Orchestrator plugin hooks (Path B, TP-CS-101): `SubagentStart` agent-owned-phase protocol injection, actor-attribution and skill-invocation enforcement, and plan-mode (Enter/ExitPlanMode) guidance — ported from the upstream `task-orchestrator` Claude plugin into the native Python hook dispatcher (`native_hooks.py`); all fail-open and dormant without `.taskorchestrator/config.yaml` (PR #724).

### Changed
- Pull request CI now treats the full Repo Truth Extractor suite and auditor-router tests as blocking gates, with both jobs included in the aggregate CI summary.
- `stage_and_push_if_needed` now uses `git add -A` to detect case-only renames on macOS.
- `pr_merge_loop.sh` updated with progress-based exit logic to prevent infinite retries on stuck PRs.
- The speculative train now rebases each candidate against `origin/main` instead of chaining later PRs onto earlier speculative branches.
- The flight dashboard passes its active `Console` into the renderer so viewport sizing reflects the live terminal instance.
- `flight-deck` now delegates to the authoritative `flight` dashboard path so autopilot, remediation, and merge execution share the same runtime.
- The docs workflow now runs on pull requests and `main` pushes only, preventing PR-branch push runs from re-failing on unrelated legacy docs debt.
- Active extractor docs now describe the validated bounded v5 lane, the current reliability contract, and the upgrade-design reality check for this branch.
- `dopemux truth`, `dopemux upgrades trace`, and `dopemux extractor trace` now delegate to the canonical v5 runtime contract instead of legacy `PipelineRunner` behavior.
- Interactive wizard surfaces now load `questionary` through a deterministic dependency gate, and the production theme defaults to `mint-mojo`.
- The extraction wizard now lets operators browse cost profiles with inline behavior details before selecting a run profile.
- The extraction wizard now delegates execution through the v5 upgrades wrapper and defaults first-run posture to routing policy `cost` with `workers=1`.
- The dashboard and detail views now resolve service endpoints from repo environment authority instead of assuming fixed localhost ports.
- CI now includes wrapper-authority coverage, interactive import smoke, and the production `brand_lint.py` gate.

### Fixed
- Reconciled autoreview integration contracts across PR Steward schemas/runtime, Action Bridge fallback action categories, resolved-thread review-comment handling, proof self-reference freshness states, and PR Steward package entrypoint metadata.
- Hardened autoreview integration review fixes: embedded-audit CI now captures PAL clink output before proof emission, PR Steward console installs include steward/action-bridge engines, scaffolded downstream workflows install Dopemux before invocation, and steward gates require explicit artifact paths instead of implicit queue-run fallbacks.
- Tightened follow-up autoreview review fixes: PR Steward recomputes proof freshness from the current PR head, manual embedded-audit dispatch checks out the requested head SHA, and packaged installs include the Copilot repair engine.
- Aligned PR Steward scaffold merge policy with explicit steward artifact paths and preserved local thread-resolution evidence in the final queue-drain apply state.
- Closed latest autoreview review gaps by packaging existing Dopemux namespaces, loading PR Steward doctor defaults from packaged resources, and allowing validated proof self-reference exceptions through the steward finalization gate.
- Wired scaffolded PR Steward intake to pass the configured proof bundle path so initialized downstream repositories do not emit missing-proof readiness blockers by default.
- Added verified base-to-head diff context to the embedded-audit PAL prompt so independent audit proof is based on visible PR changes.
- Fixed the packaged PR Steward intake wrapper so documented `--repo`, `--pr`, `--out`, proof, and format options are parsed and forwarded to the intake runtime.
- Hardened PR Steward proof self-reference exceptions against spoofed proof-reported file lists by validating them against the actual harvested PR files.
- Decisions CLI review repair now uses the ConPort HTTP REST port, accepts string decision IDs, validates referenced decisions before append-only writes, preserves requested list limits, and covers the new subcommands with focused tests.
- MCP doctor now runs relative stdio doctor commands from the resolved repo root, so Task Orchestrator wrapper checks work when invoked from repo subdirectories.
- MCP bootstrap now points Task Orchestrator at a tracked launcher wrapper and keeps catalog-rendered SSE URL defaults aligned with checked-in `.mcp.json`.
- Installer review cleanup now removes dead SQLite test isolation code and makes setup-time `dopemux-network` creation fail closed on unexpected Docker errors.
- Dependabot uv security-update resolution now has bounded Python support metadata and a patched MCP service floor compatible with current Semgrep/LiteLLM resolution.
- Repo Truth Extractor full-suite CI now avoids platform-sensitive strict XPASS failures by scoping known prescan xfails to macOS and stabilizing the v4 help assertion environment.
- Task sequencer predictive action labels now use the same complete and skip transition rules as the buttons they describe.
- Repo-truth extractor prescan now excludes generated artifact, proof, audit, operator-local, and known secret-bearing paths from default corpus input, while allowlisting committed `.env.example` / `.env.template` / `.env.sample` placeholders so they remain in the corpus as text. Wired through `run_integrated_prescan_stage` so the v5 integrated path uses the same defaults.
- Claude security review automation now resolves the repository-specific scan and false-positive instruction files referenced by `security-review.yml` and `ci-complete.yml`, preventing missing-path failures during AI security analysis.
- Restored `compose.yml` as the canonical hand-authored Docker Compose file, removed the stale root unified compose variant, and hardened compose guard checks against future root-level compose drift.
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
- `dopemux extract truth-run --resume` no longer injects a fresh run ID when resume is implicit, so v5 latest-run semantics are preserved.
- Wizard extraction no longer silently forces `--skip-hygiene`, and rich validation output now shows the full blocker set plus next actions.
- `scripts/brand_lint.py` is runnable again on this checkout after repairing the `activity-capture` syntax failure and tightening the production authority checks.

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
