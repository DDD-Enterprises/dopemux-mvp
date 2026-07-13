# Validation Receipt

Run ID: `merge-integrity-reaudit-20260713T002157Z-005`

This compact receipt records the exact commands, working directory, summarized stdout/stderr, and exit codes for this remediation. It intentionally excludes large raw output; the command index records immutable inputs and the GitHub Actions artifact references retain external audit output.

## Phase B Main Identity

Command: `git rev-parse origin/main`

Working directory: `/Users/hue/code/dopemux-merge-integrity-0001`
Exit code: `0`
Stdout: `45b5ee3f320e777111a6f00227072efeb725996b`

## Task Packet Schema

```bash
python - <<'PY'
import json
from pathlib import Path
from jsonschema import Draft7Validator

schema_path = Path('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json')
packet_path = Path('task-packets/TP-DMX-MERGE-INTEGRITY-0001R-PR1040-SUPERVISOR-REMEDIATION.json')
schema = json.loads(schema_path.read_text(encoding='utf-8'))
packet = json.loads(packet_path.read_text(encoding='utf-8'))
errors = sorted(Draft7Validator(schema).iter_errors(packet), key=lambda item: list(item.path))
if errors:
    raise SystemExit('\n'.join(error.message for error in errors))
print('task_packet_schema: PASS')
PY
```

Working directory: `/Users/hue/code/dopemux-merge-integrity-0001`
Exit code: `0`
Stdout: `task_packet_schema: PASS`
Schema SHA-256: `62abd93a27b7307e5b78aa8a46d967937e257817e41822f2edfc73162d4535ed`
Observation: the checked-in strict schema explicitly permits `execution.base_branch` and `execution.stacked_because`.

## Proof And Handoff Contract

```bash
python - <<'PY'
import json
from pathlib import Path

proof = json.loads(Path('proof/TP-DMX-MERGE-INTEGRITY-0001/PROOF.json').read_text(encoding='utf-8'))
handoff = json.loads(Path('proof/TP-DMX-MERGE-INTEGRITY-0001/HANDOFF.json').read_text(encoding='utf-8'))
required_proof = {'bundle_id', 'run_id', 'skill', 'status', 'validation_state', 'created_at', 'authoritative_artifacts', 'chain_of_custody'}
required_handoff = {'handoff_id', 'source_skill', 'target_skill', 'run_id', 'repo', 'branch', 'base_branch', 'governing_posture', 'recommended_next_step', 'authoritative_artifacts', 'chain_of_custody'}
assert not (required_proof - proof.keys())
assert not (required_handoff - handoff.keys())
assert proof['status'] == 'BLOCKED'
assert proof['validation_state'] == 'PARTIAL'
assert handoff['governing_posture'] == 'NO_GO_LIMIT_TO_ARTIFACTS_ONLY'
assert handoff['recommended_next_step'] == 'BLOCK_AND_AWAIT_FIX'
assert proof['audit_receipt']['status'] == 'FAIL'
print('proof_contract: PASS')
print('handoff_contract: PASS')
print('audit_receipt: historical FAIL; final-head receipt remains required')
PY
```

Working directory: `/Users/hue/code/dopemux-merge-integrity-0001`
Exit code: `0`
Stdout:

```text
proof_contract: PASS
handoff_contract: PASS
audit_receipt: historical FAIL; final-head receipt remains required
```

## Embedded Audit Proof

Command: `uv run --frozen python scripts/audit/validate_audit_proof.py proof/TP-DMX-MERGE-INTEGRITY-0001/PROOF.json`

Working directory: `/Users/hue/code/dopemux-merge-integrity-0001`
Exit code: `0`
Stdout: `PASS proof/TP-DMX-MERGE-INTEGRITY-0001/PROOF.json` and `Result: 1/1 PASS`.

## JSON Parse

Command: `python -m json.tool` against `PROOF.json`, `HANDOFF.json`, `EVIDENCE_MANIFEST.json`, `GITHUB_CONTROL_CAPTURE.json`, `COMMAND_INDEX.json`, and the remediation Task Packet.

Working directory: `/Users/hue/code/dopemux-merge-integrity-0001`
Exit code: `0`
Stdout: `json_parse: PASS`

## Diff Hygiene

Command: `git diff --check`

Working directory: `/Users/hue/code/dopemux-merge-integrity-0001`
Exit code: `0`
Stdout: `diff_check: PASS`

## Pre-Commit

Command: `pre-commit run --files` against all 15 remediation allowlist files changed in this slice, exactly as recorded in `COMMAND_INDEX.json#precommit`.

Working directory: `/Users/hue/code/dopemux-merge-integrity-0001`
Exit code: `0`
Stdout summary: all applicable documentation, proof, Markdown, whitespace, JSON/YAML, and embedded-audit-schema hooks passed; non-applicable hooks were skipped.
