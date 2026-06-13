# Stage 4: PAL Challenge Results

## Challenge Context
We challenge the assumption that the dopemux wizard provides a safe, fully-configured launch path for v5 extraction.

## Assertions
1. Wizard command assembly drops the `max-cost` safety cap.
2. Live validation gates are not enforced by the wizard's `upgrades run` command.

## Verification
- Confirmed via `src/dopemux/ux/wizard/extraction.py` line 29: `_build_wizard_phase_command` only appends `--routing-policy`, `--resume`, `--ui`, `--prescan-dir`, `--skip-prescan`, and `--execute`.
- It completely lacks `--max-cost` or `--validate-live`.

## Conclusion
The wizard is structurally unsafe for live launch until command assembly enforces `max-cost` and `validate-live` parity with the raw CLI.
