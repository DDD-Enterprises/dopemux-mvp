---
id: rte-production-certification-audit-20260414
title: RTE Production Certification Audit
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-14'
status: blocked
last_review: '2026-04-14'
next_review: '2026-05-14'
prelude: Exhaustive read-only certification audit for the canonical repo-truth extractor runtime and dopemux operator-facing CLI, TUI, UX, and voice surfaces.
---
# RTE Production Certification Audit

**Branch audited:** `tp/rte-v5-seam-foundation-restart`
**HEAD SHA:** `3d5c3c2fb944942c5c368e85481ce2723feb1282`
**Audit date:** `2026-04-14`
**Mode:** read-only audit plus patch-ready remediation backlog
**Overall release verdict:** `NO-GO / BLOCKED`

## Executive Summary

The canonical repo-truth extraction runtime remains materially healthier than the dopemux operator surfaces around it. The targeted v5/v4 extractor suites passed again on this branch, which is strong evidence that `services/repo-truth-extractor/run_extraction_v5.py` is stable on the packet-critical contracts already covered by tests. Production certification is still blocked because the wrapper plane, install-time UX dependencies, brand/runtime authority, and certification tooling are not coherent enough to trust in front of operators.

Current certification assessment:

| Area | Score | Status | Evidence-backed reason |
|------|-------|--------|------------------------|
| RTE runtime correctness | 7/10 | `PARTIAL` | Canonical v5/v4/operator/reporting suites passed, but live-provider execution and every wrapper path were not certified end-to-end. |
| Artifact and fail-closed contracts | 8/10 | `PASS` | Promptset fail-closed, proof/report contracts, and resume smoke stayed green in targeted suites. |
| Wrapper and entrypoint coherence | 3/10 | `BLOCKED` | `dopemux truth` remains a broken legacy path and `extract truth-run --resume` changes v5 resume semantics. |
| Dependency and install integrity | 3/10 | `BLOCKED` | `questionary` is imported by multiple UX surfaces but is not declared in `pyproject.toml`. |
| CLI/TUI usability | 5/10 | `PARTIAL` | The main help surfaces are readable, but blocker visibility, wizard safety messaging, and dashboard portability drift remain. |
| Brand and voice coherence | 4/10 | `BLOCKED` | Theme defaults, brand docs, voice gates, and the brand checklist disagree on the production standard. |
| Accessibility and log readability | 5/10 | `PARTIAL` | Text-first semantics exist, but blinking, emoji-heavy signaling, and endpoint assumptions reduce operational clarity. |
| Certification gate completeness | 4/10 | `BLOCKED` | `brand_lint.py` is not runnable on this checkout and `.pre-commit-config.yaml` remains docs-heavy. |

Recommended production direction:

| Option | Fit | Distinctiveness | Operator trust | Maintenance | Recommendation |
|--------|-----|-----------------|----------------|-------------|----------------|
| `Option A: Operational Mint Production` | 9/10 | 7/10 | 9/10 | 8/10 | **Recommended**. Keep mint/cyan/ink-black, chips, and aftercare; constrain spicy brand voice to banners and opt-in surfaces. |
| `Option B: Balanced Ritual Daemon` | 7/10 | 8/10 | 7/10 | 7/10 | Viable if the team insists on more personality in non-critical surfaces. |
| `Option C: Maximalist Luxury Filth` | 4/10 | 10/10 | 4/10 | 5/10 | Strong aesthetic identity, weak production safety and governance fit. |

## Authority and Call-Flow Map

### Runtime and authority classes

