# TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001 Repair Decisions

Packet: `TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001`
Base SHA: `c4f0c17b29f67dd949b15953f7c5e6b01ac5cbdf`
Branch: `codex/rte-costprofile-f-fullsuite-repair-001`
Source failure inventory: `proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/SERIES_VERIFICATION_REPORT.md`

## S1 Gate Evidence

- `origin/main` SHA captured in `/tmp/F_REPAIR_ORIGIN_MAIN_SHA.txt`: `c4f0c17b29f67dd949b15953f7c5e6b01ac5cbdf`.
- PR #701 merge commit `9b98b3c47c986f3dc6037cfa9cac663690a50cbf` is an ancestor of `origin/main`.
- F-VERIFY-001 `SERIES_VERIFICATION_REPORT.md` is present on `origin/main`.
- F-VERIFY-001 `PROOF.json` is present on `origin/main` and parses as JSON.
- `task-packets/INDEX.md` row for `TP-RTE-COSTPROFILE-F-VERIFY-001` contains `NOT_VERIFIED_ACCEPTED_AS_EVIDENCE`.
- E-series ancestry caveat captured from F-VERIFY-001 evidence: PR #690's GitHub merge commit is not a direct ancestor of the normalized F base, but equivalent E7 commits are recorded in the F-VERIFY report.

## PAL S2 Record

- Operator updated the PAL execution constraint during S11/S12 recovery:
  do not use Gemini; redo PAL with working non-Gemini models.
- PAL analyze redo: `gpt-5-codex`, internal/local workflow, completed. It
  preserved the 26-failure classification and kept Cluster A/B/C/E/F repairs
  tied to runtime/source evidence while leaving Cluster D as explicit
  `TP-RTE-WALKER-006` deferrals.
- PAL thinkdeep redo: `gpt-5-codex`, internal/local workflow, completed. It
  supported preserving legacy routing visibility while adding canonical
  `cost_profile`; it flagged removal of legacy fields as operator-breaking
  within this packet.
- PAL consensus redo: `gpt-5-codex` (`for`) and `gpt-5` (`against`) completed
  successfully. Both supported option (i): dual emission of top-level
  `cost_profile` plus legacy routing projections for a compatibility window,
  provided legacy projections remain documented compatibility metadata and
  follow-up work handles eventual deprecation.
- Consensus caveat: the `gpt-5` against stance also suggested a central
  no-Gemini runtime routing guard. That is recorded as out of scope for this
  packet because the operator's current no-Gemini instruction governs PAL/tool
  model choice, not RTE runtime route policy. Runtime route policy remains
  governed by packet scope and existing CostProfile/model-map authority.

## Target Policy / Cost Profile Decision

Decision: option (i), emit both fields.

`cost_profile` is the canonical operator-visible field. The legacy `target_policy` / `routing_policy` projection remains emitted for one compatibility window and is documented as deprecated. Runtime evidence supports this decision:

- `services/repo-truth-extractor/run_extraction_v5.py` defines `COST_PROFILES`, maps legacy `--routing-policy` values through `LEGACY_ROUTING_POLICY_TO_COST_PROFILE`, and backfills `args.routing_policy` from the resolved profile so downstream code keeps working.
- Parser help already marks `--routing-policy` as deprecated in favor of `--cost-profile`.
- F-VERIFY-001 observed `target_policy=balanced_openrouter` and missing `cost_profile`; adding `cost_profile` fixes the operator visibility gap without breaking existing consumers of the legacy field.

Rejected alternatives:

- Option (ii), `cost_profile` supersedes `target_policy` by removing the latter: rejected as operator-breaking and broader than this repair packet.
- Option (iii), remove `target_policy` in favor of `cost_profile` only: rejected for the same compatibility reason and because runtime still uses the legacy projection internally.

## Failure Classification

