# Changelog

All notable changes to Dopemux will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-13

### Added
- Initial public alpha release
- Universal installer script with platform detection
- Support for macOS (Apple Silicon & Intel), Ubuntu 22.04+, Arch Linux, Fedora
- Fast test suite for CI/CD (`test_installer_basic.sh`)
- Homebrew formula for macOS installation
- PyPI package distribution (wheel + source)
- ADHD-optimized CLI with 40+ commands
- Multi-instance workspace support
- Claude Code integration
- MCP server management
- Document processing pipeline
- Profile management system
- Mobile workflow support
- Docker service orchestration

### Fixed
- Python version requirement (3.11 → 3.10) for Ubuntu 22.04 LTS compatibility
- IndentationError in cli.py (misplaced imports)
- Missing litellm dependency in package dependencies

### Changed
- Installer now requires Python 3.10+ (down from 3.11+)
- Updated help text to reflect Python 3.10+ requirement

### Documentation
- Comprehensive installer testing report
- PyPI release guide
- Platform-specific testing documentation
- Quick reference guides
- Session summaries (Days 1-3)

### Testing
- Validated on macOS (100% pass rate)
- Partial Ubuntu 22.04 container testing (60% pass rate)
- Clean virtualenv installation verified
- Twine PyPI compliance validation passed
- CLI functionality verified

### Package Details
- Package Size: 565 KB (wheel), 575 KB (source)
- Dependencies: 86 packages
- Python Support: >= 3.8 (tested on 3.10, 3.13)
- Entry Point: `dopemux` CLI command

### Known Limitations
- Docker-in-Docker testing not supported in containers
- Full functionality requires Docker daemon running
- Some features require system-level dependencies

## [Unreleased]

### Added
<<<<<<< HEAD
=======
<<<<<<< HEAD
- Pending items for the next patch release.
=======
>>>>>>> cf344f45c (review-response: address thread suggestions (pr-merge/20260311_210757/PR-205))
- PM-plane authority ADR set:
  - ConPort as decision/progress/context authority
  - Dopecon-bridge narrowed to adapter-only scope
  - Leantime JSON-RPC + plugin integration strategy
  - PM-plane authority boundaries
- Task-orchestrator and Leantime follow-up ticket queue in PM docs.
- PR docgen sync skill family templates:
  - `templates/skills/pr-docgen-sync/`
  - `templates/skills/pr-docgen-sync-gemini/`
  - `templates/skills/pr-docgen-sync-copilot/`
  - `templates/skills/pr-docgen-sync-claude/`
<<<<<<< HEAD
=======
- PR merge specialist skill template:
  - `templates/skills/pr-merge-specialist/`
>>>>>>> cf344f45c (review-response: address thread suggestions (pr-merge/20260311_210757/PR-205))
- Repo skill installer for template families: `scripts/skills/sync_repo_skills.py`.

### Changed
- Canonicalized runtime orchestration on root `compose.yml`; smoke flows now run through `scripts/smoke_up.sh` and `scripts/smoke_down.sh`.
- Updated smoke/runtime tooling (`tools/smoke_runtime_gate.py`, `tools/ports_health_audit.py`, `tools/generate_smoke_env.py`) to use canonical compose semantics.
- Updated deploy/start scripts to target compose project `dopemux` consistently.
- Parameterized additional host port bindings in `compose.yml` (`POSTGRES_PORT`, `QDRANT_PORT`, `QDRANT_GRPC_PORT`, `TASK_ORCHESTRATOR_PORT`, `DOPE_MEMORY_PORT`).
<<<<<<< HEAD
=======
- Expanded `pr-merge-specialist` into a rebase-first queue drain with hybrid ordering, multi-pass retries, pending-check waits, proof artifacts, and review-thread handling.
>>>>>>> cf344f45c (review-response: address thread suggestions (pr-merge/20260311_210757/PR-205))

### Fixed
- Added rogue task-orchestrator container cleanup in `scripts/start.sh` to prevent non-canonical compose projects from auto-restart conflicts.
- Corrected registry-to-compose mapping for Qdrant (`compose_service_name: mcp-qdrant`).
- Hardened ADHD Engine startup for local/test environments:
  - optional degraded startup mode (`ADHD_ENGINE_ALLOW_DEGRADED_STARTUP`)
  - optional in-memory cache forcing (`ADHD_FORCE_INMEMORY_CACHE`)
  - graceful fallback when optional deps (`prometheus_client`, `fastmcp`) are unavailable.