| Surface | Classification | Evidence |
|--------|----------------|----------|
| `services/repo-truth-extractor/run_extraction_v5.py` | `authoritative runtime` | Canonical runner; targeted runtime suites passed on this branch. |
| `services/repo-truth-extractor/run_extraction_v4.py` | `compatibility runtime` | Active shim; v4 core suite passed. |
| `services/repo-truth-extractor/run_extraction_v3.py` | `legacy compatibility runtime` | Still present and still referenced by docs and compatibility flows. |
| `src/dopemux/commands/extract_commands.py` `truth-run` path | `canonical direct wrapper with drift` | Directly execs `run_extraction_v5.py`, but currently injects a fresh `--run-id` on resume. |
| `src/dopemux/commands/extractor_commands.py` / `dopemux upgrades` runner helpers | `canonical wrapper family` | These paths target the extractor runners directly and are the closest CLI authority after the raw v5 runner. |
| `src/dopemux/cli.py` `truth` command | `legacy / broken` | Delegates to `PipelineRunner`, not the v5 runtime. |
| `src/dopemux/extractor/runner.py` | `legacy simulator / non-canonical` | Emits trace markdown and contains a live `NameError` path. |
| `src/dopemux/ui/*`, `src/dopemux/ux/*`, `src/dopemux/voice/*`, `services/shared/brand_voice.py` | `operator UX / shared voice authority` | These surfaces define what operators see and hear, but they do not currently agree on one production contract. |

### Command-to-runtime map

| Operator surface | Current target | Classification | Production status |
|------------------|----------------|----------------|-------------------|
| `dopemux upgrades run --pipeline-version v5` | runner helper -> `run_extraction_v5.py` | canonical wrapper | `PARTIAL` |
| `dopemux upgrades doctor/status/preflight` | runner helper -> extractor runtimes | canonical wrapper family | `PARTIAL` |
| `dopemux extract truth-run` | direct subprocess -> `run_extraction_v5.py` | canonical wrapper with drift | `PARTIAL` |
| `dopemux extractor ...` | legacy group, but many subcommands route to extractor runtimes | compatibility wrapper | `PARTIAL` |
| `dopemux extractor trace` | `PipelineRunner` | legacy non-canonical trace simulator | `NON-PRODUCTION` |
| `dopemux truth` | `PipelineRunner.run_all()` | broken legacy shortcut | `BLOCKED` |
| `dopemux.ux.wizard.runner` stage 6 | intended wrapper around `dopemux extract truth-run` | blocked by missing `questionary` and command-assembly drift | `BLOCKED` |
| `dopemux dashboard` / `dashboard_detail` | local TUI against hard-coded service URLs | operator observability surface | `PARTIAL` |

## Severity-Ranked Code Findings

### `[P1]` `dopemux truth` is a broken legacy path, not a production wrapper

- **Observed evidence**
  - `src/dopemux/cli.py:5153-5198` routes `dopemux truth` to `PipelineRunner`.
  - `src/dopemux/extractor/runner.py:75-86` uses `project_root` instead of `self.project_root`, which raises `NameError`.
  - `src/dopemux/extractor/runner.py:232-238` writes only `PHASE_*_TRACE.md` files, not v5 run artifacts.
  - Runtime probe on this branch reproduced the legacy trace-only behavior when prescan was disabled.
- **Why it matters**
  - Operators can select a command that claims universal truth extraction but does not reach the canonical runtime contract.
- **Affected files and consumers**
  - `src/dopemux/cli.py`
  - `src/dopemux/extractor/runner.py`
  - Any operator or doc path that still presents `dopemux truth` as authoritative.
- **Recommended minimal fix**
  - Either rewire `dopemux truth` to the same canonical v5 wrapper used by `upgrades run` / `extract truth-run`, or demote it explicitly as legacy and fail closed with a redirect message.
- **Proof command**
  - `PYTHONPATH=src python -m dopemux.cli truth --help`
  - Add a command-path test that asserts the selected runtime target is the v5 runner or that the command exits with an explicit legacy refusal.

### `[P1]` `dopemux extract truth-run --resume` breaks v5 latest-run resume semantics

- **Observed evidence**
  - `src/dopemux/commands/extract_commands.py:1008` generates `auto_run_id = run_id or datetime.now().strftime(...)`.
  - `src/dopemux/commands/extract_commands.py:1119-1124` always appends `--run-id <auto_run_id>` plus `--resume`.
  - `services/repo-truth-extractor/rte_output_layout.py:206-230` only falls back to `latest_run_id.txt` when `args.run_id` is absent.
  - Runtime probe on this branch showed `--resume` assembling a fresh `RUN-...` id instead of omitting the flag.
