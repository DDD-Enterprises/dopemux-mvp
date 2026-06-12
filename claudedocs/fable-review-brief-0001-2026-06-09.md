# Fable Review Brief — DMX-DCP-MODEL-ROUTING-MVP-0001

**Date**: 2026-06-09
**Prepared by**: Claude Sonnet 4.6 (Auditor A, this session)
**For**: Claude Fable 5 (independent reviewer)
**Repo**: DDD-Enterprises/dopemux-mvp

---

## 1. What This Is

Task packet `DMX-DCP-MODEL-ROUTING-MVP-0001` is a **design-only domain model** for the DCP (Dope Context Protocol) Routing & Execution Plane.

**Scope**: Schemas + fixtures + tests + domain doc + proof artifacts. No runtime code. No model calls. No MCP invocations. No router implementation.

**Implementer**: OpenCode using Grok 4.3 (backend-only authority)

**Branch**: `dcp/chatgpt-mcp-ro-0006-dope-context-and-task-orchestrat`

**Most recent commit**: `fdefc7cc8 feat(dcp): DMX-DCP-MODEL-ROUTING-MVP-0001 domain model + dual independent audit`

---

## 2. Current Git State

```
Branch:  dcp/chatgpt-mcp-ro-0006-dope-context-and-task-orchestrat
HEAD:    fdefc7cc8

Staged modified (from prior sessions, pre-HEAD):
  proof/DMX-DCP-MODEL-ROUTING-MVP-0001/PROOF.json
  proof/DMX-DCP-MODEL-ROUTING-MVP-0001/audit/AUDITOR_A_REPORT.md
  proof/DMX-DCP-MODEL-ROUTING-MVP-0001/audit/AUDIT_SUMMARY.md
  proof/DMX-DCP-MODEL-ROUTING-MVP-0001/COMMAND_LOG.md
  proof/DMX-DCP-MODEL-ROUTING-MVP-0001/GPT55_REVIEW_BRIEF.md
  proof/DMX-DCP-MODEL-ROUTING-MVP-0001/HANDOFF.md
  proof/DMX-DCP-MODEL-ROUTING-MVP-0001/IMPLEMENTER_NOTES.md
  proof/DMX-DCP-MODEL-ROUTING-MVP-0001/PAL_CHAIN.md
  [+agent prompts 01–07]

Pre-existing branch dirt (NOT part of 0001):
  .gitignore, AGENTS.md, compose.yml, mcp_catalog.yaml  (unstaged)
  proof/TP-OPS-MAC-SCRUBBER-001/*                        (unstaged)

Untracked (NOT part of 0001):
  task-packets/DMX-DCP-MODEL-ROUTING-MVP-0000C–I.md
  tests/fixtures/dcp/routing_corpus/
  Various prior proof bundles, scripts/opencode/, etc.
```

**Note**: The branch carries pre-existing modifications unrelated to 0001. The diff stat for 0001 items is authoritative; do not treat branch-level dirt as 0001 scope.

---

## 3. What Was Built (Allowed Files)

### 9 JSON Schemas (`schemas/dcp/`)

| Schema | Purpose |
|--------|---------|
| `dcp_routing_classification.schema.json` | Risk class + automation safety |
| `dcp_routing_decision.schema.json` | Decision with lane, stops, authority, audit |
| `dcp_execution_lane.schema.json` | Lane with backend authority constraints |
| `dcp_model_slot.schema.json` | Model slot with evidence quality (NOT runtime health) |
| `dcp_backend_runner.schema.json` | Runner with authority level + OpenCode flag |
| `dcp_authority_surface.schema.json` | Authority surface with canonical owner |
| `dcp_audit_route.schema.json` | Audit route with PAL chain + verdict separation |
| `dcp_stop_condition.schema.json` | Stop condition with evidence + resolution |
| `dcp_routing_proof_extension.schema.json` | Additive proof extension (NOT replacement) |

All 9 have `"additionalProperties": false`. All dangerous fields use controlled enums.

### 15 Fixtures (`tests/fixtures/dcp/model_routing_0001/`)

Cover the key stop conditions and behavioral invariants:
- `safe_read_task.json`, `design_only_task.json`
- `litellm_unhealthy_stop.json`, `stale_alias_stop.json`
- `policy_advisory_not_runtime.json`, `mcp_unknown_surface.json`
- `workflow_red_lane_forbidden.json`, `opencode_backend_only.json`
- `dopetask_execution_forbidden.json`, `task_orchestrator_write_forbidden.json`
- `dopecode_legacy_serena_alias.json`, `agent_authority_unknown.json`
- `arbitrary_selector_rejected.json`, `auditor_verdict_distinct.json`
- `proof_extension_additive.json`

### 15 Tests (`tests/dcp/test_dcp_model_routing_0001_domain.py`)

**Result**: 15 passed in 0.03s (run live by Auditor A this session).

Tests assert: strict schema enforcement, stop condition triggering, advisory policy isolation, OpenCode backend-only posture, auditor_verdict/validation_state separation, proof extension additivity, and more.

### Domain Doc (`docs/03-reference/dcp/model-routing-domain.md`)

Explicitly states: does not implement routing, does not prove runtime health, does not lock model slots, does not make OpenCode authoritative, does not enable Dopetask or Task Orchestrator, does not collapse proof families.

### Proof Bundle (`proof/DMX-DCP-MODEL-ROUTING-MVP-0001/`)

