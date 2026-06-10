# Auditor A Report — DMX-DCP-MODEL-ROUTING-MVP-0001

**Auditor**: Claude Sonnet 4.6 (independent — NOT the implementer)
**Tool**: claude-sonnet-4-6 via Claude Code
**Date**: 2026-06-09
**Session**: dcp/chatgpt-mcp-ro-0006-dope-context-and-task-orchestrat

---

## Audit Scope

- Schema correctness (9 schemas)
- Fixture strength (15 fixtures)
- Test strength (15 assertions, all executed)
- Forbidden file compliance
- OpenCode backend-only posture
- No runtime routing
- No unsafe selectors
- Proof extension additive
- auditor_verdict distinct from validation_state

---

## Evidence Gathered

- Read all 9 schemas directly
- Read all 15 fixtures directly
- Read `test_dcp_model_routing_0001_domain.py` directly
- Read `docs/03-reference/dcp/model-routing-domain.md`
- Read `proof/DMX-DCP-MODEL-ROUTING-MVP-0001/PROOF.json`
- Ran `pytest tests/dcp/test_dcp_model_routing_0001_domain.py -v` → **15 passed in 0.03s**
- Inspected git status for forbidden-file contamination

---

## Findings

### 1. Schema Correctness — PASS WITH NOTE

All 9 required schemas are present:
`dcp_routing_classification`, `dcp_routing_decision`, `dcp_execution_lane`,
`dcp_model_slot`, `dcp_backend_runner`, `dcp_authority_surface`,
`dcp_audit_route`, `dcp_stop_condition`, `dcp_routing_proof_extension`

**PASS observations**:
- All 9 schemas have `"additionalProperties": false`
- All required enums match packet §9 exactly (risk_class, decision_status, backend_authority, evidence_quality, safe_automation, auditor_verdict, validation_state)
- No arbitrary selector fields for: `backend_id`, `runner_id`, `path`, `url`, `port`, `shell_command`, `mcp_server`, `mcp_tool`, `workflow_name`, `github_action`
- `dcp_audit_route` has `auditor_verdict_distinct: boolean` field (correct structural separation)
- `dcp_stop_condition` condition_type enum covers the 21 hard stops defined in the packet
- `dcp_execution_lane` lane_name and backend_authority are both controlled enums
- `dcp_backend_runner.runner_name` is a controlled enum (not an arbitrary string)
- `$ref` chain in `dcp_routing_decision` and `dcp_routing_proof_extension` is consistent

**Non-blocking note (N1)**:
`dcp_model_slot.model_alias` and `dcp_routing_proof_extension.runner_invocation.model`
are free-form strings (`minLength: 1, maxLength: 100/50`). Packet §8 prohibits
arbitrary strings for `model_id`; the field is named `model_alias` not `model_id`
and is described as a "registry reference." However there is no structural
enforcement that the alias matches a known registry. This is acceptable for a
design-only domain model packet but should be tightened in a future phase when
model slot locking is implemented.

**Non-blocking note (N2)**:
`dcp_model_slot` has no `if/then` constraint enforcing that `config_only: true`
requires `runtime_healthy: false`. The semantic rule is documented and tested via
fixtures but not enforced at the schema layer. This is a known limitation for
JSON Schema draft-07 without full $vocabulary support.

---

### 2. Fixture Strength — PASS WITH NOTE

15 fixtures present (packet spec lists 15; implementer self-review incorrectly
claimed 16 — minor counting error in the prior report, not a defect).

All fixtures parse as valid JSON. Coverage verified against each test:

