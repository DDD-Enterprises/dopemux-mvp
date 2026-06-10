---
id: DMX-DCP-MODEL-ROUTING-MVP-0001
title: Dmx Dcp Model Routing Mvp 0001
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-09'
last_review: '2026-06-09'
next_review: '2026-09-07'
prelude: Dmx Dcp Model Routing Mvp 0001 (explanation) for dopemux documentation and
  developer workflows.
---
# Task Packet: DMX-DCP-MODEL-ROUTING-MVP-0001 · DCP · Routing Domain Model

## 0. Read Me First

This packet is intentionally simple.

You are OpenCode using Grok 4.3 as a bounded implementer.

You are allowed to create schemas, fixtures, tests, docs, and proof files.

You are not allowed to implement runtime routing.
You are not allowed to make OpenCode authoritative.
You are not allowed to self-audit your own work as final proof.
You must produce enough proof for GPT-5.5 Pro web review after completion.

---

## 1. Objective

Create the first DCP Routing & Execution Plane domain model.

This means:
1. Define strict JSON schemas.
2. Define safe fixtures.
3. Define tests for the schemas and fixtures.
4. Write a short domain-model doc.
5. Write proof and review artifacts.

This packet does **not** create a router.
This packet does **not** call models.
This packet does **not** invoke MCP tools.
This packet does **not** touch workflows.
This packet does **not** run Dopetask execution.

---

## 2. Current Evidence Baseline

Use this evidence posture:

| Evidence | Status | How 0001 uses it |
|---|---|---|
| Clean `origin/main` exists at `55a713be4c49c59f1d4fedeed6a1930477dd54fb` | OBSERVED | Baseline for policy and red-lane cleanliness |
| `config/ai/model-routing.policy.yaml` exists on clean `origin/main` | OBSERVED | Advisory design input only |
| `model-routing.policy.yaml` says it is not runtime routing authority | OBSERVED | Do not treat as router |
| LiteLLM is unhealthy | OBSERVED | Stop condition, no runtime dependency |
| routing alias contract is stale | OBSERVED | Stop condition |
| PAL model inventory is not locked for runtime | UNKNOWN / BLOCKED | Do not lock model slots |
| MCP/slash/workflow registry is incomplete | UNKNOWN | Unknown surfaces stay unknown |
| OpenCode is installed/invokable | OBSERVED | Backend implementer only |
| OpenCode write/output controls are under-proven | UNKNOWN | Do not make OpenCode authoritative |
| Agents have unknown runtime authority | UNKNOWN | Helper prompts only, no runtime agents |

---

## 3. What You Are Building

Create these domain objects:
1. `DcpRoutingClassification`
2. `DcpRoutingDecision`
3. `DcpExecutionLane`
4. `DcpModelSlot`
5. `DcpBackendRunner`
6. `DcpAuthoritySurface`
7. `DcpAuditRoute`
8. `DcpStopCondition`
9. `DcpRoutingProofExtension`

These are schemas and fixtures only.
No runtime code.
No CLI.
No adapter.
No model calls.

---

## 4. Allowed Files

Only touch these paths:

