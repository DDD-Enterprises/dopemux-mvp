# RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001 — Audit Note

## Packet

- **Packet id**: `RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001`
- **Recommendation**: `R-OPUS-8`
- **Finding label**: `HIGH-1` (valuation-derived; the source audit bundle
  `out/rte-opus-uiux-claude-design-audit/` is **absent** from this checkout, so
  the exact finding-ledger mapping cannot be reconstructed locally — preserved
  as UNKNOWN below).
- **Base ref**: `origin/main`
- **Base HEAD**: `fbf1b5df333e815db718ec05b4bc324ebf7d9af6` (`origin/main`
  after packet-4 branch refresh; PR #645 merge commit
  `b2558dfbc931f59d6dc338c63a8cc5d97ed592a0` is an ancestor).
- **Worktree**: `/Users/hue/code/dopemux-mvp-rte-prelive-validator-error-shape`
- **Branch**: `codex/rte-prelive-validator-error-shape`
- **Primary checkout**: `/Users/hue/code/dopemux-mvp` — **not modified** by this
  packet (already dirty at session start; left as-is per packet rules).

## PR Merge Gate Evidence

All four prior packet PRs verified merged into `origin/main` before packet-4
implementation work. During the 2026-05-19 refresh, PR #645 was reverified as
merged and its merge commit was reverified as an ancestor of current
`origin/main`:

| PR | Title | State | Merged at | Merge commit |
| --- | --- | --- | --- | --- |
| #640 | RTE UX valuation proof pack | MERGED | 2026-05-17T11:01:15Z | `3bdb146813ad34de44078d86900c3fdbb971ef25` |
| #643 | Claude/RTE safety guidance | MERGED | 2026-05-18T01:13:19Z | `0083f50a58ffa5e9d34eb3c9c620bf28076541e5` |
| #644 | RTE UX proof replay cleanup (packet 2) | MERGED | 2026-05-18T03:52:54Z | `de69cfd120c43916ee89caf9f9c0f5ceacfcf8c6` |
| #645 | RTE UX CLI tone emoji cleanup | MERGED | 2026-05-18T07:07:46Z | `b2558dfbc931f59d6dc338c63a8cc5d97ed592a0` |

PR #645's merge commit is no longer `origin/main` HEAD because `origin/main`
also contains later merges. `git merge-base --is-ancestor` confirms the PR #645
merge commit is still an ancestor of current `origin/main`.

Refresh evidence:

- Existing packet-4 worktree reused:
  `/Users/hue/code/dopemux-mvp-rte-prelive-validator-error-shape`.
- Existing local commit before refresh:
  `956f30de647e58dcc5e1dc8c3468af1831b17c30`.
- Safety branch created before rebase:
  `backup/rte-prelive-validator-error-shape-before-refresh-20260519064527`.
- Rebase target: `origin/main` at
  `fbf1b5df333e815db718ec05b4bc324ebf7d9af6`.
- Rebase result: successful, no conflicts.
- Final refreshed commit SHA is reported in closeout because this audit note is
  committed inside that same commit.

## Authority Read

Authority files read for this packet (evidence-first order):

1. `AGENTS.md`
2. `.claude/PROJECT_INSTRUCTIONS.md`
3. `.claude/brand-voice-guidelines.md`
4. `docs/03-reference/governance/rules.md`
5. `docs/03-reference/truth/truth-canonicals.md`
6. `docs/03-reference/truth/truth-scope.md`
7. `docs/03-reference/systems/system-boundaries.md`
8. `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md`
9. `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_MANIFEST.json`
10. `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_PACKET_SEQUENCE.md`
11. `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_ACCEPTED_SCOPE.md`
12. `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_VALUATION_MATRIX.md`
13. `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_REMAINING_UNKNOWNS.md`
14. `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_DEFERRED_ITEMS.md`
15. `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_NO_RUNTIME_CHANGE_ATTESTATION.md`
16. `proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json`
17. `proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json`
18. `proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json`
19. `out/rte-ux-authority-order-reconciliation/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001_AUDIT_NOTE.md`
20. `out/rte-ux-claude-rte-safety-guidance/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001_AUDIT_NOTE.md`
21. `out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md`

### Authority drift recorded

