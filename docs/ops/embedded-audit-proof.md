---
id: embedded-audit-proof
title: Embedded Audit Proof Format
type: reference
owner: governance
date: 2026-05-27
author: '@hu3mann'
last_review: '2026-07-29'
next_review: '2026-10-27'
prelude: Embedded Audit Proof Format (explanation) for dopemux documentation and developer
  workflows.
---
# Embedded Audit Proof Format

Every PROOF.json bundle for this series must contain an `embedded_audit` sub-object.
This document defines the canonical format, the schema that enforces it, and the
known pre-existing non-compliant bundles.

Related: [`docs/ops/audit-bundles.md`](audit-bundles.md)

---

## Schema

**Canonical file**: `schemas/proof/embedded_audit.schema.json` (Draft 7)

**Do not modify the enums in this schema without supervisor approval** — that is a
series stop condition for `DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED`.

### Required fields

| Field | Type | Notes |
|---|---|---|
| `required` | `boolean` | Whether an embedded audit was mandated for this TP |
| `status` | `string` (enum) | Audit outcome |
| `auditor_tool` | `string` (enum) | Tool used to run the audit |
| `auditor_model` | `string` (enum) | Model invoked by the audit tool |
| `invocation` | `string \| null` | Exact MCP call / CLI command |
| `exit_code` | `integer \| null` | Process exit code; null when SKIPPED |
| `report_path` | `string` | Relative path to the AUDITOR_REPORT.md |
| `findings` | `array<Finding>` | Zero or more finding objects |
| `fixes_applied` | `array<string>` | Human-readable list of fixes applied |
| `remaining_risks` | `array<string>` | Residual risks after the audit |
| `skip_reason` | `string \| null` | Required (non-null) when status=SKIPPED; null otherwise |

### Enums

**`status`** — `PASS`, `PASS_WITH_RISKS`, `FAIL`, `NEEDS_SUPERVISOR`, `SKIPPED`

**`auditor_tool`** — `agy`, `antigravity`, `claude-code-cli`, `copilot-cli`, `gemini-cli`, `pal-mcp-clink`, `none`

`pal-mcp-clink` is not new here: it is already present in the trusted schema on `main`.
This line previously omitted it, and the omission is corrected as documentation catching
up to the enacted schema — no `auditor_tool` value is added by this change.

**`auditor_model`** — `sonnet`, `claude-sonnet-4.6`, `opus`, `gemini`, `gemini-3.1-pro-high`, `unknown`

`gemini-3.1-pro-high` is the exact approved model identifier for an AGY audit.
Use it only when the invocation proves explicit selection, for example
`agy --model gemini-3.1-pro-high --print ...`, and the captured AGY evidence
shows no fallback to another model. The generic `gemini` value remains valid for
backward compatibility and for bootstrap audits performed before this enum change
is present on the trusted branch; new post-merge proofs should prefer the exact
identifier.

### Conditional constraints

**SKIPPED** (`status == "SKIPPED"`):
- `auditor_tool` must be `"none"`
- `auditor_model` must be `"unknown"`
- `invocation` must be `null`
- `exit_code` must be `null`
- `skip_reason` must be a non-empty string

**Non-SKIPPED** (all other status values):
- `auditor_tool` must not be `"none"`
- `auditor_model` must not be `"unknown"`
- `invocation` must be a non-empty string
- `exit_code` must be an integer
- `skip_reason` must be `null`

**Exact AGY model** (`auditor_model == "gemini-3.1-pro-high"`):
- `auditor_tool` must be present and must be `"agy"`

The `required` inside that conditional is deliberate. JSON Schema `properties` is vacuous
for an absent key, so without it the constraint would pass for a payload that omits
`auditor_tool`. The top-level `required` list already forbids that, but the conditional is
made self-contained so it cannot be weakened by an unrelated edit to that list.

### What the schema proves — and what it does not

`ACCEPTED_DESIGN_BOUNDARY: SCHEMA_BINDS_DECLARED_TOOL_MODEL_PAIR; RUNTIME_SELECTOR_PROVEN_BY_EXECUTION_EVIDENCE`

The `auditor_model` → `auditor_tool` conditionals bind the **declared pairing**: a proof
claiming `auditor_model: "gemini-3.1-pro-high"` must also claim `auditor_tool: "agy"`.
That is a consistency constraint on the declaration.

The schema deliberately **does not parse `invocation`**. It is an opaque string, so a
schema-valid proof is *not* evidence that the runner was actually executed with
`--model gemini-3.1-pro-high`. A regex over `invocation` would only prove that a
substring appeared in a field the producer wrote — the same trust level as the
`auditor_model` field itself — while creating a brittle shell-command parser and a
false impression of runtime enforcement.

Runtime selector truth is carried by execution evidence instead:

- the recorded `invocation`;
- captured runner evidence (`agy --version`, model list) at capture time;
- `requested_selector` / `observed_selector` in the route record;
- fail-closed rejection of an invalid selector — AGY aborts with
  `model ... is not recognized as a known model` rather than silently substituting,
  so no unproven fallback can occur;
