---
id: RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001
title: RTE UX CLI Tone Emoji Cleanup Audit Note
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-18'
last_review: '2026-05-18'
next_review: '2026-08-16'
prelude: Audit note for voice containment on RTE/operator CLI copy.
---
# RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001 Audit

## What Changed

- Tightened `src/dopemux/cli.py` copy for RTE/operator command surfaces where
  tone could obscure command replacement, safety/refusal, live/provider,
  preflight, or promptset-audit guidance.
- Changed only help text, command docstrings, and refusal/error message text.
- Updated exact expected text in `tests/unit/test_cli_upgrades_commands.py` for
  the `dopemux truth` refusal.
- Created the task packet, this audit note, and proof JSON.

## What Did Not Change

- No command names, arguments, Click option semantics, subprocess calls, runner
  dispatch, exception classes, return paths, exit codes, validation logic, or
  live-gate semantics changed.
- No provider behavior changed.
- No routing or pricing behavior changed.
- No promptsets or schemas changed.
- No services changed.
- No pre-live validator error shape changed.
- No `DPMX_LIVE_OK` behavior changed.
- No progressive-disclosure work was started.
- No docs or brand-voice guidance files were edited.
- No provider calls, live extraction, live preflight, network/provider
  validation, or account-specific checks were run.

## Authority Read

- `AGENTS.md`
- `.claude/PROJECT_INSTRUCTIONS.md`
- `.claude/brand-voice-guidelines.md`
- `docs/03-reference/governance/rules.md`
- `docs/03-reference/truth/truth-canonicals.md`
- `docs/03-reference/truth/truth-scope.md`
- `docs/03-reference/systems/system-boundaries.md`
- `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md`
- `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_MANIFEST.json`
- `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_PACKET_SEQUENCE.md`
- `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_ACCEPTED_SCOPE.md`
- `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_VALUATION_MATRIX.md`
- `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_REMAINING_UNKNOWNS.md`
- `proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json`
- `proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json`
- `out/rte-ux-authority-order-reconciliation/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001_AUDIT_NOTE.md`
- `out/rte-ux-claude-rte-safety-guidance/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001_AUDIT_NOTE.md`

## Operator Surfaces Inspected

- `src/dopemux/cli.py`
  - `dopemux rte scan`
  - `dopemux rte run`
  - `dopemux rte doctor`
  - `dopemux rte status`
  - `dopemux rte preflight`
  - `dopemux rte validate-live`
  - `dopemux rte promptset audit`
  - legacy `dopemux repscan` replacement surface
  - legacy `dopemux upgrades` alias commands
  - legacy/refusal `dopemux truth`
- `src/dopemux/commands/extractor_commands.py`
  - legacy promptset/prescan utilities
  - inspected and left unchanged because the voice amendment narrowed this
    packet to confusing or safety-sensitive copy, and the implementation slice
    found the clearest red/yellow-zone problems in `src/dopemux/cli.py`
- `tests/unit/test_cli_upgrades_commands.py`
- `tests/unit/test_cli_repscan_passthrough.py`
- `tests/unit/test_extractor_command_authority.py`

## Before/After Inventory