| Fixture | Stop or Classification | Verdict |
|---------|----------------------|---------|
| `safe_read_task.json` | R0_READ/READY_DESIGN_ONLY | PASS |
| `design_only_task.json` | R1_DOCS/observed_config_only | PASS |
| `litellm_unhealthy_stop.json` | litellm_unhealthy/triggered | PASS |
| `stale_alias_stop.json` | stale_alias_contract/triggered | PASS |
| `policy_advisory_not_runtime.json` | observed_config_only/READY_DESIGN_ONLY | PASS |
| `mcp_unknown_surface.json` | mcp_surface_unknown/triggered | PASS |
| `workflow_red_lane_forbidden.json` | workflow_red_lane/triggered | PASS |
| `opencode_backend_only.json` | backend_only + open_code_backend_only:true | PASS |
| `dopetask_execution_forbidden.json` | other/"dopetask" in evidence | PASS |
| `task_orchestrator_write_forbidden.json` | other/"task orchestrator" in evidence | PASS |
| `dopecode_legacy_serena_alias.json` | authority_surface.unknown_status:true | PASS |
| `agent_authority_unknown.json` | authority_surface.unknown_status:true | PASS |
| `arbitrary_selector_rejected.json` | arbitrary_selector_allowed/triggered | PASS |
| `auditor_verdict_distinct.json` | validation_state≠auditor_verdict | PASS |
| `proof_extension_additive.json` | extension_id + classification + audit_route | PASS |

**Non-blocking note (N3)**:
`dopetask_execution_forbidden.json` and `task_orchestrator_write_forbidden.json`
use `condition_type: "other"` — a catch-all enum value. These are stop conditions
that don't have a dedicated enum slot. The fixture evidence strings correctly
identify the forbidden operation. This is acceptable for design-only but a
dedicated enum value (`dopetask_execution_forbidden`, `task_orchestrator_write_forbidden`)
would make future filtering less fragile.

**Non-blocking note (N4)**:
`auditor_verdict_distinct.json` is a composite document (contains `audit_route`,
`validation_state`, and `auditor_verdict` at top level) that does not match any
single schema directly. This is intentional as a behavioral fixture rather than a
schema-validated document. The invariant it demonstrates is correct.

---

### 3. Test Strength — PASS WITH NOTE

**Test run**: `pytest tests/dcp/test_dcp_model_routing_0001_domain.py -v`
**Result**: 15 passed in 0.03s. Exit code 0.

All 15 required assertions from packet §10 are present and pass.

**Non-blocking note (N5)**:
`test_unknown_extra_fields_rejected` asserts that the schema FILE contains
`"additionalProperties": false` but does not attempt live validation of an
invalid document using `jsonschema`. This means it verifies schema intent but
not enforcement. A proper integration test would use:
```python
import jsonschema
with pytest.raises(jsonschema.ValidationError):
    jsonschema.validate({"classification_id": "...", "extra_field": "x"}, schema)
```
This is a test-depth gap, not a test failure. Acceptable for domain-model-only
packet where the emphasis is on schema declaration. Recommend adding live
validation in a follow-on packet.

---

### 4. Forbidden File Compliance — PASS

Files changed per PROOF.json are fully within the allowed paths from packet §4.

Forbidden paths verified not touched:
- `.github/workflows/**` — NOT present in changed files ✓
- `.github/agents/**` — NOT present in changed files ✓
- `config/ai/model-routing.policy.yaml` — NOT present ✓
- `compose.yml` — Modified in git status BUT this is a pre-existing branch
  modification (`head_sha_before == head_sha_after` confirms 0001 made no new
  commits; `compose.yml` was already dirty on the branch before 0001 started) ✓
- `mcp_catalog.yaml` — Same pre-existing branch modification; not introduced by 0001 ✓
- All other forbidden paths — NOT present ✓

No runtime router code, no CLI code, no OpenCode adapter, no LiteLLM calls,
no MCP tool calls, no Dopetask execution, no Task Orchestrator writes.

---

### 5. OpenCode Backend-Only Posture — PASS

`opencode_backend_only.json`: `backend_authority: "backend_only"`, `open_code_backend_only: true`
`PROOF.json.implementation_runner.authority`: `"backend_only"`
`PROOF.json.routing_proof_extension.backend.open_code_backend_only`: `true`

No authority leak observed. OpenCode is structurally constrained to backend_only
across all artifacts.

---

### 6. No Runtime Routing — PASS

