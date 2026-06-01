# TP-DMX-AUTOREVIEW-HARDEN-401 Validation Output

Generated: 2026-06-01T00:54:39Z

## PASS

- `python -m json.tool task-packets/generated/TP-DMX-AUTOREVIEW-HARDEN-401.json`
- `python -m jsonschema -i task-packets/generated/TP-DMX-AUTOREVIEW-HARDEN-401.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `git diff --check`
- `python scripts/audit/validate_audit_proof.py proof/TP-DMX-AUTOREVIEW-HARDEN-401/PROOF.json`
- `pre-commit run --files <TP401 changed files>`
- GitHub checks passed for refreshed PR #755 head `0dcd8ab0ac96` and refreshed PR #763 head `379017583449`.

## FAIL

- `pytest -q tests/pr_steward tests/pr_action_bridge tests/audit tests/copilot_repair tests/pr_merge_specialist tests/dopemux_cli tests/dopemux_init`
  - Exit code: 1
  - Observed: 17 failures.
  - Classification: integration branch-shape failure. The TP401 branch is based on TP303 and does not contain every parallel dependency branch.

## NOT_RUN

- External Claude Code Opus adversarial audit.
- Live governed merge execution.
- A single integrated whole-platform branch containing all dependency PR heads.
