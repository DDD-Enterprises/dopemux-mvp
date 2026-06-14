# Stage 1: PAL Challenge Results

## Challenge Context
We map the authority of cost profiles, wizard policies, and runtime defaults.

## Assertions
1. Wizard labels `balanced_openrouter` as "v5 default".
2. `run_extraction_v5.py` specifies `cost` as default.

## Verification
- Confirmed via `read_file` on `run_extraction_v5.py` line 495: `DEFAULT_ROUTING_POLICY = "cost"`
- Confirmed via `read_file` on `validate_pre_live_gate_v25.py` line 37: `DEFAULT_TARGET_POLICY = "balanced_openrouter"`
- Confirmed via `read_file` on `src/dopemux/ux/wizard/cost_profiles.py` line 99: `balanced_openrouter` labeled as `v5 default`.

## Conclusion
The mismatch is real and poses a launch hazard: the wizard and validator assume one policy (`balanced_openrouter`), while the engine defaults to a different, cheaper policy (`cost`). The system lacks a single source of truth for the default launch profile.
