# Stage 1: Authority Map for Launch Policy and Cost Profiles

Observed from runtime code on branch `audit/rte-cost-profiles-ladders-wizard-gemini-001`.

## Canonical routing writer

- `services/repo-truth-extractor/run_extraction_v5.py`
  - `DEFAULT_ROUTING_POLICY = "balanced_openrouter"`
  - owns `ROUTING_LADDERS`, `ACTIVE_ROUTING_LADDERS`, `ROUTING_POLICY_GUIDE`
  - owns CLI `--routing-policy` choices and `--max-cost-usd`

## Validator target policy

- `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
  - `DEFAULT_TARGET_POLICY = "balanced_openrouter"`
  - `DEFAULT_TARGET_PROFILE = "P00_GENERIC"`

## Preset rewrites

- `services/repo-truth-extractor/rte_ops_surfaces.py`
  - `apply_first_live_preset(...)` rewrites `args.routing_policy = "cost"` when `--routing-policy` is absent
  - `apply_staged_safe_preset(...)` does the same
  - this is a preset-layer override, not the base runtime default

## Dopemux launch surfaces

- `src/dopemux/commands/extract_commands.py`
  - `dopemux extract truth-run --routing-policy` defaults to `balanced_openrouter`
  - forwards directly toward v5 execution

- `src/dopemux/cli.py`
  - `dopemux upgrades run --pipeline-version v5` defaults routing to `balanced_openrouter` when omitted
  - `dopemux upgrades validate-live --routing-policy` also defaults to `balanced_openrouter`

- `src/dopemux/commands/audit_commands.py`
  - wizard option `--routing-policy` defaults to `balanced_openrouter`

## Wizard-specific drift found before patch

- `src/dopemux/ux/wizard/stages.py`
  - `WizardState.selected_policy` default was `cost`
  - this disagreed with `WizardRunner(... routing_policy="balanced_openrouter")`

- `src/dopemux/ux/wizard/cost_profiles.py`
  - carried a static route/pricing snapshot that diverged from the runner
  - treated “cost profile” as a UX label for the selected routing policy

## Authority conclusion

- Directly observed:
  - base runtime default is `balanced_openrouter`
  - first-live and staged-safe presets intentionally coerce omitted policy to `cost`
- Inferred from code structure:
  - preset-to-`cost` behavior is a safety-layer override, not proof that global defaults should change
- Unknown:
  - whether operators want wizard default selection to remain implicit or become explicit-only; this is a product/policy decision, not proven by current code alone
