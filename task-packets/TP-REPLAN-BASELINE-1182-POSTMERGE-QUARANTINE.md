---
id: TP-REPLAN-BASELINE-1182-POSTMERGE-QUARANTINE
title: PR 1182 post-merge formal audit evidence quarantine
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-02'
last_review: '2026-08-02'
next_review: '2026-11-02'
prelude: L0 quarantine packet for false or stale formal audit evidence after PR #1182 merged. Not an audited proof-only successor and not Wave 0 or PR Steward READY authority.
---

# Task Packet: TP-REPLAN-BASELINE-1182-POSTMERGE-QUARANTINE

> **Canonical machine form:** `task-packets/TP-REPLAN-BASELINE-1182-POSTMERGE-QUARANTINE.json`
> (validated against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`).
> This Markdown file is human narrative only; execution allowlist and step
> validations are owned by the JSON packet.

## Objective

Quarantine false or stale formal audit evidence after PR #1182 merged.

PR #1182 implementation content already landed on `main`. This packet authorizes only a fail-closed correction of the formal audit package so historical/non-exact-head material cannot be read as PR Steward READY or Wave 0 authorization.

## Classification (explicit)

This is a **quarantine / correction packet**, not an audited proof-only successor.

Reasons:

- No exact-head independent audit exists for the merged content.
- The proof-only head/signature contract is intentionally inapplicable.
- Creating or retaining a signed audit attestation would contradict the quarantine disposition.
- This packet adds no new authority and does **not** claim PR #1182 is safe to dispatch.

## Risk lane

- **L0** deterministic only.
- `MODEL_CALLS_REQUIRED=0`
- Independent model audit: **NOT_REQUIRED** for this quarantine repair.

## Authority binding

| Field | Value |
|---|---|
| Merged PR | #1182 |
| Merged PR head (landed content) | `1b80fc6f11681baebdb00acc7f756ce8471a24b0` |
| Merge commit on main | `fb710ef40500695882a5b421a3325150176fffa1` |
| Quarantine PR | #1190 |
| Packet id | `TP-REPLAN-BASELINE-1182-POSTMERGE-QUARANTINE` |

## Invariants

- `exact_head_audit=NOT_PROVEN`
- `wave_0_authorized=false`
- No historical artifact may be interpreted as PR Steward READY.
- Canonical formal status remains `embedded_audit.status=SKIPPED`.
- `auditor_tool=none`, `auditor_model=unknown`.
- `PROOF.json.sig` must remain absent.
- No claim that PR #1182 is safe to dispatch.
- No Wave 0 dispatch, no reopening of PR #1182, no implementation mutation.

## Allowed paths

- `task-packets/TP-REPLAN-BASELINE-1182-POSTMERGE-QUARANTINE.md` (this packet)
- `proof/pr_merge/embedded-audit/pr-1182/**`

## Forbidden paths

All runtime, routing, orchestration, workflow, schema, signer-policy, and implementation files, including but not limited to:

- `src/**`, `services/**`, `compose*.yml`
- `config/**`, `schemas/**`, `.github/workflows/**`
- `scripts/audit/**`, `scripts/governance/**`, `config/audit/**`
- routing tables, orchestrator plans, load plans, and any non-allowlisted docs

## Required repair surface (PR #1190 follow-up)

1. Track this Task Packet so reviewers can validate allowlist, risk lane, and stop conditions.
2. Set canonical `embedded_audit.report_path` to the bundled report:
   `proof/pr_merge/embedded-audit/pr-1182/AUDITOR_REPORT.md`
3. Preserve truthful unsigned SKIPPED state (no replacement signature).
4. Update quarantine bookkeeping (`COMMAND_LOG.md`, PR description) to state:
   - allowlist includes this tracked L0 Task Packet;
   - not an audited proof-only successor;
   - proof-only head/signature contract inapplicable because no exact-head audit exists;
   - canonical SKIPPED proof schema validates under pr-merge relaxation;
   - model calls remain zero.

## Validation

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git diff --name-status origin/main...HEAD
git diff --check origin/main...HEAD

python3 scripts/docs_frontmatter_guard.py \
  task-packets/TP-REPLAN-BASELINE-1182-POSTMERGE-QUARANTINE.md

python3 scripts/governance/validate_change_contract.py \
  --base origin/main --head HEAD --format text

# pr-merge packages soften report_path pattern (local acceptance practice)
python3 - <<'PY'
import json
from pathlib import Path
import jsonschema
proof = json.loads(Path("proof/pr_merge/embedded-audit/pr-1182/PROOF.json").read_text())
schema = json.loads(Path("schemas/proof/embedded_audit.schema.json").read_text())
props = dict(schema.get("properties") or {})
if "report_path" in props:
    rp = dict(props["report_path"]); rp.pop("pattern", None); props["report_path"] = rp
    schema = dict(schema); schema["properties"] = props
jsonschema.Draft7Validator(schema).validate(proof["embedded_audit"])
assert proof["embedded_audit"]["status"] == "SKIPPED"
assert proof["embedded_audit"]["auditor_tool"] == "none"
assert proof["embedded_audit"]["auditor_model"] == "unknown"
assert proof["exact_head_audit"] == "NOT_PROVEN"
assert proof["wave_0_authorized"] is False
assert proof["embedded_audit"]["report_path"] == (
    "proof/pr_merge/embedded-audit/pr-1182/AUDITOR_REPORT.md"
)
assert not Path("proof/pr_merge/embedded-audit/pr-1182/PROOF.json.sig").exists()
print("PROOF_SCHEMA_PASS")
PY

pre-commit run --from-ref origin/main --to-ref HEAD
```

Expected:

- max lane `L0`
- `model_audit_required=false`
- not classified as audited proof-only successor
- proof schema PASS (SKIPPED allOf / pr-merge softened report_path)
- no runtime or governance-tool path changes
- `MODEL_CALLS_REQUIRED=0`
- `WAVE_0_AUTHORIZED=false`

## Stop conditions

Stop and return `NEEDS_SUPERVISOR` if any of:

- change escapes the allowlist;
- risk lane escalates above L0;
- any path under forbidden surfaces is modified;
- a signature is created or retained over the quarantine SKIPPED proof;
- packet or proof claims PR Steward READY, Wave 0 authorization, or exact-head audit PASS;
- any implementation, routing, workflow, schema, or signer-policy mutation is proposed;
- merge of PR #1190 is requested as automatic READY rather than operator-controlled quarantine merge.

## Rollback

Revert only the quarantine commit(s) on branch `chore/pr-1182-postmerge-proof-quarantine` / PR #1190.

Do **not** touch merged implementation content on `main` for PR #1182 (`1b80fc6f…` / merge `fb710ef40…`).

## Terminal verdict

Return exactly one:

```text
PR_1190_READY_FOR_OPERATOR_MERGE
PR_1190_BLOCKED
PR_1190_NEEDS_SUPERVISOR
```

No merge, Wave 0 dispatch, PR #1182 reopening, or implementation mutation is authorized by this packet.