- **Why it matters**
  - Resume flows are operator-sensitive. A wrapper that silently changes run identity can invalidate the expected checkpoint and proof path.
- **Affected files and consumers**
  - `src/dopemux/commands/extract_commands.py`
  - `services/repo-truth-extractor/rte_output_layout.py`
  - `services/repo-truth-extractor/tests/test_truth_run_cli.py`
- **Recommended minimal fix**
  - When `--resume` is set and the user did not specify `--run-id`, omit `--run-id` so v5 can resolve `latest_run_id.txt`.
- **Proof command**
  - Add a wrapper test asserting that `truth-run --resume` without `--run-id` does not pass `--run-id` to the subprocess.

### `[P1]` Wizard and interactive UX paths depend on undeclared `questionary` and fail before preflight

- **Observed evidence**
  - `pyproject.toml:28-61` does not declare `questionary`.
  - `src/dopemux/ux/interactive_prompts.py:14-15`, `src/dopemux/ux/wizard/extraction.py:8`, `src/dopemux/ux/wizard/prompts.py:9`, and `src/dopemux/ux/wizard/cost_profiles.py:12` import `questionary` unconditionally.
  - `src/dopemux/ux/wizard/runner.py:10-17` imports those wizard stages at module import time.
  - `src/dopemux/ux/wizard/preflight.py:36-41` checks for `questionary` only after those imports would already have failed.
  - Import smoke on this branch failed for all of those modules with `ModuleNotFoundError: No module named 'questionary'`.
- **Why it matters**
  - The current operator UX cannot be considered installable or production-safe if core interactive surfaces crash before their own health checks.
- **Affected files and consumers**
  - `pyproject.toml`
  - `src/dopemux/ux/interactive_prompts.py`
  - `src/dopemux/ux/wizard/*`
- **Recommended minimal fix**
  - Decide between a required dependency or a tested optional fallback. If optional, lazy-import `questionary` inside interaction paths and fail closed with a plain-text fallback or a precise install error.
- **Proof command**
  - `PYTHONPATH=src python - <<'PY' ... import dopemux.ux.wizard.runner ... PY`
  - Add a clean-environment import smoke test for all supported operator surfaces.

### `[P1]` The current certification gate is not trustworthy because `brand_lint.py` is not runnable

- **Observed evidence**
  - `scripts/brand_lint.py` parses audited files with `ast.parse(...)`.
  - Running `python scripts/brand_lint.py` failed on `IndentationError` from `services/activity-capture/main.py:32`.
  - `services/activity-capture/main.py:29-43` contains a real indentation defect in `_configure_import_paths()`.
- **Why it matters**
  - A non-runnable certification hook is worse than an absent one because it creates false confidence about gate coverage.
- **Affected files and consumers**
  - `scripts/brand_lint.py`
  - `services/activity-capture/main.py`
  - Any release process that treats brand lint as part of a production gate.
- **Recommended minimal fix**
  - Repair the syntax error first, then expand `brand_lint.py` into a real certification check instead of a best-effort script.
- **Proof command**
  - `python scripts/brand_lint.py`

### `[P2]` The rich validation UI hides blocker detail that the plain UI preserves

- **Observed evidence**
  - `src/dopemux/commands/extractor_validation_ui.py:61-70` renders only one `"Why stopped spending"` row.
  - `src/dopemux/commands/extractor_validation_ui.py:117-119` returns only the first blocker.
  - `src/dopemux/commands/extractor_validation_ui.py:85-88` prints the full blocker list in plain mode.
  - Probe payload on this branch reproduced that split exactly.
- **Why it matters**
  - The richer surface should not reduce operator access to blockers or remediation data.
- **Affected files and consumers**
  - `src/dopemux/commands/extractor_validation_ui.py`
  - Operators using the rich validation dashboard.
- **Recommended minimal fix**
  - Add a rich blocker list section or a compact multi-row blocker table while keeping the summary rail.
- **Proof command**
  - Add a UI rendering test that compares blocker visibility parity between plain and rich modes.

