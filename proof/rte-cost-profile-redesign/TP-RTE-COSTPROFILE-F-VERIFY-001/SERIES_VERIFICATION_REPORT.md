# TP-RTE-COSTPROFILE-F-VERIFY-001 Series Verification Report

Status: NOT_VERIFIED

## Verification Point

- Worktree: `/Users/hue/.codex/worktrees/rte-costprofile-e9-tests-002`
- Branch: `codex/rte-costprofile-f-verify-001`
- PR: https://github.com/DDD-Enterprises/dopemux-mvp/pull/698
- First proof commit: `67749b94d5084c9a667501cb16f60ee2ffcbe882`
- Base branch: `origin/claude/goofy-haibt-fc568e`
- Base SHA: `6ecb72de3c089867bcd64dd8302fb68ba8d10980`
- Merge base for cumulative series diff against `origin/main`: `21b48ee10f9b3db69162fa84c32c5532a29d64b3`
- Cumulative verification range: `21b48ee10f9b3db69162fa84c32c5532a29d64b3..6ecb72de3c089867bcd64dd8302fb68ba8d10980`
- Cumulative range commit count: 31
- F scope: verification/proof only; no production code edits.

## Packet / PR Evidence

| Packet | PR | GitHub merge commit | Ancestor of F base | Notes |
| --- | --- | --- | --- | --- |
| TP-RTE-COSTPROFILE-E3-CONTRACTS-001 | #687 | `fbaebabe41dda37e57f462ae5193b4ac8d637f0c` | yes | Merged 2026-05-24T06:21:18Z |
| TP-RTE-COSTPROFILE-E4-FINISH-001 | #688 | `53a2ef10edf73d8cbca0271ef1afaee53d93ef9e` | yes | Merged 2026-05-24T13:34:54Z |
| TP-RTE-COSTPROFILE-E7-LADDERS-FAILOVER-001 | #690 | `d7c4c31d7123cfc433df50512b0bffb2c538adee` | no | Normalized equivalent E7 commits are present in the F base: `b1f87ff17`, `f23520728`, `bd1ee85ba`, `36bb2dc62`, `9333d6b11`. |
| TP-RTE-COSTPROFILE-E8-YAML-V3-001 runtime fix | #694 | `e236cde12c4d0848431da62fdbd0b0f93d511e8b` | yes | Merged 2026-05-24T16:00:46Z |
| TP-RTE-COSTPROFILE-E9-RUNTIME-SPEND-OPTIMIZERS-001 | #695 | `c36515fdfd36b858219b097a45c4d81fbcbe1a69` | yes | Merged 2026-05-24T16:33:02Z |
| TP-RTE-COSTPROFILE-E9-ROUTE-OPTIMIZER-METADATA-001 | #696 | `4cbebce6dcf5675aa8e381263ece1cfe8bf6eafb` | yes | Merged 2026-05-24T18:27:33Z |
| TP-RTE-COSTPROFILE-E9-TESTS-001 | #697 | `6ecb72de3c089867bcd64dd8302fb68ba8d10980` | yes | Merged 2026-05-24T18:49:46Z |

## Validation Results

### Full RTE Pytest

Command:

```bash
RTE_DISABLE_LIVE_LLM_IN_TESTS=1 python -m pytest services/repo-truth-extractor/tests --tb=short -v
```

Result: FAIL, exit code 1.

Observed summary:

- 26 failed
- 1323 passed
- 2 skipped
- 3 xfailed
- 1 warning
- Runtime: 223.60s

Failure inventory:

- `test_code_prescan_truthfulness.py`: 3 KeyError failures for missing `imports`, `api_surfaces`, and `symbols`.
- `test_intelligence_routing_integration.py`: expected `gpt-4o`, observed `gpt-5.4-mini`.
- `test_phase_d_contract_hardening.py`: D-step contract lane expected Gemini, observed OpenRouter `openai/gpt-5.3-codex`.
- `test_pre_live_gate_v25.py`: expected default policy `balanced_openrouter`, observed `cost`.
- `test_prescan_contracts.py`: expected top-level `duplicate_assessments`.
- `test_prescan_e2e_smoke.py`: incremental cache reuse expected 2, observed 0.
- `test_prescan_incremental.py`: incremental/full semantic output mismatch.
- `test_pricing_coverage.py`: expected `xai/grok-4.20` coverage `unknown`, observed `priced`.
- `test_promptpack_v1_v2.py`: expected D0/D1 contract lane provider Gemini, observed OpenRouter.
- `test_reporting_seam.py`: two reporting wrapper failures due `str` deps object missing reporting dependency methods.
- `test_rte_v5_characterization.py`: two failures importing `dopemux.cli` because `litellm` is not installed in this test context.
- `test_run_extraction_v3_model_routing.py`: three route contract/strict/fallback expectations failed.
- `test_run_extraction_v5_benchmark_route_ownership.py`: two strict override RuntimeErrors for H3 OpenRouter route.
- `test_run_extraction_v5_cost_cap.py`: missing pricing coverage for active targets `gemini/gemini-3.5-flash`, `openai/gpt-5.4-mini`, `xai/grok-4-fast`.
- `test_run_extraction_v5_live_readiness.py`: benchmark-owned route readiness expected only OpenAI, observed Gemini/OpenAI/xAI.
- `test_run_extraction_v5_operator_safety.py`: doctor/preflight exit code 2 plus route readiness required-env mismatches and strict override RuntimeError.

### Promptset V3 Audit

Command: inline Python using `rte_promptset.audit_model_map_v3`.

Result: PASS, exit code 0.

Observed:

- `version=3.0`
- `steps=136`
- used tags: `control_plane`, `long_context`, `security_sensitive`
- `override_count=6`
- override steps: `C10`, `S12`, `T0`, `T1`, `T3`, `Z0`
- structural/security-sensitive steps: 4
- structural/security-sensitive with `capability_tier=critical`: 4
- `failure_count=0`

### Bounded Config Probe

Command:

```bash
RTE_DISABLE_LIVE_LLM_IN_TESTS=1 python services/repo-truth-extractor/run_extraction_v5.py --phase A --step A2 --run-id f_verify_print_config --output-root /tmp/rte-f-verify-print-config --cost-profile value-default --print-config
```

Result: PASS_WITH_FINDING, exit code 0.

Observed:

- `--execute` was not used.
- Output `git_sha` is `6ecb72de3c089867bcd64dd8302fb68ba8d10980`.
- Output `target_policy` is `balanced_openrouter`.
- Strict route logs show OpenRouter `openai/gpt-5.3-codex` for A0/A1/A11/A12/A13.
- Route readiness shows required active routes for `OPENAI_API_KEY` and `OPENROUTER_API_KEY`.
- The emitted JSON does not contain a `cost_profile` field, so the packet cannot claim the requested profile is visible in the operator config surface.

## PAL Results

- PAL analyze/chat: NOT_VERIFIED is the only supportable status; failed suite and missing `cost_profile` emission are hard blockers.
- PAL thinkdeep: NOT_VERIFIED proof plus follow-up packets is the correct audit boundary; in-place production fixes would violate F scope.
- PAL challenge: challenged both the NOT_VERIFIED disposition and the choice to still open a proof PR. The governing packet and AGENTS.md support committing/pushing a proof-only PR while making it clear that the PR is failed evidence, not readiness.
- PAL codereview: critical blocker for full-suite failure; high blocker for missing `cost_profile` emission; medium note about normalized stack SHA ancestry.
- PAL precommit: safe to commit only as failed verification evidence after proof/checksum validations; not safe to mark verified or run live execution.

## Verdict

The series is NOT_VERIFIED.

Do not run live `--execute` from this verification result. The evidence supports only a failed final gate.

## Follow-Up Packet Needed

Recommended follow-up packet name: `TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001`.

Minimum scope for that follow-up:

- Reconcile cost-profile route expectations across v3/v5 contract tests, pre-live gate defaults, route readiness summaries, pricing coverage, and promptpack D-step contract metadata.
- Add `cost_profile` to the `--print-config` emitted JSON or deliberately update the operator contract and tests if a different visibility surface is intended.
- Repair or explicitly separate non-cost-profile full-suite failures: prescan truthfulness/incremental semantics, reporting seam deps contract, and `litellm` import/test-environment dependency.
- Re-run the full RTE suite and repeat F verification after repairs.

## NOT_RUN

- Live LLM/provider calls.
- `--execute` bounded lane.
- Provider/account authentication.
- Production fixes in F.

## Residual Risk / UNKNOWN

- The full-suite failure set was observed on the post-E9 stacked base before any F production edits, but each failure was not individually git-blamed to its originating packet.
- PR #690's GitHub merge commit is not a direct ancestor of the normalized F base; equivalent E7 commits are present and recorded above.
- `origin/main` has advanced independently from the stacked verification base; final stack normalization remains a separate merge concern.