| ID | Observed failure | Cluster | Classification | Authority used | Repair direction |
| --- | --- | --- | --- | --- | --- |
| F01 | `test_code_prescan_truthfulness.py` missing `imports` | D | ambiguous / non-cost-profile | F-VERIFY-001 report; prescan tests | Investigate within allowlist. Repair test/runtime only if failure is local to allowed prescan surfaces; otherwise executable deferral to follow-up TP. |
| F02 | `test_code_prescan_truthfulness.py` missing `api_surfaces` | D | ambiguous / non-cost-profile | F-VERIFY-001 report; prescan tests | Same as F01. |
| F03 | `test_code_prescan_truthfulness.py` missing `symbols` | D | ambiguous / non-cost-profile | F-VERIFY-001 report; prescan tests | Same as F01. |
| F04 | `test_intelligence_routing_integration.py` expected `gpt-4o`, observed `gpt-5.4-mini` | A | stale test expectation | `COST_PROFILES`; model-map v3 route semantics | Update expected routing to resolved cost-profile behavior; do not revert routing code without contrary runtime evidence. |
| F05 | `test_phase_d_contract_hardening.py` D-step contract lane expected Gemini, observed OpenRouter `openai/gpt-5.3-codex` | A | stale test expectation | model-map v3; strict contract lane routing | Update expectation to OpenRouter strict contract lane where model-map v3 declares it. |
| F06 | `test_pre_live_gate_v25.py` expected default policy `balanced_openrouter`, observed `cost` | A | stale test expectation | cost-profile defaults; pre-live gate contract | Align expected target policy with resolved cost-profile/preset behavior while preserving route readiness categories. |
| F07 | `test_prescan_contracts.py` expected top-level `duplicate_assessments` | D | ambiguous / non-cost-profile | F-VERIFY-001 report; prescan contract tests | Investigate; defer if schema ownership is outside this packet. |
| F08 | `test_prescan_e2e_smoke.py` incremental cache reuse expected 2, observed 0 | D | ambiguous / non-cost-profile | F-VERIFY-001 report; prescan incremental tests | Investigate; repair deterministic cache semantics if local, otherwise defer with executable marker. |
| F09 | `test_prescan_incremental.py` incremental/full semantic output mismatch | D | ambiguous / non-cost-profile | F-VERIFY-001 report; prescan incremental tests | Investigate; repair if local and allowed, otherwise defer with executable marker. |
| F10 | `test_pricing_coverage.py` expected `xai/grok-4.20` unknown, observed priced | B | stale test expectation | static pricing coverage report; existing pricing registries | Update expected coverage to current static pricing authority if registry contains the model. |
| F11 | `test_promptpack_v1_v2.py` D0/D1 contract lane provider expected Gemini, observed OpenRouter | A | stale test expectation | promptpack contract metadata; model-map v3 | Update expected provider/routes to model-map v3 strict contract metadata. |
| F12 | `test_reporting_seam.py` `write_step_metrics_snapshot` string deps lacks methods | E | stale test fixture / seam expectation | `rte_reports.py`; `reporting.py`; seam tests | Update fixture to validate structured dependency delegation, not a string deps placeholder. |
| F13 | `test_reporting_seam.py` `write_run_manifest` string deps lacks methods | E | stale test fixture / seam expectation | `rte_reports.py`; `reporting.py`; seam tests | Same as F12. |
| F14 | `test_rte_v5_characterization.py` import `dopemux.cli` fails through `litellm` path | F | code drift / import-time fragility | `pyproject.toml`; `src/dopemux/cli.py`; `src/dopemux/litellm_proxy.py` | Lazily load LiteLLM proxy helpers so `PYTHONPATH=src import dopemux.cli` succeeds without masking actual proxy invocation failures. |
| F15 | second `test_rte_v5_characterization.py` `dopemux.cli` import failure | F | code drift / import-time fragility | same as F14 | Same as F14. |
| F16 | `test_run_extraction_v3_model_routing.py` route contract expectation 1 failed | A | stale test expectation | v3 runner routing contract; model-map v3 / E-series route migration | Update assertion to current resolved route. |
| F17 | `test_run_extraction_v3_model_routing.py` route strict expectation failed | A | stale test expectation | v3 runner routing contract; model-map v3 / E-series route migration | Update assertion to current resolved route. |
| F18 | `test_run_extraction_v3_model_routing.py` route fallback expectation failed | A | stale test expectation | v3 runner routing contract; model-map v3 / E-series route migration | Update assertion to current resolved route. |
| F19 | `test_run_extraction_v5_benchmark_route_ownership.py` H3 strict override RuntimeError 1 | A | ambiguous route ownership contract | benchmark route ownership tests; explicit route override runtime | Prefer runtime code repair only if explicit H3 route override is supposed to apply outside Phase A; otherwise update/defer the H3 assertion with rationale. |
| F20 | `test_run_extraction_v5_benchmark_route_ownership.py` H3 strict override RuntimeError 2 | A | ambiguous route ownership contract | same as F19 | Same as F19. |
| F21 | `test_run_extraction_v5_cost_cap.py` missing pricing for active targets | B | pricing catalog/test drift | `initialize_spend_tracker`; pricing registry | Add missing pricing entries only when existing static catalog authority supports them; otherwise revise active target expectations. |
| F22 | `test_run_extraction_v5_live_readiness.py` benchmark-owned route readiness expected OpenAI only, observed broader routes | A | stale test expectation or route-ownership scope drift | benchmark ownership payload; route readiness summary | Align route readiness with benchmark-owned lane scope if code already produces deterministic required-active-route categories. |
| F23 | `test_run_extraction_v5_operator_safety.py` doctor/preflight exit code 2 | A | ambiguous readonly/operator contract | operator safety tests; runner readonly paths | Investigate exact failure; repair runtime only if readonly command behavior regressed. |
| F24 | `test_run_extraction_v5_operator_safety.py` route readiness required-env mismatch 1 | A | stale test expectation | cost-profile route readiness summary | Update expected categories to current resolved cost-profile behavior. |
| F25 | `test_run_extraction_v5_operator_safety.py` route readiness required-env mismatch 2 | A | stale test expectation | cost-profile route readiness summary | Same as F24. |
| F26 | `test_run_extraction_v5_operator_safety.py` strict override RuntimeError | A | ambiguous route ownership contract | explicit route override runtime | Same decision basis as F19/F20. |