| Surface | Before | After | Why changed |
| --- | --- | --- | --- |
| legacy `repscan --phase` help | `📊 Target Phase: Phase code or ALL for the repo scan ritual.` | `Phase code or ALL for the legacy repo scan.` | Replacement/legacy scan guidance should be direct; removed ornamental emoji and ritual phrasing. |
| legacy `repscan --run-id` help | `🆔 Ritual Session: Unique identifier for the scan run.` | `Scan run identifier.` | Run identifiers are operator controls; concise label is clearer. |
| legacy `repscan --promptgen` help | `🧠 Prompt Synthesis: Mode for automated prompt generation.` | `Prompt generation mode.` | Removed ornamental label while preserving meaning. |
| legacy `repscan --promptpack` help | `📦 Prompt Package: Specific promptpack to use for the ritual.` | `Prompt package to use.` | Removed ritual phrasing from operator help. |
| legacy `repscan --promptgen-only` help | `⚡ Synthesis Only: Execute only the prompt generation phase.` | `Run only the prompt generation phase.` | Clear procedural instruction without decorative marker. |
| legacy `repscan --prompt-root` help | `🔬 Prompt Source: Root directory for ritual prompts.` | `Root directory for prompts.` | Shorter, direct path guidance. |
| legacy `repscan --profiles-dir` help | `📂 Profile Registry: Path to the ritual profiles directory.` | `Prompt profile directory.` | Removed ritual phrasing; preserved target meaning. |
| legacy `repscan --legacy-runner` help | `⏪ Legacy Engine: Path to the legacy v3 runner.` | `Path to the legacy v3 runner.` | Removed ornamental emoji/label from legacy execution boundary. |
| legacy `repscan` docstring | `🔬 Repository Audit: Run deterministic repo scan and prompt synthesis` / `Engages ... extraction rituals.` | `Run the legacy deterministic repo scan and prompt synthesis path.` / `This legacy command is disabled. Use \`dopemux rte scan\` instead.` | Hidden replacement surface should tell the operator the replacement and not decorate the refusal path. |
| `rte scan --phase` help | `📊 Target Phase: Phase code or ALL for the repo scan ritual.` | `Phase code or ALL for the legacy repo scan.` | Legacy scan gate copy should be terse and explicit. |
| `rte scan --run-id` help | `🆔 Ritual Session: Unique identifier for the scan run.` | `Scan run identifier.` | Removed unnecessary voice from a run-control option. |
| `rte scan --promptgen` help | `🧠 Prompt Synthesis: Mode for automated prompt generation.` | `Prompt generation mode.` | Removed ornamental emoji and label. |
| `rte scan --promptpack` help | `📦 Prompt Package: Specific promptpack to use for the ritual.` | `Prompt package to use.` | Removed ritual phrasing from operator control. |
| `rte scan --promptgen-only` help | `⚡ Synthesis Only: Execute only the prompt generation phase.` | `Run only the prompt generation phase.` | More procedural wording. |
| `rte scan --prompt-root` help | `🔬 Prompt Source: Root directory for ritual prompts.` | `Root directory for prompts.` | Shorter and unambiguous. |
| `rte scan --profiles-dir` help | `📂 Profile Registry: Path to the ritual profiles directory.` | `Prompt profile directory.` | Removed metaphor from path guidance. |
| `rte scan --legacy-runner` help | `⏪ Legacy Engine: Path to the legacy v3 runner.` | `Path to the legacy v3 runner.` | Legacy runner boundary should be plain. |
| `rte scan` blocked message | `` `dopemux rte scan` delegates ... disabled by default. Pass --allow-legacy-v3-scan only after accepting the v3 consent posture; live delegated execution still requires v3 --execute and DPMX_LIVE_OK=1.`` | `Blocked: \`dopemux rte scan\` delegates ... disabled by default. Pass --allow-legacy-v3-scan only after accepting the v3 consent posture. Live delegated execution still requires v3 --execute and DPMX_LIVE_OK=1.` | Safety gate now leads with `Blocked:` and separates live-execution requirements. |
| `rte list` docstring | `📋 Catalog Phases: List ritual phases and effective pipeline order` | `List extraction phases and effective pipeline order.` | Removes ornamental/ritual wording from operator command help. |
| `rte list` long help | `Displays ... prescribed order of operations for the active ritual pipeline.` | `Displays the full sequence of extraction phases for the selected pipeline.` | Clearer pipeline description. |
| `rte run --routing-policy` help | `🧠 Cognitive Routing: LLM policy for extraction (default: model-map balanced).` | `LLM routing policy for extraction. Defaults to the model-map policy.` | Routing/provider-facing option should be procedural. |
| `rte run --batch-provider` help | `🧪 Batch Alchemist: Specific provider for asynchronous processing (default: auto).` | `Provider for asynchronous batch processing.` | Provider selection must not be obscured by metaphor. |
| `rte run --sync` help | `🔄 State Sync: Sync local artifacts before ignition (v4 only).` | `Sync local artifacts before the run (v4 only).` | Removed ignition metaphor from run behavior. |
| `rte run --skip-prescan` help | `⏩ Skip integrated Stage 0 prescan.` | `Skip integrated Stage 0 prescan.` | Removed decorative emoji. |
| `rte run --prescan-import-dir` help | `📥 Import external prescan artifacts.` | `Import external prescan artifacts.` | Removed decorative emoji. |
| `rte run --prescan-online` help | `📡 Authorize online LLM passes in prescan.` | `Authorize online LLM passes in prescan.` | Online/provider boundary should be plain. |
| `rte run --prescan-allow-scope-reduction` help | `⚖️  Allow scope reduction.` | `Allow scope reduction.` | Removed decorative emoji. |
| `rte run --allow-online-llm` help | `💸 Authorize online LLM spend for whole run.` | `Authorize online LLM spend for the run.` | Spend/provider authorization should be terse and unambiguous. |
| `rte run` docstring | `🚀 Ignite Pipeline: Run the Repo Truth Extractor (resumable)` | `Run the Repo Truth Extractor.` | Primary operator run surface should be direct. |
| `rte run` long help | `Engages ... active ritual promptset and routing policies.` | `Executes the selected extraction pipeline with the provided run controls.` | Removes ritualized phrasing from execution guidance. |
| `rte doctor --run-id` help | `🆔 Ritual Session: Unique identifier for the extraction run to diagnose.` | `Extraction run identifier to diagnose.` | Diagnostics should use clear run-control terminology. |
| `rte doctor --auto-reprocess` help | `🔧 Auto-Remediation: Automatically re-process failed partitions identified during the audit.` | `Automatically re-process failed partitions identified during the audit.` | Removed decorative label from a corrective action. |
| `rte doctor --reprocess-dry-run` help | `🔬 Ritual Preview: Simulate the re-processing sequence without committing to disk.` | `Simulate re-processing without writing changes.` | Dry-run behavior should be plain and stress-readable. |
| `rte doctor --reprocess-phases` help | `📊 Targeted Phases: Comma-separated list of extraction phases to audit.` | `Comma-separated list of extraction phases to audit.` | Removed ornamental label. |
| `rte doctor` docstring | `🏥 Extraction Apothecary: Run diagnostics and deterministic re-process planning` | `Run extraction diagnostics and deterministic re-process planning.` | Diagnostics copy belongs in the red/yellow zone, not a metaphor. |
| `rte doctor` long help | `Performs ... re-synchronization plan for failed partitions.` | `Inspects an extraction run and prepares a deterministic plan for failed partitions.` | Shorter, more procedural. |
| `rte status --run-id` help | `🆔 Ritual Session: Unique identifier for the extraction run to query.` | `Extraction run identifier to query.` | Status query option is clearer without ritual phrase. |
| `rte status --json` help | `📊 Emit JSON: Output the ritual status as raw machine-readable data.` | `Emit status as machine-readable JSON.` | Machine output should be terse. |
| `rte status` docstring | `📊 Ritual Status: Show status of an extraction run` | `Show extraction run status.` | Removed decorative emoji/ritual phrase. |
| `rte status` long help | `Retrieves current cockpit telemetry ...` | `Reports phase progression and partition status for an extraction run.` | Status output description now says what is reported. |
| `rte preflight` docstring | `🛫 Pre-Ignition Check: Run pre-flight diagnostics for an extraction run` | `Run preflight diagnostics for an extraction run.` | Preflight is safety-adjacent and should be procedural. |
| `rte preflight` long help | `Executes a comprehensive sensor audit ... ritual...` | `Verifies promptset and provider readiness before extraction.` | Provider/preflight boundary is now direct. |
| `rte promptset audit --strict` help | `🛡️  Enforce Constraints: Perform a strict structural audit of the promptset artifacts.` | `Perform a strict structural audit of promptset artifacts.` | Audit option copy should not rely on ornamental prefix. |
| `rte promptset audit` docstring | `⚖️ Ritual Integrity: Audit promptset contract compliance` | `Audit promptset contract compliance.` | Contract/audit copy should be direct. |
| `rte promptset audit` long help | `Performs a deep-tissue audit ... ritual contracts...` | `Verifies required promptset sections, schemas, and determinism.` | Removed metaphor from contract validation. |
| `truth --dry-run` help | `🔬 Ritual Preview: Simulate execution without committing to disk (default).` | `Simulate execution without writing changes (default).` | Legacy refusal surface help should be plain. |
| `truth --execute` help | `⚡ Ignite Ritual: Actually call LLM providers for extraction.` | `Call configured LLM providers for extraction.` | Provider boundary should be procedural. |
| `truth --deep` help | `🌊 Deep Harvest: Compatibility flag only; canonical v5 does not support legacy deep mode.` | `Compatibility flag only; canonical v5 does not support legacy deep mode.` | Removed ornamental label from deprecated option. |
| `truth --resume` help | `⏯️  Resume Sequence: Resume a previously suspended extraction run.` | `Resume a previously suspended extraction run.` | Removed decorative label. |
| `truth --workers` help | `⚡ Ritual Workers: Number of parallel extraction workers (default: 1).` | `Number of parallel extraction workers (default: 1).` | Removed ritual label from execution control. |
| `truth --routing-policy` help | `🧠 Cognitive Routing: Intelligence routing policy (default: cost).` | `Routing policy for extraction (default: cost).` | Routing boundary should be direct. |
| `truth` docstring | `👁️  Truth Extraction: deprecated legacy surface` | `Deprecated Repo Truth Extractor entrypoint.` | Deprecated command help should be explicit. |
| `truth` refusal | `` `dopemux truth` is no longer a supported operator entrypoint... Use the canonical `dopemux rte` family instead:`` | `Blocked: \`dopemux truth\` is not a supported Repo Truth Extractor entrypoint... Next: use \`dopemux rte\`:` | Refusal now uses procedural blocker/next-action shape. |
| `test_cli_upgrades_commands.py` expected text | `` `dopemux truth` is no longer a supported operator entrypoint`` | `` `dopemux truth` is not a supported Repo Truth Extractor entrypoint`` | Text-only test expectation update for the new refusal copy. |