```
task-packets/DMX-DCP-MODEL-ROUTING-MVP-0001.md
docs/03-reference/dcp/model-routing-domain.md
schemas/dcp/dcp_routing_classification.schema.json
schemas/dcp/dcp_routing_decision.schema.json
schemas/dcp/dcp_execution_lane.schema.json
schemas/dcp/dcp_model_slot.schema.json
schemas/dcp/dcp_backend_runner.schema.json
schemas/dcp/dcp_authority_surface.schema.json
schemas/dcp/dcp_audit_route.schema.json
schemas/dcp/dcp_stop_condition.schema.json
schemas/dcp/dcp_routing_proof_extension.schema.json
tests/dcp/test_dcp_model_routing_0001_domain.py
tests/fixtures/dcp/model_routing_0001/safe_read_task.json
tests/fixtures/dcp/model_routing_0001/design_only_task.json
tests/fixtures/dcp/model_routing_0001/litellm_unhealthy_stop.json
tests/fixtures/dcp/model_routing_0001/stale_alias_stop.json
tests/fixtures/dcp/model_routing_0001/policy_advisory_not_runtime.json
tests/fixtures/dcp/model_routing_0001/mcp_unknown_surface.json
tests/fixtures/dcp/model_routing_0001/workflow_red_lane_forbidden.json
tests/fixtures/dcp/model_routing_0001/opencode_backend_only.json
tests/fixtures/dcp/model_routing_0001/dopetask_execution_forbidden.json
tests/fixtures/dcp/model_routing_0001/task_orchestrator_write_forbidden.json
tests/fixtures/dcp/model_routing_0001/dopecode_legacy_serena_alias.json
tests/fixtures/dcp/model_routing_0001/agent_authority_unknown.json
tests/fixtures/dcp/model_routing_0001/arbitrary_selector_rejected.json
tests/fixtures/dcp/model_routing_0001/auditor_verdict_distinct.json
tests/fixtures/dcp/model_routing_0001/proof_extension_additive.json
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/PROOF.json
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/COMMAND_LOG.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/HANDOFF.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/GPT55_REVIEW_BRIEF.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/IMPLEMENTER_NOTES.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/PAL_CHAIN.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/agents/01_scout_prompt.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/agents/02_planner_prompt.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/agents/03_builder_prompt.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/agents/04_self_check_prompt.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/agents/05_auditor_a_prompt.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/agents/06_auditor_b_prompt.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/agents/07_gpt55_review_prompt.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/audit/AUDITOR_A_REPORT.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/audit/AUDITOR_B_REPORT.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/audit/AUDIT_SUMMARY.md
```

If you need any other file, stop.

---

## 5. Forbidden Files

Do not touch these:

```
.github/workflows/**
.github/agents/**
config/ai/model-routing.policy.yaml
templates/routing.yaml
litellm.config.yaml
model_map_v2_tp008.yaml
compose.yml
mcp-proxy-config*
scripts/dopetask
scripts/taskx
scripts/batch_resolve_and_merge.py
src/dopemux_pr_merge_specialist/**
dopemux_pr_merge_specialist/**
services/task-orchestrator/**
services/dopecon-bridge/**
services/dope-context/**
services/working-memory-assistant/**
docker/mcp-servers-source/**
```

**Important**: do not create real repo agents.

The "agents" in this packet are only prompt files inside:

```
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/agents/
```

They are proof-local helper prompts, not runtime agents.

---

## 6. Hard Stop Conditions

Stop immediately if any of these happen:

1. You touch a forbidden file.
2. You create or edit `.github/agents/**`.
3. You create runtime router code.
4. You create CLI code.
5. You create an OpenCode adapter.
6. You call LiteLLM.
7. You call PAL listmodels.
8. You call MCP tools.
9. You run Dopetask execution.
10. You run Task Orchestrator writes.
11. You run ConPort writes.
12. You run dope-memory writes.
13. You run dope-context indexing.
14. You import or call PR merge specialist code.
15. You import or call `scripts/batch_resolve_and_merge.py`.
16. A schema allows arbitrary path, URL, port, shell command, backend, model, or MCP tool selection.
17. A schema treats config-only model evidence as runtime-health evidence.
18. A fixture marks a forbidden task as ready.
19. A fixture marks an unknown MCP/slash/workflow surface as safe.
20. `auditor_verdict` is merged into `validation_state`.
21. Existing proof families are replaced by one fake universal proof format.

If stopped, write:

```
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/HANDOFF.md
```

with:
- what you attempted
- what stopped you
- exact evidence
- what GPT-5.5 Pro should review next

---

## 7. Dead-Simple Execution Plan

Do these steps in order.

**Step 1 — Preflight**

Run preflight commands, append to COMMAND_LOG.md.

**Step 2 — Create helper prompt files**

Create proof-local prompts under `proof/.../agents/`.

**Step 3 — Run Scout**

Use `01_scout_prompt.md`. Output to PAL_CHAIN.md.

**Step 4 — Run Planner**

Use `02_planner_prompt.md`. Add to PAL_CHAIN.md.

**Step 5 — Challenge the Plan**

Challenge plan. If FAIL, stop.

**Step 6 — Build Schemas**