- Stabilized integration/security/unit tests for compose canonicalization and ADHD runtime behavior.
<<<<<<< HEAD
=======
- Improved PR queue automation by reproducing local rebase conflicts for deep conflict packets and auto-applying explicit conflict-marker review suggestions.
>>>>>>> cf344f45c (review-response: address thread suggestions (pr-merge/20260311_210757/PR-205))

### Documentation
- Updated install/deployment/reference docs to remove legacy compose-file guidance and document canonical `compose.yml` usage.
- Updated architecture, server registry, and instruction docs to reflect task-orchestrator canonical port `8000`.
- Added canonical docs index/list reconciliation surfaces (`docs/INDEX.md`, section overviews, documentation catalog).
- Added PR docgen workflow guidance across Codex/Claude/Gemini/Copilot instruction surfaces.
<<<<<<< HEAD
=======
>>>>>>> 776ae3a99 (feat(pr-merge-specialist): add rebase-first queue drain)
>>>>>>> cf344f45c (review-response: address thread suggestions (pr-merge/20260311_210757/PR-205))

## [0.6.0] - Target: 2026-04-09

### Release Phase E - Quality, Test Coverage, and Reliability
#### Added
- Expanded integration and unit coverage across EventBus, TaskDecomposer, core logging, retry policy, and global error handling paths.
- Reliability scaffolding for extractor phase routing, retries, and ProcessPool stabilization.
- Memory capture CLI commands (`dopemux memory rollup`):
  - `build` to build a global rollup index from project ledgers.
  - `list` to list registered projects in the global index.
  - `search` to search promoted work log entries across projects.

#### Documentation
- Comprehensive MCP troubleshooting guide and related operator runbooks.
- Repo Truth Extractor operator docs (user guide + batch quickstart + runbook cross-links).
- Derived Memory Pipeline CLI interface documentation and dopeTask upgrade notes across migration and supervisor docs.

## [0.5.0] - Target: 2026-04-02

### Release Phase D - Security and Safety Hardening (2026-03-02 onward)
#### Added
- Stronger safety mandates and audit instrumentation in extraction workflows (including TP-008 tooling and repair lanes).

#### Fixed
- Removed hardcoded database credentials from ConPort memory defaults and enforced environment-driven DB configuration.
- Closed CLI wiring regression for autoresponder config command placement.
- Corrected strict route handling in `run_extraction_v3` and restored missing promptset model-map source.

## [0.4.0] - Target: 2026-03-26

### Release Phase C - Dashboard UX and Accessibility (2026-02-23 to 2026-03-03)
#### Added
- Task selection and detail drill-down in Dopemux dashboard, replacing hardcoded task targeting.
- Accessibility improvements across Team Dashboard and task UI components, including better labels, tooltip context, and keyboard support.
- Improved status visibility and micro-UX polish for live indicators and shorthand metrics.

#### Fixed
- Dashboard endpoint and integration issues that blocked consistent task data display.
- Accessibility test gaps to ensure regressions are caught in CI.

## [0.3.0] - Target: 2026-03-19

### Release Phase B - Platform Hardening and MCP Reliability (2026-02-23 to 2026-02-26)
#### Added
- MCP stack hardening with auto-provisioning, multi-instance isolation, and real tool-server wiring.
- Mobile-first tmux integration and connectivity stabilization improvements.
- Infrastructure consolidation and migration cleanup across task tooling and compose setup.

#### Fixed
- Serena Docker path mapping mismatches affecting project discovery inside containers.
- ConPort wiring and stdio integration mismatches across compose and tool wrappers.
- Root hygiene and pre-commit guardrails updated to reflect intentional repository structure.

## [0.2.0] - Target: 2026-03-12

### Release Phase A - Extractor and Routing Cutover (2026-02-20 to 2026-02-22)
#### Added
- Repo Truth Extractor cutover with hardened Phase S synthesis flows, async webhook batch handling, and richer extraction observability.
- Canonical v4 upgrades CLI namespace with improved batch UX and prompt routing proof flows.
- Deterministic routing and manual pro prompt controls for more predictable provider behavior.
- Cloudflare tunnel + webhook receiver Option B flow for resilient external event ingestion.
- Global routing configuration template and `RoutingConfig` support.

#### Fixed
- Repo Truth Extractor OpenAI routing now uses `gpt-5.2` and `gpt-5.2-pro` model IDs.
- OpenAI GPT-5 requests no longer send unsupported temperature values.
- Webhook storage migration and compose service-path mismatches were corrected.
- MCP server wrappers now handle container naming variance more reliably.

---

[0.1.0]: https://github.com/dopemux/dopemux-mvp/releases/tag/v0.1.0