## Behavior-Preservation Attestation

The implementation changed only operator-facing text strings and matching
exact-text test assertions. Runtime dispatch, option names, option types,
defaults, runner calls, validation behavior, provider behavior, routing,
pricing, promptsets, schemas, live extraction, and `DPMX_LIVE_OK` behavior were
not changed.

Manual codereview status: PASS. The final diff was reviewed as copy-only in
`src/dopemux/cli.py` plus exact expected-text test updates in
`tests/unit/test_cli_upgrades_commands.py`.

## Unknowns Preserved

- Exact Opus finding-ledger recovery is `UNKNOWN` because
  `out/rte-opus-uiux-claude-design-audit/` is absent in this worktree.
- Exact Opus recommendation-to-finding crosswalk is `UNKNOWN` without the source
  audit bundle.
- `CRIT-1` is preserved as valuation-derived, not independently recovered from
  a local Opus findings ledger.
- Broader repo-wide agent runtime authority remains `UNKNOWN` where no specific
  runtime path is verified.

## No-Provider / No-Live Attestation

- No provider calls were run.
- No live extraction was run.
- No live preflight was run.
- No network/provider validation was run.
- No account-specific checks were run.

## Base And Checkout Attestation

- Base ref used: `origin/main`.
- Worktree path:
  `/Users/hue/code/dopemux-mvp-rte-cli-tone-emoji-cleanup-after-pr644`.
