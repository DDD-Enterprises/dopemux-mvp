# TP-CODEX-RTE-V5-COLLECT-AND-HARDEN-20260401

## Scope executed

Stage 1 was completed on branch `codex/rte-v5-collect-and-harden-20260401` from current `main`.

- Consolidated prompt, worktree, branch, and stash findings into:
  - `docs/05-audit-reports/repo-truth-extractor-v5-prelive-consolidated-2026-04-01.md`
- Recorded prompt authority and collection decisions in:
  - `docs/05-audit-reports/repo-truth-extractor-v5-prompt-authority-decision-2026-04-01.md`
- Accepted no wholesale promptset imports from drift branches or worktrees.

Stage 2 implemented the bounded pre-live hardening scope only.

- Repaired `R0` extraction procedure numbering and added scan-only numbering hygiene detection.
- Made spend ledger pricing model-aware with explicit `baseline_v1_fallback` unknown-model policy.
- Mapped and hardened spend accounting at the active v5 runtime boundaries:
  - sync requests
  - S_INT prompt executor
  - batch submit projection gate
  - batch watch accumulation
  - async R submit projection gate
  - async R finalize accumulation
- Added visible warnings for lossy truncation salvage.
- Added sidefill scalar conflict reporting without changing deterministic merge order.
- Added degraded upstream dependency warnings for `R` and `S`.
- Added `--list-phases`.
- Improved `DPMX_LIVE_OK` discoverability in help and live-consent errors.

## Validation summary

Passed:

- `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/lib/spend_ledger.py services/repo-truth-extractor/lib/structured_output_contracts.py scripts/repo_truth_extractor_promptset_audit_v4.py`
- `pytest -q services/repo-truth-extractor/tests/test_promptset_v4_lint.py services/repo-truth-extractor/tests/test_run_extraction_v5_promptset_truth.py services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py services/repo-truth-extractor/tests/test_v5_observability_improvements.py`
- `python services/repo-truth-extractor/extraction_hygiene.py scan`
- `python services/repo-truth-extractor/run_extraction_v5.py --list-phases`
- `python services/repo-truth-extractor/run_extraction_v5.py --phase A --dry-run --print-config --run-id tp_collect_harden_a_cfg`

Expected/recorded non-green validations:

- `python services/repo-truth-extractor/run_extraction_v5.py --phase R --dry-run --run-id tp_collect_harden_r_dry`
  - failed because `R` now emits explicit degraded dependency errors when required upstream norm artifacts are absent
- `python services/repo-truth-extractor/validate_pre_live_gate_v25.py`
  - verdict `NO_GO`
  - reason codes:
    - `CONTRACT_MAP_NONDETERMINISTIC`
    - `ONLINE_PREFLIGHT_FAILURE`
    - `PAL_REQUIRED_UNAVAILABLE`
    - `REQUIRED_API_KEY_MISSING`
- `pytest -q services/repo-truth-extractor/tests/`
  - still fails in older `run_extraction_v3` coverage and related legacy surfaces outside this packet

## Remaining drift called out

- `model_map.yaml` still warns about steps outside repo-truth-map JSON scope, including `G5`, `Q11`, `R*`, `S*`, and `Z1`.
- Phase `S` overlap with `phase_s` remains unresolved; this packet aligned current runner truth but did not rewrite registry authority.
- Validator remains `NO_GO` because active-route PAL files and online preflight evidence are still missing in this checkout.
- Full extractor suite still contains unrelated `run_extraction_v3` failures; this packet did not backport v5 changes into v3.
