# Stage 4: Wizard Dependency and Command Assembly Audit

Observed from code after the bounded stabilization patch.

## Dependency safety

- `pyproject.toml` declares `questionary>=2.0.1`.
- Interactive wizard modules import safely without `questionary`; runtime interaction loads it lazily via `src/dopemux/ux/questionary_support.py`.
- `tests/unit/test_wizard_interactivity.py` covers import-without-questionary behavior.

## Command assembly truth

- Prior defect:
  - `src/dopemux/ux/wizard/extraction.py` built `dopemux upgrades run ... --max-cost --validate-live --skip-hygiene`
  - `src/dopemux/cli.py` did not define those flags for `upgrades run`
  - result: wizard could assemble an operator-visible command that the target CLI would reject

- Current behavior:
  - wizard now calls the canonical runner directly:
    - `services/repo-truth-extractor/run_extraction_v5.py`
  - forwarded flags are code-backed:
    - `--phase`
    - `--run-id`
    - `--partition-workers`
    - `--routing-policy`
    - `--promptset-root`
    - `--ui rich`
    - `--resume`
    - `--max-cost-usd` when set
    - `--prescan-dir` and `--skip-prescan` when imported prescan exists
    - `--execute`

## Validator and hygiene truthfulness

- Validator:
  - wizard no longer claims a separate `--validate-live` command flag
  - canonical runner already enforces the pre-live validator for live phase execution

- Hygiene:
  - wizard no longer forwards a nonexistent `--skip-hygiene` flag to the runner
  - current skip-hygiene toggle is wizard-local UI state only and now emits an explicit warning instead of pretending downstream support exists

## Cost-profile truth source

- Prior defect:
  - wizard cost selection maintained a stale route/pricing snapshot
- Current behavior:
  - wizard reads `ROUTING_LADDERS` from `services/repo-truth-extractor/run_extraction_v5.py`
  - wizard reads pricing data from `config/pricing.yaml`
  - route/cost preview is now sourced from canonical repo truth rather than a forked snapshot

## Verdict

- `PASS` for import safety
- `PASS` for command assembly truthfulness after patch
- `PARTIAL` for operator semantics:
  - skip-hygiene remains exposed as a wizard option even though there is no matching canonical runner flag
  - explicit operator copy now reflects that limitation instead of fabricating support