## Cluster D Deferral Record

Follow-up TP: `TP-RTE-WALKER-006`.

S6 runtime evidence shows the remaining Cluster D failures are prescan schema,
summary payload, and incremental cache/semantic parity failures. They do not
trace to CostProfile F routing, pricing, print-config, reporting seam, or CLI
import behavior. The failing assertions were converted to executable
`xfail` markers with this follow-up TP ID so the full suite records the
deferral explicitly instead of masking it as a normal pass.

| Test | Observed failure | Deferral reason |
| --- | --- | --- |
| `test_code_prescan_emits_dotted_relative_python_imports` | `CodePrescan.analyze_file()` no longer emits top-level `imports` for the direct fixture call. | Prescan schema/runtime output contract belongs to `TP-RTE-WALKER-006`, not CostProfile F. |
| `test_code_prescan_api_surface_detection_avoids_substring_false_positives` | Direct fixture call no longer emits top-level `api_surfaces`. | Same prescan schema/runtime contract deferral. |
| `test_code_prescan_arrow_function_signatures_match_symbol_coverage` | Direct fixture call no longer emits top-level `symbols`. | Same prescan schema/runtime contract deferral. |
| `test_optimize_payload_includes_prior_pass_summaries` | `duplicate_assessments` now appears under nested `dedup_results`, not top-level payload text. | Prescan summary payload schema deferral. |
| `test_prescan_real_repo_full_and_incremental_smoke` | Warm incremental run reports `cached_code_analysis_reused == 0`, expected `2`. | Prescan incremental cache semantics deferral. |
| `test_incremental_outputs_match_full_run_semantically` | Incremental and full normalized outputs differ under prescan intelligence payload. | Prescan incremental/full parity deferral. |