- `PROOF.json` — full audit record with carried risks, stop conditions, validation state
- `COMMAND_LOG.md` — preflight + build commands
- `PAL_CHAIN.md` — PAL chain status (prompts created; execution deviations noted)
- `IMPLEMENTER_NOTES.md` — implementer notes on decisions
- `GPT55_REVIEW_BRIEF.md` — GPT-5.5 Pro supervisor review brief
- `HANDOFF.md` — handoff for next reviewer
- `agents/01–07_*_prompt.md` — proof-local helper prompts (NOT runtime agents)
- `audit/AUDITOR_A_REPORT.md` — Auditor A (Claude Sonnet 4.6) report
- `audit/AUDITOR_B_REPORT.md` — Auditor B (Gemini 2.5 Pro) report
- `audit/AUDIT_SUMMARY.md` — combined audit summary

---

## 4. Audit Results

### Auditor A — Claude Sonnet 4.6 (this session, independent)

**Verdict**: PASS_WITH_RISKS

**Blocking**: None

**Non-blocking (N1–N5)**:
- N1: `model_alias` / `runner_invocation.model` are free-form strings — not registry-constrained at schema level
- N2: `config_only: true` → `runtime_healthy: false` not enforced by JSON Schema `if/then`
- N3: Dopetask / task-orchestrator stop conditions use generic `"other"` condition_type
- N4: `auditor_verdict_distinct.json` is a composite fixture not validated against a single schema
- N5: `test_unknown_extra_fields_rejected` verifies schema metadata, not live jsonschema validation

**Full report**: `proof/DMX-DCP-MODEL-ROUTING-MVP-0001/audit/AUDITOR_A_REPORT.md`

### Auditor B — Gemini 2.5 Pro (prior session, independent)

**Verdict**: PASS

**Contradictions found**: 0 (across 12 attack vectors)
**Authority leaks**: None
**Proof gaps**: None

**Full report**: `proof/DMX-DCP-MODEL-ROUTING-MVP-0001/audit/AUDITOR_B_REPORT.md`

---

## 5. Carried Risks (from PROOF.json)

| Risk | Status |
|------|--------|
| LiteLLM unhealthy | CARRIED FROM 0000E — operator resolution required |
| Stale routing alias contract | UNRESOLVED — supervisor required |
| PAL model inventory not locked | UNKNOWN |
| MCP/slash/workflow registry incomplete | UNKNOWN |
| OpenCode write/output controls under-proven | UNKNOWN |
| Agent authority unknown | CONFIRMED per AGENTS.md |
| PAL chain prompts created but not executed | Deviation noted; supervisor review required before PR |
| model_alias not registry-constrained | Design-only acceptable; tighten in future phase |

---

## 6. Hard Stop Conditions (for 0001)

All 21 stop conditions from the packet spec are structurally represented in schemas/fixtures. Key active triggers:
- `litellm_unhealthy: triggered: true`
- `stale_alias_contract: triggered: true`
- `mcp_surface_unknown: triggered: true`
- `workflow_red_lane: triggered: true`
- `arbitrary_selector_allowed: triggered: true` (test fixture asserting rejection)

None of these represent violations — they are correct representations of the environment state that 0001 must not act on.

---

## 7. What Fable Should Review

1. **Schema strictness** — Are all 9 schemas genuinely safe? Any enum gaps or missing constraints that Auditors A+B missed?

2. **N1 risk** — Is the free-form `model_alias` string an acceptable design-only choice, or does it need to be a controlled enum even at this stage?

3. **N2 risk** — Should `config_only: true` → `runtime_healthy: false` be enforced at the schema layer (JSON Schema `if/then`)? Or is the test-layer check sufficient for domain-model-only?

4. **N5 risk** — Is `test_unknown_extra_fields_rejected` strong enough, or does the test suite need live `jsonschema.validate()` calls to be credible?

5. **Proof integrity** — Does the PROOF.json correctly represent the packet's scope and limitations? Are any carried risks understated?

6. **PR readiness** — Given Auditor A PASS_WITH_RISKS + Auditor B PASS + PAL chain deviation (not executed), is this packet PR-ready, or does it need additional gates?

7. **Forbidden file contamination** — The branch has pre-existing dirty tracked files (`.gitignore`, `AGENTS.md`, `compose.yml`, `mcp_catalog.yaml`). Are any of these forbidden for 0001, and do they present a merge risk?

---

## 8. Key Files to Read

Start here:
- `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0001.md` — the authoritative spec
- `proof/DMX-DCP-MODEL-ROUTING-MVP-0001/PROOF.json` — current state summary
- `proof/DMX-DCP-MODEL-ROUTING-MVP-0001/audit/AUDIT_SUMMARY.md` — both auditor verdicts
- `schemas/dcp/dcp_routing_proof_extension.schema.json` — most complex schema

Then spot-check:
- `schemas/dcp/dcp_model_slot.schema.json` — N2 risk lives here
- `tests/dcp/test_dcp_model_routing_0001_domain.py` — N5 risk lives here
- `tests/fixtures/dcp/model_routing_0001/auditor_verdict_distinct.json` — N4 risk lives here

---

## 9. What This Packet Does NOT Do

This is design-only. Fable should NOT expect:
- A router implementation
- Model calls or invocations
- CLI code
- MCP adapter code
- Runtime routing health proof
- Model slot locking
- Dopetask execution
- Task Orchestrator writes

Any of the above appearing would be a packet violation. Auditors A+B found none.
