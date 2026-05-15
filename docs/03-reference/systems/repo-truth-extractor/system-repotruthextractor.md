---
id: SYSTEM_RepoTruthExtractor
title: System Repotruthextractor
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: System Repotruthextractor (reference) for dopemux documentation and developer
  workflows.
---
# SYSTEM_RepoTruthExtractor

## 1. Purpose

Repo Truth Extractor is the repository's canonical repo-truth extraction runtime family. In the inspected code, the primary execution authority is `services/repo-truth-extractor/run_extraction_v5.py`, with `run_extraction_v4.py` acting as a compatibility wrapper that preserves v4 prompt/artifact contracts while delegating supported execution to v5.

Its canonical authority slice is narrow:
- multi-phase extraction execution and run orchestration
- promptset/preflight/doctor/coverage/status tooling implemented by the extractor runners
- deterministic run artifact and proof generation for extraction runs

It is not the operator CLI control plane, not PM authority, not memory authority, and not a source-of-truth replacement for the repository code it analyzes. It is the extraction/audit runtime for producing repo-truth artifacts about the repo.

## 2. Core Responsibilities

- Runs the active extraction engine.
  Evidence: `services/repo-truth-extractor/run_extraction_v5.py` is the large multi-phase runner with deterministic inventory, partitioning, raw outputs, normalized merge, QA, doctor, preflight, coverage, status, and verification surfaces.

- Provides the active phase/run CLI for repo-truth extraction.
  Evidence: `run_extraction_v5.py` parses `--phase`, `--run-id`, `--doctor`, `--doctor-auth`, `--preflight-providers`, `--coverage-report`, `--status`, `--status-json`, `--verify-phase-output`, `--print-run-order`, `--print-phase-routing`, `--print-phase-prompts`, promptgen flags, comparison-lane flags, resume/batch flags, and related execution controls.

- Writes and manages v5 extraction artifacts and proofs.
  Evidence: `run_extraction_v5.py` defines `V5_EXTRACTION_ROOT = extraction/repo-truth-extractor/v5`, `V5_RUNS_ROOT`, `V5_DOCTOR_ROOT`, `V5_LATEST_RUN_FILE`, and proof/report filenames such as `PROOF_PACK.json`, `COVERAGE_ROLLUP.json`, `RUN_DASHBOARD.json`, `STEP_METRICS.json`, and `FAILURE_INDEX.json`.

- Performs extraction doctor/preflight/auth checks.
  Evidence: `run_extraction_v5.py` implements `run_doctor_checks`, `run_provider_doctor_probe`, `run_provider_preflight`, `run_doctor_full`, and `run_auth_doctor`, with explicit doctor/preflight CLI flags and doctor output writes under the v5 doctor root.

- Performs extraction coverage/status/verification reporting.
  Evidence: `run_extraction_v5.py` implements coverage rollup/report generation, `run_status_loop(...)`, log tailing, provider-usage reporting, and `verify_phase_output(...)`.

- Enforces promptset gating and fail-closed execution blocks.
  Evidence: `run_extraction_v5.py` writes run manifests, evaluates promptset reports, and applies `apply_promptset_preflight_block(...)` before execution when the promptset is blocked.

- Preserves v4 compatibility by wrapping v5 execution and rebuilding v4 outputs.
  Evidence: `services/repo-truth-extractor/run_extraction_v4.py` states it "keeps v5 execution intact" while loading v4 prompt/artifact manifests, executing v5 for supported phases, and rebuilding deterministic v4 normalized outputs under `extraction/repo-truth-extractor/v4/runs/<run_id>/`.

- Exposes repo-truth-extractor entrypoints through dopemux command wiring, with `dopemux rte` as the canonical operator command family.
  Evidence: `src/dopemux/cli.py` registers the `rte` group as the "Canonical operator entrypoint for Repo Truth Extractor", attaches `run`, `list`, `doctor`, `status`, `preflight`, `validate-live`, `trace`, `wizard`, and `promptset` subcommands to it, labels `dopemux upgrades` as a legacy compatibility alias, hides/blocks `dopemux extractor` through `LegacyReplacementCommand`, and makes `dopemux truth` raise a refusal pointing to `dopemux rte`.

## 3. Non-Responsibilities

- Repo Truth Extractor does not own repository runtime truth.
  Evidence: it analyzes repository code and emits artifacts about it; it does not replace runtime code, configs, tests, or canonical domain services.

- Repo Truth Extractor does not own operator CLI control.
  Evidence: `docs/03-reference/systems/dopemux/system-dopemux.md` identifies `dopemux` as the operator-facing control layer. `src/dopemux/commands/extractor_commands.py` delegates to extractor runners or blocks direct execution, rather than making Repo Truth Extractor the CLI control plane itself.

- Repo Truth Extractor does not own PM, memory, or retrieval authority.
  Evidence: PM, memory, and retrieval authorities are assigned in their respective system/plane docs. The extractor only emits analysis artifacts about those systems.

- Repo Truth Extractor does not make extracted artifacts equal to live system truth.
  Evidence: `docs/03-reference/governance/rules-2.md` puts runtime code/config/tests above truth artifacts in the truth hierarchy.

## 4. Key Surfaces

- Canonical runtime entrypoint:
  `services/repo-truth-extractor/run_extraction_v5.py`

- Compatibility runtime:
  `services/repo-truth-extractor/run_extraction_v4.py`

- Legacy/fallback runtime:
  `services/repo-truth-extractor/run_extraction_v3.py`