- Worktree branch: `codex/rte-cli-tone-emoji-cleanup-after-pr644`.
- Worktree `HEAD` before edits:
  `de69cfd120c43916ee89caf9f9c0f5ceacfcf8c6`.
- Primary checkout path: `/Users/hue/code/dopemux-mvp`.
- Primary checkout was not edited by this packet. The required `git fetch origin
  main` updated tracking refs; existing dirty files in the primary checkout were
  left untouched.

## PR #644 Merge Gate Evidence

- `gh pr view 644` reported `state=MERGED`, `isDraft=false`,
  `baseRefName=main`, `mergedAt=2026-05-18T03:52:54Z`, and merge commit
  `de69cfd120c43916ee89caf9f9c0f5ceacfcf8c6`.
- `git merge-base --is-ancestor de69cfd120c43916ee89caf9f9c0f5ceacfcf8c6 origin/main`
  passed.
- Packet 2 cleanup artifacts and authority-order gate artifacts resolved on
  `origin/main` before worktree creation.

## Validation Results

- PASS: `python - <<'PY' ... task packet payload schema validation ... PY`
- PASS: `python -m compileall -q src tests`
- PASS: `uv run --frozen --extra test python -m pytest -q tests/unit/test_cli_upgrades_commands.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_extractor_command_authority.py`
- PASS: `git diff --check`
- PASS: `python -m json.tool proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json`
- PASS: final forbidden-scope guards for `services/**`, promptsets/schemas, and routing/pricing/provider config
- PASS: no follow-on packet IDs found outside excluded valuation, packet, audit, and proof contexts
- PASS: primary checkout status reviewed; existing dirty files were unchanged by this packet
- PASS: `pre-commit run --files src/dopemux/cli.py tests/unit/test_cli_upgrades_commands.py task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json`