Create 9 JSON schemas. Validate with `python -m json.tool`.

**Step 7 — Build Fixtures**

Create 16 JSON fixtures. Validate all parse.

**Step 8 — Build Tests**

Create test file. Run pytest. Assert 15 specific conditions.

**Step 9 — Build Domain Doc**

Create short domain doc with required headings.

**Step 10 — Self-Check**

Use `04_self_check_prompt.md`. Write IMPLEMENTER_NOTES.md.

**Step 11 — Diff Allowlist Check**

Run diff allowlist validation. If fails, stop.

**Step 12 — Run Auditors**

Run two independent audits. If tooling unavailable, write NOT_RUN with reason.

**Step 13 — Build Audit Summary**

Create AUDIT_SUMMARY.md.

**Step 14 — Build PROOF.json**

Create PROOF.json with required shape.

**Step 15 — Build GPT-5.5 Review Brief**

Create GPT55_REVIEW_BRIEF.md (most important artifact).

**Step 16 — Build Handoff**

Create HANDOFF.md for GPT-5.5 Pro.

**Step 17 — Final Capture**

Run final git status/diff, append to COMMAND_LOG.md.

---

## 8. Required Schema Rules

All schemas must be strict.

Use `"additionalProperties": false` for every object unless clearly documented reason not to.

Do not allow arbitrary strings for dangerous fields:
- backend_id, runner_id, model_id, tool_id
- path, url, port, shell_command
- mcp_server, mcp_tool, workflow_name, github_action

Represent via controlled enum or registry reference with evidence fields.

---

## 9. Required Enum Values

**Risk classes**: R0_READ, R1_DOCS, R2_TESTS, R3_CODE, R4_CROSS_BOUNDARY, R5_SECURITY_AUTH_CI, R6_LIVE_WRITE, R7_FORBIDDEN

**Decision statuses**: PROPOSED, READY_DESIGN_ONLY, READY_DRY_RUN_ONLY, BLOCKED, NEEDS_SUPERVISOR, FORBIDDEN

**Backend authority**: backend_only, validation_only, read_only, adapter, advisory, forbidden, unknown

**Evidence quality**: observed_clean_origin_main, observed_current_branch, observed_config_only, observed_runtime_healthy, observed_runtime_unhealthy, vendor_only, claimed_only, conflicting, unknown

**Safe automation class**: safe_read, safe_projection, requires_operator, unsafe_until_proven, forbidden, unknown

**Auditor verdict**: PASS, PASS_WITH_RISKS, FAIL, NEEDS_SUPERVISOR, SKIPPED, NOT_RUN

**Validation state**: NOT_STARTED, IN_PROGRESS, PASSED, FAILED, PARTIAL, BLOCKED

**Important**: `auditor_verdict` and `validation_state` are different fields. Do not merge them.

---

## 10. Required Test Assertions

Test file must assert 15 conditions (see packet for full list).

---

## 11. Required Domain Doc Content

Domain doc must state that 0001 is design-only, does not implement routing, does not prove runtime health, does not lock model slots, does not make OpenCode authoritative, etc.

---

## 12. Helper Agent Prompts

See packet for exact prompt content for all 7 prompts.

---

## 13. Completion Rules

May mark complete only if:
1. All allowed files created or intentionally omitted with reason
2. No forbidden files touched
3. JSON schemas parse
4. Fixtures parse
5. Tests pass
6. Diff allowlist passes
7. Proof files exist
8. GPT55_REVIEW_BRIEF.md exists
9. AUDITOR_A_REPORT.md exists or NOT_RUN with reason
10. AUDITOR_B_REPORT.md exists or NOT_RUN with reason
11. PROOF.json records all carried risks
12. HANDOFF.md tells GPT-5.5 Pro what to review

If any auditor returns FAIL or NEEDS_SUPERVISOR, status is `BLOCKED_NEEDS_SUPERVISOR`.

---

## 14. Final Output Required From OpenCode

Return exact report format with Status, Files Changed, Diff Stat, Commands Run, Validation, Auditor Results, Proof Artifacts, Carried Risks, Stop Conditions, What GPT-5.5 Pro should review.

Do not say "done" without this report.