- The valuation matrix
  (`RTE-UX-VAL-001_VALUATION_MATRIX.md`) frames R-OPUS-8 as fixing a
  `ClickException` collapse in "the CLI wrapper" of `src/dopemux/cli.py`.
  Runtime inspection of `src/dopemux/cli.py` shows **no** reference to
  `validate_pre_live_gate`, `enforce_pre_live_validator`, or `run_extraction_v5`
  on the pre-live validator path; the click CLI does not host this surface.
  Both call sites that collapse validator failure live inside
  `services/repo-truth-extractor/run_extraction_v5.py` (argparse-based).
  This packet records the matrix's "ClickException" wording as
  valuation-derived terminology and treats `src/dopemux/cli.py` as out of
  scope — consistent with the allowlist condition ("only if evidence proves
  the generic ClickException collapse lives in the CLI wrapper").

## Runtime Files Inspected

- `src/dopemux/cli.py` — read-only; confirmed no validator integration. Not
  modified.
- `services/repo-truth-extractor/run_extraction_v5.py` — modified.
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py` — read-only;
  verdict logic untouched.
- `services/repo-truth-extractor/rte_ops_surfaces.py` — read-only; the
  `run_pre_live_validator` implementation (which returns the `(bool, payload)`
  tuple with `{generated_at, validator_path, exit_code, status, stdout,
  stderr}`) is unchanged.
- `services/repo-truth-extractor/output_safety.py` — read-only; existing
  `sanitize_text_for_output` reused for validator stderr.
- Tests:
  - `services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py` —
    extended with seven new tests.
  - `services/repo-truth-extractor/tests/test_run_extraction_v5_live_gate_terminality.py` —
    read-only; substring assertions on consent gate output are unaffected by
    the new message format (no overlap with the strings this packet changes).
  - `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py` — read-only.

## What Changed

### `services/repo-truth-extractor/run_extraction_v5.py`

1. **Added** three internal helpers next to `build_pre_live_validator_command`:
   - `format_pre_live_validator_block(...)` — pure function that returns a
     multi-line, plain-text operator-facing block message containing
     `verdict`, optional `parse_status`, `reason_codes`, `output_dir`,
     optional `artifact`, optional sanitized `stderr`, and a procedural
     `next_step`. No emoji, no decorative framing.
   - `_emit_pre_live_validator_block(text)` — writes the block verbatim to
     `sys.stderr` and flushes. Bypassing the line-prefixing logger keeps
     subsequent lines readable while the short `RuntimeError`/`parser.error`
     message itself remains single-line and backward-compatible for log
     formatters.
   - `_normalize_reason_codes(value)` — defensive coercion of payload
     `reason_codes` (list/tuple/string/None) into `Optional[List[str]]`.
2. **Updated** `enforce_pre_live_validator_for_execution`:
   - Validator command construction (`build_pre_live_validator_command`),
     `subprocess.run` arguments, `DPMX_LIVE_OK` consent short-circuit, and
     return-payload shape are unchanged.
   - Malformed validator stdout (`json.loads` raises) is now an explicit
     `parse_error` flag and treated as fail-closed regardless of
     `returncode`. This adds **no new GO path** — it only guarantees the
     existing fail-closed contract still holds in the (implausible but
     possible) `returncode == 0` + unparseable-stdout case.
   - When blocking, the structured block is emitted to stderr; the
     `RuntimeError` is rewritten to a short single-sentence message
     (`Pre-live validator blocked live execution (verdict=NO_GO). See
     structured block above for details.`) that survives `logger.error("%s",
     exc)` without mangling.
   - Validator stderr is sanitized through `sanitize_text_for_output` before
     it ever reaches the operator-facing block, so the pre-existing redaction
     contract is preserved.
3. **Updated** the secondary validator-first preset call site in `main()`:
   - `run_pre_live_validator` is still called with the same arguments, still
     writes `PRELIVE_VALIDATOR_RESULT.json` via
     `write_confidence_ramp_artifacts`, and the `--skip-pre-live-validator`
     wording is preserved (now carried as the `next_step` hint).
   - The "parse validator payload + emit block" logic is factored into a
     named helper, `_emit_validator_first_preset_block(validator_payload,
     run_root)`, so the secondary path is unit-testable in isolation. The
     helper parses `validator_payload["stdout"]` (with the same `parse_error`
     flag), normalises reason codes, sanitizes stderr through
     `sanitize_text_for_output`, and emits the structured block to stderr
     — including the path to the persisted `PRELIVE_VALIDATOR_RESULT.json`
     artifact — before the surrounding caller terminates via
     `parser.error(...)` with a short final message. This adds
     stdout/stderr/reason-code visibility that previously was silently
     swallowed.

### `services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py`

Ten new tests, each isolated from any provider/network surface (the
validator subprocess is fully stubbed):

1. `test_format_pre_live_validator_block_includes_all_sections`
2. `test_format_pre_live_validator_block_missing_reason_codes`
3. `test_format_pre_live_validator_block_parse_error_flag`
4. `test_enforce_pre_live_validator_emits_block_on_structured_no_go`
5. `test_enforce_pre_live_validator_fails_closed_on_malformed_stdout`
6. `test_enforce_pre_live_validator_returns_payload_on_go`
7. `test_enforce_pre_live_validator_short_circuits_without_consent`
8. `test_emit_validator_first_preset_block_structured_payload`
9. `test_emit_validator_first_preset_block_malformed_stdout`
10. `test_emit_validator_first_preset_block_empty_payload`

The pre-existing four tests
(`test_should_enforce_pre_live_validator_for_live_phase_execution`,
`test_main_blocks_live_phase_when_validator_returns_no_go`,
`test_main_allows_live_phase_when_validator_returns_go`,
`test_main_skips_validator_for_dry_run`) are unchanged and still pass.

### `task-packets/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001.md`

New file describing objective, authority order, allowlist, forbidden paths,
implementation steps, validation plan, proof plan, commit plan, rollback
plan, and the live-gate preservation statement. During the refresh, the packet
artifact was corrected to include the fenced canonical JSON payload required by
`docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`, matching the
prior RTE-UX packet convention.

## What Did Not Change

- `services/repo-truth-extractor/validate_pre_live_gate_v25.py` — untouched.
- `services/repo-truth-extractor/rte_ops_surfaces.py` — untouched.
- `src/dopemux/cli.py` — untouched.
- `should_enforce_pre_live_validator` enforcement conditions — untouched.
- `build_pre_live_validator_command` — untouched.
- `enforce_live_operation_consent` — untouched.
- `DPMX_LIVE_OK` consent semantics — untouched.
- `--skip-pre-live-validator` behavior — untouched (wording preserved in the
  new `next_step` hint).
- Validator command, subprocess invocation, return-payload shape, and
  `PRELIVE_VALIDATOR_RESULT.json` persistence — untouched.
- Promptsets, schemas, provider clients, routing, pricing — untouched.
- Documentation, README, AGENTS.md, `.claude/**` — untouched.

## Before / After Failure-String Inventory

Two operator-visible failure messages changed.

### `enforce_pre_live_validator_for_execution`

**Before** (single string emitted via `logger.error("%s", exc); sys.exit(1)`):

```
Pre-live validator blocked live execution: verdict=NO_GO reason_codes=<list-or-none> output_dir=<dir-or-unknown>.[ stderr=<verbatim-stderr>]
```

**After** (multi-line block written to stderr, then a short single-line
`RuntimeError` for log compatibility):

```
Pre-live validator blocked live execution.
  verdict: NO_GO
  [parse_status: validator stdout was not parseable as JSON; treating as block (fail-closed).]
  reason_codes: MISSING_KEY, STALE_PRESCAN   # or: none reported
  output_dir: /tmp/run_abc                    # or: <unknown>
  [stderr:
    <sanitized validator stderr, line by line>]
  next_step: review the validator output above, fix the reported pre-live issues, and rerun.
```

Followed by:

```
Pre-live validator blocked live execution (verdict=NO_GO). See structured block above for details.
```

### Validator-first preset flow (secondary call site)

**Before**:

```
Validator-first preset flow blocked live execution. Run the validator, fix the reported pre-live issues, and retry. Use --skip-pre-live-validator only if you have separately reviewed the gate output.
```

(Single line from `parser.error(...)` with no verdict, no reason codes, no
output_dir, no stderr surface.)

**After**: same structured block as above written to stderr first,
including the persisted artifact path:

```
Pre-live validator blocked live execution.
  verdict: NO_GO
  [parse_status: ...]
  reason_codes: ...
  output_dir: ...
  artifact: <run_root>/PRELIVE_VALIDATOR_RESULT.json
  [stderr: ...]
  next_step: review the validator output above and the persisted artifact, fix the reported pre-live issues, then rerun. Use --skip-pre-live-validator only after a separate review of the gate output.
```

Followed by the short final `parser.error`:

```
Validator-first preset flow blocked live execution. See structured block above for details.
```

## Behavior-Preservation Attestation

- The pre-live validator's command construction, dispatch conditions, and
  operator-visible verdict semantics are preserved.
- The malformed-stdout edge case is now explicitly fail-closed. This is a
  defensive tightening of the existing fail-closed contract; it does **not**
  add any GO path that was not already a GO path before, and it does **not**
  weaken any block path. In the real validator, `returncode == 0` plus
  unparseable stdout is not observed; this codifies the safe behavior in case
  of future regressions.
- `DPMX_LIVE_OK` consent and `--skip-pre-live-validator` semantics are not
  altered.
- No code path performs provider calls, live extraction, live preflight,
  routing changes, pricing changes, or promptset/schema mutations.

## Unknowns Preserved

- **U-1**: Exact finding-ledger ids/wording from the source Opus audit bundle
  are not locally reconstructible because
  `out/rte-opus-uiux-claude-design-audit/` is absent in this checkout. The
  `HIGH-1` label used here is the valuation matrix's local approximation.
- **U-2**: The valuation matrix's `ClickException` wording is treated as
  valuation-derived. No `ClickException` is raised on the pre-live validator
  path in the actual runtime, so the wording was not adopted verbatim into
  the implementation.
- **U-3**: `rte_ops_surfaces.run_pre_live_validator` truncates the validator
  stdout to the last 4 KB before storing it in `validator_payload`. When a
  real validator emits >4 KB of JSON, the secondary call-site path will
  surface a `parse_status: validator stdout was not parseable as JSON;
  treating as block (fail-closed)` message even though the underlying cause
  is truncation. Gate behaviour remains fail-closed (correct outcome); the
  diagnostic message is the only thing that could be more precise. Out of
  scope for this packet because addressing it touches the tuple-payload
  contract in `rte_ops_surfaces.py`, which the packet keeps untouched.

## No Provider / No Live Extraction / No Live Preflight Attestation

- All validator subprocess invocations in tests are stubbed via
  `monkeypatch.setattr(runner.subprocess, "run", ...)`. No real subprocess is
  started.
- `DPMX_LIVE_OK` is set only in test scope where the helper itself is
  exercised; no provider, network, or live extraction code path is reached.
- The implementation does not introduce any new I/O, network, or provider
  call.

## Validation Performed

- `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py
  -q` — **14 passed** (4 pre-existing + 10 added).
- Embedded task-packet JSON validated against
  `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` — **PASS**.
- `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_live_gate_terminality.py
  -q` — **39 passed** (unrelated terminality assertions still hold).
- `pytest
  services/repo-truth-extractor/tests/test_pre_live_gate_v25.py::test_default_policy_requires_direct_gemini_and_xai`
  fails on this checkout **and on clean `origin/main`** (verified by
  stashing the worktree changes and rerunning). This pre-existing failure is
  in `validate_pre_live_gate_v25.py`, which this packet does **not** modify.
  It is unrelated to the failure-shape change.
- `python -m compileall -q src services tests` — **PASS**.
- `git diff --check` — clean.
- `pre-commit run --files services/repo-truth-extractor/run_extraction_v5.py
  services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py
  task-packets/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001.md
  out/rte-ux-prelive-validator-error-shape/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001_AUDIT_NOTE.md
  proof/rte-ux/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001/PROOF.json` —
  **PASS** after the docs frontmatter hook normalized the task-packet
  frontmatter.
- Scope guard: `git diff --name-only` shows only allowlisted paths.
- Forbidden-path grep: `promptsets/`, `schemas/`, `src/dopemux/cli.py` — none
  touched.
- Future-packet grep: no references to
  `RTE-UX-PKT-RUN-HELP-PROGRESSIVE-DISCLOSURE-001`,
  `RTE-UX-PKT-UX-DOC-CLEANUP-001`, or `RTE-UX-PKT-DPMX-LIVE-OK-HINTS-001`
  outside the valuation/sequencing artifacts and this packet's task-packet
  metadata.
- Primary checkout `/Users/hue/code/dopemux-mvp` confirmed not modified
  (status set identical to session start; no edit/stage/clean operation was
  run against it).

## Confirmation Statements

- **Base used**: `origin/main` at `fbf1b5df333e815db718ec05b4bc324ebf7d9af6`
  after the packet-4 refresh.
- **Primary checkout not modified**: confirmed; remained dirty at the same
  state it was at session start.
- **PR #645 merge gate**: verified MERGED, non-draft, base = `main`, merge
  commit present, and ancestor of `origin/main`.