### `[P2]` The extraction wizard’s copy and runtime behavior disagree on hygiene scanning

- **Observed evidence**
  - `src/dopemux/ux/wizard/extraction.py:53-59` says `truth-run handles ... hygiene scanning`.
  - `src/dopemux/ux/wizard/extraction.py:96-105` always appends `--skip-hygiene`.
- **Why it matters**
  - This is a direct safety and trust mismatch in a guided operator flow.
- **Affected files and consumers**
  - `src/dopemux/ux/wizard/extraction.py`
- **Recommended minimal fix**
  - Either stop forcing `--skip-hygiene` or change the wizard copy to explain the current shortcut honestly.
- **Proof command**
  - Add a wizard command-assembly test that asserts the safety copy matches the actual flags.

## Severity-Ranked UI / UX Findings

### `[P1]` Production brand authority is split across incompatible docs and runtime gates

- **Observed evidence**
  - `docs/04-explanation/branding/dopemux-brand-system.md:15-22` makes “luxury filth”, kink-coded tone, and self-aware roasts part of the canonical spec.
  - `src/dopemux/voice/core.py:143-145` forces all `Surface.UI` output into `UI_STRICT`.
  - `src/dopemux/voice/core.py:217-230` forbids public shame / roast-escalation language on UI surfaces.
  - `services/shared/brand_voice.py:41-53` and `:55-83` already behave more like a deterministic operational voice than the spicier brand doc.
- **Why it matters**
  - The team cannot certify copy, prompts, or UI tone while runtime and docs disagree on what “on-brand” means.
- **Direct recommendation**
  - Adopt `Operational Mint Production` as the production default:
    - Palette authority: `ink.black`, `void.navy`, `ritual.cyan`, `serum.mint`, `gilt.edge`, `gremlin.pink`, `aftercare.violet`
    - Runtime voice: `UI_STRICT` for UI shapes and `ClinicalForensics` for preflight, errors, and blockers
    - Allow `BannerOneLiner` only for banners and help headings
    - Demote `FilthDaemon`, `UXScold`, and kink-coded copy to opt-in or non-operational surfaces

### `[P2]` Theme defaults do not match the documented production palette

- **Observed evidence**
  - `src/dopemux/ui/theme.py:43` defaults to `"pastel-neon-dreams"`.
  - `src/dopemux/ui/theme.py:90-140` contains the documented `mint-mojo` palette.
  - `src/dopemux/ui/dopemux.tcss:1-19` uses `mint-mojo`-aligned tokens.
  - `docs/04-explanation/branding/cli-ux-design-spec.md:22-55` describes the neon mint palette as the CLI/TUI authority.
- **Why it matters**
  - Operators and contributors are being told that one palette is authoritative while runtime defaults to another.
- **Direct recommendation**
  - Make `mint-mojo` the default production theme. Keep the pastel themes as explicit opt-in themes only after they pass the same contrast and component checks.

### `[P2]` The launcher wizard bypasses shared theme and style rules

- **Observed evidence**
  - `src/dopemux/ux/launcher_wizard.py:28-36` defines local color constants and uses a local `Console()`.
  - `src/dopemux/ux/launcher_wizard.py:37-49` hardcodes an alternate ASCII-art header and color treatment.
- **Why it matters**
  - This surface does not inherit the same tokens, chips, or voice discipline as the rest of dopemux, so it will continue to drift.
- **Direct recommendation**
  - Move the launcher wizard onto `dopemux.console`, `StatusChip`, and the shared semantic style names from `src/dopemux/ui/theme.py`.
- **Current rating**
  - Visual distinctiveness: `7/10`
  - Production coherence: `4/10`
  - Accessibility and legibility: `6/10`

### `[P2]` The dashboard is visually strong in demo mode but not portable or trust-heavy enough for certification

- **Observed evidence**
  - `src/dopemux/ui/dashboard.py:103-114`, `:190-206`, and `:259-263` hard-code localhost service URLs.
  - `src/dopemux/ui/dashboard_detail.py:65-66`, `:86-88`, and `:109-113` do the same.
  - `src/dopemux/ui/dashboard.py:168` uses `[blink]`.
  - `src/dopemux/ui/dopemux.tcss:87-108` defines blinking animation for active and error states.