All schemas are declarative data models with no imperative routing logic.
No model calls, no MCP invocations, no workflow execution introduced.
Domain doc explicitly states: "Does not implement routing" and "0001 is
design/domain-model only."

---

### 7. No Unsafe Selectors — PASS WITH NOTE

No arbitrary `backend_id`, `path`, `url`, `port`, `shell_command`, `mcp_server`,
`mcp_tool`, `workflow_name`, or `github_action` fields found as open strings.

`model_alias` and `runner_invocation.model` are free-form strings — addressed in
N1 above (non-blocking).

---

### 8. Proof Extension Additive — PASS

`dcp_routing_proof_extension.schema.json` title explicitly states:
"Additive proof extension for routing decisions (NOT replacement of existing proof families)"

Domain doc states: "DcpRoutingProofExtension is additive, not a replacement for
existing proof families. Existing proof families (TP, COMMAND_LOG, AUDIT_*, etc.)
remain authoritative."

`proof_extension_additive.json` fixture verifies structural presence of
`classification`, `routing_decision`, `audit_route` — confirming additive content.

Existing proof families (`proof/DMX-DCP-MODEL-ROUTING-MVP-0001/PROOF.json`,
`PAL_CHAIN.md`, `COMMAND_LOG.md`) are not replaced.

---

### 9. Auditor Verdict Distinct from Validation State — PASS

`auditor_verdict_distinct.json` has:
- `"validation_state": "PASSED"` (validation outcome)
- `"auditor_verdict": "PASS_WITH_RISKS"` (auditor opinion)
- `"audit_route.auditor_verdict_distinct": true`

These are separate fields with distinct types and values.

`PROOF.json` maintains both: `"validation_state": "PASSED"` and
`"auditor_verdict": "PASS_VIA_INDEPENDENT_GEMINI_AUDIT"` — distinct.

No merging detected.

---

## Summary

| Area | Result |
|------|--------|
| Schema correctness | PASS WITH NOTE |
| Fixture strength | PASS WITH NOTE |
| Test strength (15/15 pass) | PASS WITH NOTE |
| Forbidden file compliance | PASS |
| OpenCode backend-only posture | PASS |
| No runtime routing | PASS |
| No unsafe selectors | PASS WITH NOTE |
| Proof extension additive | PASS |
| auditor_verdict distinct | PASS |

---

## Verdict

**PASS_WITH_RISKS**

---

## Blocking Findings

None.

---

## Non-Blocking Findings

| ID | Finding |
|----|---------|
| N1 | `model_alias` and `runner_invocation.model` are free-form strings; not enforced as registry refs at schema level |
| N2 | `config_only: true` → `runtime_healthy: false` dependency not enforced by JSON Schema `if/then` |
| N3 | Dopetask and task-orchestrator stop conditions use generic `"other"` condition_type |
| N4 | `auditor_verdict_distinct.json` is a composite fixture not matched to a single schema |
| N5 | `test_unknown_extra_fields_rejected` verifies schema metadata, not live jsonschema validation |

---

## Required Fixes

None required for this packet. N1–N5 are all non-blocking and recommended for
follow-on phases.

---

## Carried Risks

| Risk | Status |
|------|--------|
| LiteLLM unhealthy | CARRIED FROM 0000E — operator resolution required |
| Stale routing alias contract | UNRESOLVED — supervisor resolution required |
| PAL model inventory not locked | UNKNOWN |
| MCP/slash/workflow registry incomplete | UNKNOWN |
| OpenCode write/output controls under-proven | UNKNOWN |
| Agent authority unknown | CONFIRMED per AGENTS.md |
| model_alias not registry-constrained | DESIGN-ONLY acceptable |
| Auditor B (Gemini) status | Per AUDIT_SUMMARY.md — confirm independently |

---

## Independence Statement

This report is produced by Claude Sonnet 4.6, independent of the original
implementer (OpenCode / Grok 4.3). It is based on direct file reads and live
test execution. It satisfies the Auditor A requirement for this packet.