- the independent audit itself.

Do not read schema validity as proof of runtime execution semantics, and do not widen
these conditionals into invocation parsing without replacing this boundary statement.
`tests/audit/test_agy_gemini31_model.py::test_schema_does_not_constrain_invocation_string`
pins the boundary so it cannot drift silently.

### Finding shape

```json
{
  "id": "F-001-MED-1",
  "severity": "MEDIUM",
  "title": "Short title",
  "status": "RESOLVED",
  "body": "Detail."
}
```

`severity` enum: `BLOCKING`, `HIGH`, `MEDIUM`, `LOW`, `INFO`
`status` enum: `OPEN`, `RESOLVED`, `ACCEPTED_RISK`

---

## Canonical example: PASS_WITH_RISKS

```json
{
  "required": true,
  "status": "PASS_WITH_RISKS",
  "auditor_tool": "claude-code-cli",
  "auditor_model": "claude-sonnet-4.6",
  "invocation": "mcp__pal__codereview expert_model=gpt-5.2 review_type=full",
  "exit_code": 0,
  "report_path": "proof/TP-EXAMPLE-001/AUDITOR_REPORT.md",
  "findings": [
    {
      "id": "F-001-LOW-1",
      "severity": "LOW",
      "title": "Pre-existing fixture coverage gap",
      "status": "ACCEPTED_RISK",
      "body": "Not introduced by this TP; covered by a dedicated test file."
    }
  ],
  "fixes_applied": [],
  "remaining_risks": ["mypy not run — no new typed source files"],
  "skip_reason": null
}
```

## Canonical example: AGY Gemini 3.1 Pro High

```json
{
  "required": true,
  "status": "PASS_WITH_RISKS",
  "auditor_tool": "agy",
  "auditor_model": "gemini-3.1-pro-high",
  "invocation": "agy --model gemini-3.1-pro-high --print '<bounded read-only audit prompt>'",
  "exit_code": 0,
  "report_path": "proof/TP-EXAMPLE-AGY/AUDITOR_REPORT.md",
  "findings": [],
  "fixes_applied": [],
  "remaining_risks": ["Model availability is account-dependent; captured model-selection evidence is required."],
  "skip_reason": null
}
```

This proof shape approves the model identifier. It does not grant AGY write
authority, authorize CI credentials, or permit an unproven alias such as `pro`.

## Canonical example: SKIPPED

```json
{
  "required": false,
  "status": "SKIPPED",
  "auditor_tool": "none",
  "auditor_model": "unknown",
  "invocation": null,
  "exit_code": null,
  "report_path": "proof/TP-EXAMPLE-002/AUDITOR_REPORT.md",
  "findings": [],
  "fixes_applied": [],
  "remaining_risks": [],
  "skip_reason": "No executable logic introduced; read-only evidence capture only."
}
```

---

## Validator

`scripts/audit/validate_audit_proof.py` validates one or more PROOF.json files
against the schema.

```bash
# Validate a single bundle
python scripts/audit/validate_audit_proof.py proof/TP-DMX-PR-FIXTURES-011/PROOF.json

# Validate multiple bundles
python scripts/audit/validate_audit_proof.py proof/TP-*/PROOF.json

# Scan all bundles under proof/
python scripts/audit/validate_audit_proof.py --all proof/

# Quiet: suppress PASS lines, show only failures and summary
python scripts/audit/validate_audit_proof.py --quiet --all proof/

# Custom schema path
python scripts/audit/validate_audit_proof.py --schema path/to/schema.json proof/TP-001/PROOF.json
```

**Exit codes**:
- `0` — all validated bundles PASS
- `1` — one or more bundles FAIL
- `2` — usage error (bad arguments, missing schema, no files found)

### The schema is the single policy engine

Two routes validate an `embedded_audit` object, and both execute **this schema**
under real Draft 7 semantics via `jsonschema.Draft7Validator`:

| Route | Entry point | Schema is read from |
|---|---|---|
| Deterministic sweep | `scripts/audit/validate_audit_proof.py` | working tree |
| Signed local attestation | `scripts/audit/local_audit_acceptance.py` | the **trusted base ref**, never the PR branch |

Neither route mirrors the schema's rules in hand-written Python. That matters
most for the `allOf` conditionals: a conditional added to the schema is enforced
by both routes the day it lands, with no second implementation to update.

This was not always true. The acceptance route previously used a hand-rolled
stdlib check that verified `required`, a few enum memberships, and a few types —
it never walked `allOf` and it exempted `report_path`. The consequence was that
a signed proof the canonical validator **rejects** could be **accepted** by the
attestation route: for example `auditor_model: gemini-3.1-pro-high` declared
with `auditor_tool: claude-code-cli`, a pairing the schema forbids. The gap sat
behind the signature trust boundary, so it let a *trusted signer* record a
forbidden pairing rather than letting an untrusted party in — but a trust
contract that the trusted path does not enforce is not a trust contract.
Parity is now pinned by `tests/audit/test_local_audit_acceptance.py`, which
asserts agreement between the acceptance route and `Draft7Validator` over a
fixture corpus and fails if a new `allOf` branch appears without coverage.

