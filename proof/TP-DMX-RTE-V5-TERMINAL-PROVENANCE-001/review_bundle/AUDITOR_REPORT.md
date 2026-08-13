# Controlling Audit Report — TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001

**Auditor tool**: `grok-cli` (`~/.grok/bin/grok`, headless single-turn, `--permission-mode dontAsk`)
**Auditor model (API-reported, authoritative)**: `grok-4.5-build` → represented in the embedded-audit proof as `grok-4.5` per the admitted schema pairing (PR #1228; `-build` is a usage/telemetry label, not a requestable model id).
**Auditor model (self-reported in transcript)**: inconsistent — "Grok 4.6", "Grok-2", "Grok 4.5" at different points. Per packet §15, runtime/provider-reported identity outranks model prose self-report; `grok-4.5-build` (API telemetry) is treated as authoritative.
**Commit audited (C1)**: `67f22b4829` on `tp/DMX-RTE-V5-TERMINAL-PROVENANCE-001`
**Independence**: genuinely independent — different vendor/family/runtime from the implementer (Claude Code / Sonnet 5) and from the prior supporting review (GPT-5-pro / OpenAI).
**Method**: direct filesystem read of the actual worktree (no paraphrase relay) — the auditor ran its own `git diff`, `grep`, and file reads inside `/Users/hue/code/dopemux-mvp/.worktrees/TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001` and self-corrected twice mid-session after finding evidence that contradicted an earlier draft verdict.
**Cost**: $0.5735, 15 turns, 91,461 input tokens / 14,375 output tokens.

## Verdict: PASS_WITH_RISKS

## Claim-by-claim result

| Claim | Result |
|---|---|
| Terminal exit solely from rollup `run_status`; only `OK` → 0 | **Confirmed** |
| Batch outcome cannot report success for listed material failures | **Confirmed** |
| Identity gate before phase loop + doctor persist + pre-live blocker | **Confirmed** |
| Identity gate before *any* canonical evidence write | **Not fully true** (see residual risk 1) |
| Legacy int-returning `integrate_batch_results_with_webhook` untouched | **Confirmed** (byte-identical body vs `origin/main`) |
| `--doctor` persist=True gap (found by the prior GPT-5-pro review) closed in C1 | **Confirmed**, verified in source + the two new `test_s9_*` tests |
| No secret/credential leakage in new code/tests | **Confirmed** |
| New tests assert real behavior, not tautological | **Mostly yes**; two noted as weaker (structural/source-order guards, and one persist=False test that checks outcomes but doesn't spy that the identity function is never called) |

## Explicit residual risks (all classified non-blocking by the auditor)

1. **`RUN_MANIFEST.json` / `RUNNER_IDENTITY.json` are written via the ungated `get_git_sha()` before `required_execution_source_identity()` runs** in `main()`'s phase-execution path (`write_run_manifest` ~line 23798, `write_runner_identity` ~line 23803, gate ~line 24158). A failed identity check still leaves `git_sha: "UNKNOWN"` on those two files on disk, even though `RUN_MANIFEST.json`'s `run_status` is subsequently overwritten to `FAILED`/`source_identity_unproven` by `update_run_manifest_startup_failure`. This is the same nuance the implementer self-disclosed in their original report (satisfies invariant 9's "identity resolved before terminal evidence is *accepted as authoritative*" reading, not a stricter "before any write" reading) — independently rediscovered here, not new.
2. **`write_confidence_ramp_artifacts` (triggered by `--preset`) can write `CERTIFICATION_RESULT.json` before the phase-loop identity gate.** Lower severity than the closed doctor gap: the auditor verified `write_certification_result`'s payload does not itself embed a `git_sha` field for this call path (it embeds `topology_payload` — the doctor-full payload's `runner.git_sha` — only when called from the now-gated doctor path).
3. **The audit-prompt's own wording ("before any canonical evidence write") overstates the implementation** — the actual guarantee is "before phase-execution completes and before doctor-persist writes," not "before every run-root file write." A wording/scope precision issue in how the fix was described to the auditor, not a code defect beyond risks 1–2.
4. **Base-SHA note**: at audit time this worktree's `origin/main` ref had moved past the packet's recorded execution base (`6626aa9a58`) to a newer tip (`75b4cfc581`) due to normal upstream repo activity during this session. The RTE branch itself was correctly created from `6626aa9a58` and is unaffected; this is expected drift per packet §23, not a defect.
5. **Structural (`inspect.getsource`) tests for `main()`'s control flow are source-order guards, not full runtime end-to-end execution** — a known, disclosed limitation (main() is several thousand lines; true e2e simulation is impractical offline), already acknowledged in the implementer's own report.

The auditor's own summary: *"None of these re-open the original 'shell exit 0 on semantic FAIL', 'batch bare-int always ≥0 → exit 0', or 'doctor persist certifies with unproven identity' defects."*

## Recommended (non-blocking) follow-on

Move `required_execution_source_identity()` earlier — before `write_run_manifest` / `write_runner_identity` / the preset confidence-ramp writes — or rewrite/delete those artifacts on identity failure, to fully satisfy a strict "before any write" reading. Not required for this packet's PASS_WITH_RISKS disposition.

## Raw transcript

Full raw JSON output (including the auditor's self-correcting reasoning trace) preserved at `proof/TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001/GROK_AUDIT_OUTPUT.json`. Audit prompt at `proof/TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001/GROK_AUDIT_PROMPT.md`.
