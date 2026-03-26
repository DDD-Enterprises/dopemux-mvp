# Changelog

All notable changes to the PR Merge Specialist will be documented in this file.

## [Unreleased]
### Added
- Restored the PR Merge Specialist runtime, tests, docs, and skill template from branch history into the active codebase.
- Reintroduced the top-level `dopemux pr-merge ...` operator entrypoint while retaining `dopemux-pr-merge ...` as the package entrypoint.
- Added active how-to and explanation docs for the recovered cockpit:
  - `docs/02-how-to/pr-merge-flight-dashboard.md`
  - `docs/04-explanation/pr-merge-queue-orchestration.md`

### Changed
- Updated canonical documentation indexes and overviews to include the recovered PR merge cockpit docs and `templates/skills/pr-merge-specialist/`.
- Extended `scripts/skills/sync_repo_skills.py` to install the PR Merge Specialist skill family alongside the existing documentation skill families.

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