Two consequences worth stating plainly:

- **`report_path` is validated on both routes.** A downstream trusted emitter
  may later substitute its own canonical artifact path, but that is not a reason
  to accept a schema-invalid signed input. Skipping the field is precisely how a
  nonconformant `report_path` reached a published proof while CI stayed green.
- **Verdict policy is separate from schema validity.** The schema deliberately
  admits `FAIL` and `SKIPPED`, because CI also emits diagnostic proofs. Local
  attestation accepts passing verdicts only, applied as its own check after
  schema validation.

`jsonschema` is a declared project dependency (`pyproject.toml`). Where it is
absent the acceptance route **fails closed** with `schema_validator_unavailable`
and never falls back to a partial check.

## Independent Workflow Output

`scripts/audit/run_embedded_audit.py` writes a top-level `PROOF.json` bundle with
the canonical `embedded_audit` sub-object and a separate `provenance` object.
The provenance object is outside the schema-governed `embedded_audit` object and
records:

- proof author: `independent-embedded-audit`
- workflow: `embedded-audit.yml`
- read-only permission set
- trusted-token status (`AVAILABLE` or `UNKNOWN`)
- `token_value_recorded: false`
- `engine_authored_proof: false`

The entrypoint accepts a static `AUDITOR_ROUTE.json` and, when available,
`PAL_CLINK_AUDIT_OUTPUT.json`. Pull-request CI does not expose
`EMBEDDED_AUDIT_TOKEN` to PR-head code and runs the proof emitter from a trusted
checkout, so that path emits `SKIPPED` unless a trusted-ref caller supplies both
token authority and PAL output. With a present token in a trusted invocation and
captured PAL output, the entrypoint normalizes the PAL verdict through the
existing embedded-audit policy. Without route evidence, the token, or PAL output,
it emits `SKIPPED` and records the missing authority in `skip_reason`.

The emitted `embedded_audit.report_path` is the canonical
`proof/<packet-id>/AUDITOR_REPORT.md` path. Artifact bundles must include that
relative file path so consumers following the proof object can read the report.
If the trusted checkout does not yet contain the proof emitter, bootstrap CI
must emit a schema-valid `SKIPPED` proof rather than executing the PR-head copy
of the emitter.
If the requested head SHA cannot be fetched or does not match
`refs/pull/<number>/head`, the proof must also be `SKIPPED` and record the
head-integrity failure as the reason.
Manual dispatch must keep proof-authoring code on the repository default branch
and must not treat the selected dispatch branch as trusted proof-authoring code
or as proof that the supplied SHA belongs to the requested PR.
The audit token may be passed only to the trusted-source emitter step; bootstrap
and head-integrity SKIPPED proof paths must not receive it.

---

## Known non-compliant bundles (pre-existing)

These bundles exist in the `DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED` series but
were written before the schema was finalized. They **cannot be fixed** under
TP-DMX-AUDIT-PROOF-004 because they are not in the TP-004 files allowlist.
Remediation requires a dedicated TP per bundle.

### `proof/TP-DMX-CI-TRIGGERS-008/PROOF.json`

**Series**: DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED

**Violations** (as of 2026-05-27):
- `auditor_tool`: `"PAL MCP codereview (mcp__pal__codereview)"` — not in enum
- `auditor_model`: `"gemini-2.5-pro"` — not in enum; closest canonical value is `"gemini"`
- `exit_code`: `"code_review_complete: true"` — string, must be integer
- `remaining_risks`: plain string, must be array
- Missing required fields: `report_path`, `findings`, `fixes_applied`, `skip_reason`
- Extra (forbidden) fields: `fallback_used`, `fallback_reason`, `auditor_verdict`, `auditor_findings`, `fixes_applied_from_audit`

**Remediation**: Rewrite the `embedded_audit` object using the canonical schema.
Requires operator authorization; no auto-remediation.

---

### `proof/TP-DMX-BRANCH-POLICY-AUDIT-012/PROOF.json`

**Series**: DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED

**Violations** (as of 2026-05-27):
- `status`: `"NOT_RUN"` — not in enum; closest canonical value is `"SKIPPED"`
- Missing required fields: `auditor_tool`, `auditor_model`, `invocation`, `exit_code`,
  `report_path`, `findings`, `fixes_applied`, `remaining_risks`
- `skip_reason` present and non-null, but `status != "SKIPPED"` — conditional constraint violated

**Remediation**: The intent appears to be `status: "SKIPPED"` (read-only TP, no code changes).
Rewrite using the SKIPPED canonical shape. Requires operator authorization.

---

## Authority

- Schema: `schemas/proof/embedded_audit.schema.json` (canonical, do not modify enums without supervisor)
- Validator: `scripts/audit/validate_audit_proof.py`
- Tests: `tests/audit/test_audit_proof.py`
- Governing task: `TP-DMX-AUDIT-PROOF-004` in `DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED`