- Adjacent helper surfaces:
  - hygiene: `services/repo-truth-extractor/extraction_hygiene.py`
  - validation: `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
  - promptsets/contracts/libs: `services/repo-truth-extractor/promptsets/`, `services/repo-truth-extractor/lib/`
  - tests: `services/repo-truth-extractor/tests/`

- CLI and invocation surfaces:
  - canonical operator command family in `src/dopemux/cli.py`: `dopemux rte ...`
  - safe operator commands: `dopemux rte run`, `dopemux rte list`, `dopemux rte preflight`, `dopemux rte status`, `dopemux rte doctor`, `dopemux rte validate-live`, `dopemux rte promptset ...`, and `dopemux rte trace`
  - legacy compatibility alias: `dopemux upgrades ...`
  - deprecated/refusal surface: `dopemux extractor ...`
  - legacy/refusal drift: `dopemux truth`
  - gated legacy scan: `dopemux rte scan --allow-legacy-v3-scan`, which delegates to `run_repscan.py` and the legacy v3 chain
  - advanced/debug direct runner invocation: `python services/repo-truth-extractor/run_extraction_v5.py ...`

- Artifact/proof surfaces:
  - v5 root/constants in `run_extraction_v5.py`: `extraction/repo-truth-extractor/v5`
  - v4 root/constants in `run_extraction_v4.py`: `extraction/repo-truth-extractor/v4`
  - run/proof/report filenames defined in `run_extraction_v5.py`

## 5. System Boundaries

- dopemux
  dopemux exposes extractor-related command wiring and runner path resolution.
  Repo Truth Extractor receives invocation from dopemux commands or direct Python execution.
  Repo Truth Extractor does not control dopemux CLI policy or the overall operator control plane.

- repository code/config/tests
  Repo Truth Extractor reads and analyzes repo surfaces as inputs.
  It emits extraction artifacts, proofs, and reports.
  It does not control or replace the canonical authority of the repo surfaces it scans.

- promptsets and validation tooling
  Repo Truth Extractor consumes generated promptsets, v4 prompt/artifact manifests, and validation gates.
  It emits promptset audit/gate results and blocked-run manifests where needed.
  It does not make generated promptsets canonical repo truth by itself.

- output trees
  Repo Truth Extractor writes run, doctor, proof, and coverage artifacts under extraction trees.
  Those are evidence artifacts and operational outputs, not the upstream systems being described.

## 6. Authority Model

- Canonical
  - `services/repo-truth-extractor/run_extraction_v5.py` for active execution authority
  - extractor execution flow, doctor/preflight/coverage/status/verification logic in the v5 runner
  - deterministic artifact/proof generation behavior implemented by the runner family

- Derived
  - run artifacts, coverage rollups, proof packs, dashboards, and status reports produced by runs
  - v4 normalized outputs rebuilt by `run_extraction_v4.py`

- Operational
  - canonical CLI invocation through `dopemux rte ...`
  - legacy compatibility CLI invocation through `dopemux upgrades ...`
  - advanced/debug direct Python runner execution
  - hygiene scanning/quarantine tools in `extraction_hygiene.py`
  - validator and doctor helper tooling

- Unknown
  - whether all older docs and commands consistently reflect the active v5 runtime without drift
  - whether every legacy `dopemux truth`/older extractor shortcut has been fully retired from operator practice

Rule: Repo Truth Extractor is authoritative for extraction execution and extraction artifacts, not for the live domain truth it analyzes.

## 7. Known Drift / Issues

- Active engine vs artifact-tree messaging is inconsistent.
  Evidence: `run_extraction_v5.py` defines `V5_EXTRACTION_ROOT = extraction/repo-truth-extractor/v5`, while `services/repo-truth-extractor/README.md` also says the v5 runner is the active execution engine but "still writes run artifacts, doctor outputs, and telemetry under the `v3` extraction tree," and later separately lists v5 runtime artifacts/proofs. This is documented drift and should not be flattened into a single settled output-root claim without runtime confirmation.

- Legacy command surfaces remain present but are explicitly deprecated, hidden, gated, or blocked.
  Evidence: `src/dopemux/cli.py` labels `dopemux upgrades` as a legacy compatibility alias for `dopemux rte`, blocks `dopemux extractor` through `LegacyReplacementCommand`, makes `dopemux truth` raise a refusal, and gates `dopemux rte scan` with `--allow-legacy-v3-scan` before it delegates to `run_repscan.py`.

- Version layering is real and should not be collapsed.
  Evidence: `run_extraction_v4.py` is not a separate clean-room engine; it preserves v4 contracts while executing through v5 for supported phases. `run_extraction_v3.py` still exists as a compatibility/fallback path.

- The system has a wide tooling surface beyond the single runner.
  Evidence: the service tree includes hygiene tools, validation gates, promptgen, comparison lane support, `fl_int`, `s_int`, and many tests. Treating the system as only `run_extraction_v5.py` can hide operational dependencies, but treating every helper as equal runtime authority would also overstate them.

## 8. Working Rules

- Treat `services/repo-truth-extractor/run_extraction_v5.py` as the strongest execution authority.

- Keep engine authority, compatibility wrappers, and emitted artifacts separate.
  v5 executes.
  v4 wraps/contracts.
  output trees are evidence artifacts.

- Do not treat extractor outputs as stronger than runtime code, config, and tests.

- Prefer `dopemux rte ...` for operator workflows. Treat `dopemux upgrades ...` as a legacy compatibility alias, direct runner invocation as advanced/debug/manual, `dopemux rte scan` as a gated legacy v3 scan route, and `dopemux extractor` / `dopemux truth` as deprecated or refusal surfaces.

- Preserve the documented output-root/version drift explicitly until runtime verification settles it.

- Preserve `UNKNOWN` where older command surfaces and docs may still lag the active runner behavior.
