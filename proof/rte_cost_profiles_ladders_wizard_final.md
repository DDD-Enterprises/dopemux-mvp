# RTE Cost Profiles, Ladders, and Wizard Final Audit

## Change scope

- Stabilized wizard cost-profile truth source.
- Stabilized wizard launch command assembly.
- Added machine-readable launch-profile metadata to validation output.
- Improved plain/rich validation UI parity for launch-profile evidence.

## Directly observed fixes

- `src/dopemux/ux/wizard/cost_profiles.py`
  - no longer maintains its own ladder snapshot
  - reads `ROUTING_LADDERS` from `services/repo-truth-extractor/run_extraction_v5.py`
  - reads pricing from `config/pricing.yaml`

- `src/dopemux/ux/wizard/extraction.py`
  - no longer builds unsupported `dopemux upgrades run ... --max-cost --validate-live --skip-hygiene`
  - now invokes the canonical v5 runner directly with supported flags
  - warns explicitly when wizard-local toggles do not map to runner flags

- `src/dopemux/commands/extractor_validation.py`
  - emits `launch_profile` metadata including routing policy, validator target policy, stage, max cost, promptset root, and model-map sha256

- `src/dopemux/commands/extractor_validation_ui.py`
  - plain output now includes launch fingerprint, model-map hash, validator target policy, max cost, and safe-to-spend line
  - rich output shows the same launch-profile evidence

## Validation performed

- `./.venv/bin/python -m pytest tests/unit/test_wizard_interactivity.py tests/unit/test_extractor_validation.py tests/unit/test_extractor_validation_ui.py -q`
  - PASS

- `./.venv/bin/python -m pytest services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_live_llm_guard.py -q`
  - PASS

- `./.venv/bin/python services/repo-truth-extractor/run_extraction_v5.py --status-json`
  - PASS

- `./.venv/bin/python services/repo-truth-extractor/validate_pre_live_gate_v25.py`
  - `NO_GO`
  - blocker 1: `services/repo-truth-extractor/tests/test_v5_resume_smoke.py` fails because `canonicalize_artifacts` is undefined in `run_extraction_v5.py`
  - blocker 2: `services/repo-truth-extractor/tests/test_promptset_v4_lint.py` fails because prescan prompt audit reports `optimize: prompt appears empty or too short`

## Verdict by launch surface

- raw `run_extraction_v5.py`: `PARTIAL`
  - routing/cost authority remains coherent enough for this audit
  - repo still has unrelated validator/smoke blockers

- `dopemux extract truth-run`: `PARTIAL`
  - not patched here
  - still a separate surface with its own hygiene semantics

- `dopemux upgrades run`: `PARTIAL`
  - not patched here
  - wizard no longer depends on unsupported flags on this surface

- wizard: `BOUNDED_GO`
  - cost/profile display and command assembly are now truthful relative to canonical repo surfaces
  - live launch remains subject to the same repo-level pre-live `NO_GO` blockers above

## PAL note

- PAL `analyze` on OpenAI provider failed with quota exhaustion during this audit.
- PAL `analyze` on Gemini completed and reinforced two conclusions already observed locally:
  - preset-to-`cost` behavior is distinct from the base runtime default
  - wizard route/pricing duplication was an unsafe fork from canonical runtime truth