- **Why it matters**
  - A production dashboard needs explicit source configuration, connection age, and graceful offline behavior. Motion should not carry severity on its own.
- **Direct recommendation**
  - Externalize endpoints into config/env, display source + last refresh age per panel, and replace blink with static severity chips plus optional compact pulse only for demo mode.
- **Current rating**
  - Visual hierarchy: `7/10`
  - Operational trust: `4/10`
  - Portability: `3/10`
  - Accessibility: `4/10`

### `[P2]` The rich validation UI is better-looking than the plain view but worse at telling the truth

- **Observed evidence**
  - See the blocker-parity finding above.
  - The current rich layout emphasizes stage rails and spend but not the full remediation set.
- **Why it matters**
  - Production UX must prefer truthfulness over aesthetics.
- **Direct recommendation**
  - Keep the stage rail, but add:
    - a “Blockers” table
    - explicit next action per blocker
    - a “safe to spend?” verdict row
- **Current rating**
  - Scanability: `7/10`
  - Failure recovery: `4/10`
  - Trust: `5/10`

### `[P2]` The brand checklist itself is currently corrupted

- **Observed evidence**
  - `docs/03-reference/brand-compliance-checklist.md:20-22` contains merge conflict markers.
- **Why it matters**
  - A corrupted checklist cannot serve as an authority or release artifact.
- **Direct recommendation**
  - Resolve the conflict and reduce the checklist to machine-checkable production assertions only.

## Contradiction and Drift Ledger

| Drift | Repo-truth evidence | Impact |
|------|----------------------|--------|
| Canonical CLI messaging vs actual shortcut behavior | `services/repo-truth-extractor/README.md:30-38` points operators to `dopemux upgrades ...`, while `src/dopemux/cli.py:5153-5198` still exposes `dopemux truth` as a universal shortcut. | Operator confusion and wrong command selection. |
| Brand doc vs runtime UI gates | `docs/04-explanation/branding/dopemux-brand-system.md:15-22` vs `src/dopemux/voice/core.py:217-230` | No single production tone authority. |
| Theme default vs CLI/TUI spec | `src/dopemux/ui/theme.py:43` vs `docs/04-explanation/branding/cli-ux-design-spec.md:22-55` | Token drift and inconsistent visuals. |
| Shared theme vs launcher wizard | `src/dopemux/ui/theme.py` vs `src/dopemux/ux/launcher_wizard.py:28-49` | Visual fragmentation. |
| Wizard preflight vs import-time dependency failure | `src/dopemux/ux/wizard/preflight.py:36-41` vs `src/dopemux/ux/wizard/runner.py:10-17` | Health checks do not actually protect operators. |
| Rich validation UX vs plain validation UX | `src/dopemux/commands/extractor_validation_ui.py:61-70` and `:117-119` vs `:85-88` | Rich mode hides blocker truth. |
| Brand checklist as release authority vs merge-corrupted file | `docs/03-reference/brand-compliance-checklist.md:20-22` | Invalid certification reference. |

## Validation Evidence Ledger

### Branch and worktree confirmation