## Cluster E Reporting Seam Decision

Decision: repair the runtime wrapper seam in
`services/repo-truth-extractor/run_extraction_v5.py`.

The test fixtures patch the module-level compatibility aliases
`reporting_write_step_metrics_snapshot` and `reporting_write_run_manifest`.
The wrappers were bypassing those aliases and calling the imported RTE writer
functions directly, so the seam could not be isolated. The repair changes only
the wrapper call target; default production behavior remains the same because
the aliases still point to the same RTE writer functions unless a test replaces
them.

## Cluster F Import Repair Decision

Decision: repair at the import/lazy-surface layer and keep the dependency
failure visible at command invocation time.

`PYTHONPATH=src python -c "import dopemux.cli"` failed because `dopemux.cli`
imported LiteLLM-backed command stacks, mobile/tmux command stacks, and
`psutil`-backed health code at module load. The repair keeps `dopemux.cli`
importable in a clean `src/` layout by installing unavailable command wrappers
when optional command stacks cannot import, while commands that need those
dependencies still fail explicitly if invoked without the dependency.

`test_truth_run_finds_v5_runner_directly` only needs
`extract_commands._find_runner()`. Because `extract_commands.py` is outside this
packet's allowlist and imports the mobile hook stack at module load, the test now
stubs that unrelated hook module explicitly instead of importing the LiteLLM
proxy chain just to exercise runner-path resolution.

## S9 Residual OpenRouter Preflight Decision

Operator authorization expanded the allowlist narrowly to
`services/repo-truth-extractor/tests/test_provider_preflight_openrouter.py` for
two S9 residual failures:

- `services/repo-truth-extractor/tests/test_provider_preflight_openrouter.py::test_phase_d_provider_preflight_blocks_on_openrouter_402`
- `services/repo-truth-extractor/tests/test_provider_preflight_openrouter.py::test_phase_d_provider_preflight_is_required_when_cost_routes_include_openrouter`

Decision: update both tests as stale CostProfile/OpenRouter preflight
expectations.

Runtime evidence:

- `run_extraction_v3.collect_provider_routes(["D"], "cost")` returns providers
  `gemini`, `openai`, and `xai`; no OpenRouter route is present.
- The same Phase D route probe for `balanced_grok_openrouter`,
  `balanced_openrouter`, and `openrouter` also resolves through the JSON-managed
  D-step model map to Gemini/OpenAI/xAI routes only.
- `run_extraction_v3.phase_requires_provider_preflight("D", cfg)` returns
  `False` for the current `cost` routing policy because the implementation
  requires OpenRouter preflight only when collected Phase D routes include an
  OpenRouter provider.

The first test now proves `prepare_phase_provider_preflight()` does not probe or
write a Phase D OpenRouter preflight artifact when no OpenRouter route is
required. The second test now proves the current Phase D/cost route provider set
and the resulting `phase_requires_provider_preflight(...) is False` decision.
No runtime code was changed for this residual.

## PR #709 Review Thread Fix

- `src/dopemux/cli.py` fallback wrappers now fail closed without `KeyError`.
- Cluster D executable xfail deferrals now use `strict=True` so unexpected pass becomes a visible XPASS failure.
- No Walker/prescan runtime repair was performed.
- No live provider calls or live extraction were run.
- No CLI-specific test file was changed for this review thread because the authorized allowlist did not include a clean CLI fallback test surface; validation relies on the import probe and existing characterization tests.

## Implementation Guardrails

- Do not mark any Cluster D failure as deferred unless the test receives an executable `xfail` or `skip` marker with a follow-up TP ID before the full-suite run.
- Do not use `pytest.importorskip` for Cluster F.
- Do not remove legacy routing fields from `--print-config` in this packet.
- Any relaxed assertion must cite the runtime source that made the old assertion stale.
- Any code-only repair must be validated by at least one focused test in this packet.