- `git status --short --branch`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git worktree list --porcelain`

Observed result: current checkout is `/Users/hue/code/dopemux-mvp` on `tp/rte-v5-seam-foundation-restart` at `3d5c3c2fb944942c5c368e85481ce2723feb1282`.

### Runtime and contract validation

- `pytest -q services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_extraction_v4_core.py services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py services/repo-truth-extractor/tests/test_run_extraction_v5_promptset_truth.py services/repo-truth-extractor/tests/test_run_extraction_v5_rollup_reports.py services/repo-truth-extractor/tests/test_provider_preflight_openrouter.py services/repo-truth-extractor/tests/test_run_extraction_v5_ui_events.py services/repo-truth-extractor/tests/test_run_extraction_v5_soft_gate_logging.py services/repo-truth-extractor/tests/test_output_safety.py services/repo-truth-extractor/tests/test_v5_resume_smoke.py services/repo-truth-extractor/tests/test_phase_interaction.py services/repo-truth-extractor/tests/test_phase_execution_step_filter.py services/repo-truth-extractor/tests/test_phase_s_prompt_registry.py services/repo-truth-extractor/tests/test_phase_s_step_selection.py services/repo-truth-extractor/tests/test_v5_golden_fixture_smoke.py`
  - Result: exit `0`

### Shared UX / brand validation

- `pytest -q tests/test_voice_core.py tests/test_brand_voice.py tests/unit/test_extractor_validation.py tests/unit/test_ui_dashboard_backend_api.py tests/unit/test_dashboard_api_client.py tests/unit/test_profile_wizard.py`
  - Result: exit `0`
- `python -m py_compile src/dopemux/cli.py src/dopemux/commands/extract_commands.py src/dopemux/commands/extractor_commands.py src/dopemux/commands/extractor_validation.py src/dopemux/commands/extractor_validation_ui.py src/dopemux/extractor/runner.py src/dopemux/ui/dashboard.py src/dopemux/ui/dashboard_detail.py src/dopemux/ui/theme.py src/dopemux/ui/voice.py src/dopemux/ux/interactive_prompts.py src/dopemux/ux/wizard/extraction.py src/dopemux/ux/launcher_wizard.py src/dopemux/voice/core.py services/shared/brand_voice.py services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/run_extraction_v4.py services/repo-truth-extractor/run_extraction_v3.py`
  - Result: exit `0`
- `PYTHONPATH=src python -m dopemux.cli dashboard --help`
  - Result: exit `0`
- `python scripts/brand_lint.py`
  - Result: exit `1` because `services/activity-capture/main.py` currently raises `IndentationError`

### Direct probes

- Import smoke:
  - `PYTHONPATH=src python - <<'PY' ... import dopemux.ux.interactive_prompts ... PY`
  - Result: failed with `ModuleNotFoundError: No module named 'questionary'`
- Wizard import smoke:
  - `PYTHONPATH=src python - <<'PY' ... import dopemux.ux.wizard.runner ... PY`
  - Result: failed with `ModuleNotFoundError: No module named 'questionary'`
- Truth-run resume probe:
  - `CliRunner().invoke(cli, ['extract', 'truth-run', '--resume', '--skip-hygiene'])`
  - Result: assembled `--run-id RUN-... --resume`, confirming wrapper drift
- Validation UI probe:
  - Plain renderer displayed both blockers, while `_why_stopped()` only returned the first blocker
- PipelineRunner probe:
  - Legacy path emitted trace-only artifacts and did not exercise the canonical v5 contract

## Remediation Plan and Sequencing

### Release blockers: must clear before any production certification claim

| ID | Owner surface | Severity | Minimal safe fix | Smallest proving validation |
|----|---------------|----------|------------------|-----------------------------|
| `CERT-01` | `src/dopemux/cli.py`, `src/dopemux/extractor/runner.py` | `P1` | Rewire or explicitly demote `dopemux truth` and legacy trace surfaces. | Wrapper-path tests proving canonical delegation or explicit refusal. |
| `CERT-02` | `src/dopemux/commands/extract_commands.py` | `P1` | Preserve v5 latest-run resume semantics by omitting `--run-id` when resume has no explicit id. | `test_truth_run_cli.py` coverage for resume without explicit run id. |
| `CERT-03` | `pyproject.toml`, `src/dopemux/ux/*` | `P1` | Add `questionary` as a supported dependency or a tested lazy fallback. | Clean-environment import smoke for wizard and interactive prompts. |
| `CERT-04` | `src/dopemux/ux/wizard/*` | `P1` | Make dependency preflight real by ensuring missing deps are detected before import-time failure. | Wizard entrypoint import and stage-0 smoke in a dep-missing environment. |
| `CERT-05` | `services/activity-capture/main.py`, `scripts/brand_lint.py` | `P1` | Fix the syntax error and restore a runnable brand certification gate. | `python scripts/brand_lint.py` exits `0`. |
| `CERT-06` | `docs/03-reference/brand-compliance-checklist.md` | `P2` | Resolve merge conflict markers and reduce the checklist to current production assertions. | Docs validation plus a plain text grep showing no conflict markers. |

### Short-term hardening: do next

| ID | Owner surface | Severity | Minimal safe fix | Smallest proving validation |
|----|---------------|----------|------------------|-----------------------------|
| `CERT-07` | `src/dopemux/commands/extractor_validation_ui.py` | `P2` | Rich mode must render all blockers and next actions. | Rendering test comparing rich/plain blocker parity. |
| `CERT-08` | `src/dopemux/ux/wizard/extraction.py` | `P2` | Align copy and behavior for hygiene scanning. | Wizard command-assembly test and one smoke transcript. |
| `CERT-09` | `src/dopemux/ui/dashboard.py`, `src/dopemux/ui/dashboard_detail.py` | `P2` | Externalize endpoints, add source age, and harden offline mode. | Dashboard config test plus offline-mode screenshot/smoke. |
| `CERT-10` | `src/dopemux/ux/launcher_wizard.py` | `P2` | Migrate to shared theme tokens and status chips. | Themed rendering test or token grep proving no local raw palette remains. |
| `CERT-11` | `src/dopemux/ui/theme.py`, `src/dopemux/ui/dopemux.tcss`, docs | `P2` | Choose one production palette, preferably `mint-mojo`, and make it the default authority. | Theme-default test plus doc/token consistency check. |
| `CERT-12` | `src/dopemux/voice/*`, `services/shared/brand_voice.py`, docs | `P2` | Pick one operational voice contract and scope spicier modes away from blocker/error/preflight paths. | `tests/test_voice_core.py`, `tests/test_brand_voice.py`, and a brand-lint extension covering operator-critical copy. |

### Certification automation and release gate: do before sign-off

| ID | Owner surface | Severity | Minimal safe fix | Smallest proving validation |
|----|---------------|----------|------------------|-----------------------------|
| `CERT-13` | `.pre-commit-config.yaml`, CI | `P2` | Add real Python/runtime/operator-surface checks; stop treating docs-only hooks as certification evidence. | Explicit certification workflow or script with PASS/PARTIAL/BLOCKED output. |
| `CERT-14` | tests for wrappers, installs, wizard, dashboard, brand | `P2` | Add coverage for wrapper authority, dependency-complete imports, dashboard offline behavior, and theme/component compliance. | New targeted test families passing in CI. |
| `CERT-15` | release process | `P2` | Introduce one machine-readable go/no-go artifact with gate statuses and unresolved UNKNOWNs. | A generated certification JSON plus release sign-off review. |

### Recommended production style implementation

If the team accepts `Operational Mint Production`, implement it as:

- **Color**
  - Default theme: `mint-mojo`
  - Required tokens: `#020617`, `#041628`, `#7DFBF6`, `#94FADB`, `#F5F26D`, `#FF8BD1`, `#9B78FF`
  - Other palettes allowed only as opt-in themes, not as the default production identity
- **Voice**
  - `UI_STRICT` for UI payload shape
  - `ClinicalForensics` for blockers, auth, validation, preflight, and doctor output
  - `BannerOneLiner` for help banners and cold-open brand marks
  - `FilthDaemon` / `UXScold` restricted to demos, opt-in fun surfaces, or non-critical copy
- **Style**
  - Keep bracket chips and aftercare
  - Remove public-shame or kink-coded phrasing from blockers, auth failures, preflight, and operational recovery
  - Reduce motion to optional demo mode only

## Residual Unknowns and Deferred Risks

- Live provider execution, paid validation stages, and every service topology were not exercised in this audit.
- The canonical v5 runtime still deserves a broader live-readiness pass before any operator claims “production certified”.
- Legacy v3 and v4 surfaces remain active and continue to enlarge maintenance burden even if the wrapper/UI blockers above are repaired.
- The current audit did not certify unrelated web surfaces outside the dopemux operator CLI/TUI/voice plane.
- External non-repo consumers of emitted proof, status, and dashboard artifacts remain `UNKNOWN`.
