---
id: DMX-DCP-MODEL-ROUTING-MVP-0001R
title: Dmx Dcp Model Routing Mvp 0001R
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-13'
last_review: '2026-06-13'
next_review: '2026-09-11'
prelude: Dmx Dcp Model Routing Mvp 0001R (explanation) for dopemux documentation and
  developer workflows.
---
# Task Packet: DMX-DCP-MODEL-ROUTING-MVP-0001R

## Packet Identity

| Field | Value |
|---|---|
| **Packet ID** | `DMX-DCP-MODEL-ROUTING-MVP-0001R` |
| **Series** | `DMX-DCP-MODEL-ROUTING-MVP` |
| **Title** | Routing Domain Model Reconciliation + Minimal Core Types |
| **Repository** | `DDD-Enterprises/dopemux-mvp` |
| **Base branch** | `main` |
| **Branch** | `dcp/model-routing-0001r-routing-domain-model` |
| **Worktree** | `.worktrees/dcp-model-routing-0001r` |
| **Status** | IMPLEMENTED |
| **Risk level** | Medium |
| **Task class** | Architecture-sensitive, proof-sensitive, routing-core foundation |

---

## Why 0001R Exists

`DMX-DCP-MODEL-ROUTING-MVP-0001` (the original) was already present in
`task-packets/DMX-DCP-MODEL-ROUTING-MVP-0001.md`. That packet used
JSON schemas and JSON fixtures as its deliverable — not a Python routing
domain model. It had no `src/dopemux/dcp/routing_model.py` and no
Python-level representation of `RouteDecision`, `TaskSource`,
`RiskClass`, etc.

Reusing the `0001` ID for a Python domain-model packet would create
packet identity collision and stale-proof confusion. This `0001R` packet:

1. Inspected the existing `0001` packet and its deliverables.
2. Confirmed no equivalent Python routing domain model existed.
3. Created the minimal pure-Python domain model at `src/dopemux/dcp/routing_model.py`.
4. Added unit tests at `tests/unit/dcp/test_routing_model.py`.
5. Updated `src/dopemux/dcp/__init__.py` to export the new symbols.

---

## Existing 0001 Packet — Inspection Summary

| Item | Finding |
|---|---|
| `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0001.md` | EXISTS — dated 2026-06-10 |
| 0001 deliverable | JSON schemas + JSON fixtures + `tests/dcp/test_dcp_model_routing_0001_domain.py` |
| 0001 allowed Python files | None — no `src/dopemux/dcp/` Python modules |
| Equivalent Python routing domain model | NOT FOUND — confirmed absent |
| `routing_model.py` before this packet | NOT FOUND |
| Conflict with 0001R? | NO — different deliverable type (schemas vs Python types) |

---

## Scope

### IN
- `src/dopemux/dcp/routing_model.py` — pure Python routing domain model
- `src/dopemux/dcp/__init__.py` — routing model symbols added
- `tests/unit/dcp/test_routing_model.py` — unit tests
- `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0001R.md` — this document

### OUT (invariants enforced)
- No OpenCode implementation
- No Grok / Grok Build implementation
- No runner adapter implementation
- No Secure MCP implementation
- No MCP tool calls
- No service starts
- No Dopetask execution
- No Task Orchestrator write or transition
- No GitHub write
- No PR merge/write path
- No queue drain
- No batch merge scripts
- No ECC archive processing
- No package-manager commands
- No CI workflow edits
- No broad refactor
- No opportunistic cleanup

---

## Domain Model Summary

File: `src/dopemux/dcp/routing_model.py`

### Enumerations

| Enum | UNKNOWN member | Notes |
|---|---|---|
| `TaskSource` | ✓ | Where task originates |
| `TaskType` | ✓ | Coarse task classification |
| `RiskClass` | ✓ | Includes `RED_LANE` |
| `ComplexityClass` | ✓ | |
| `AuthorityClass` | ✓ | Includes `BLOCKED` |
| `RuntimeImpact` | ✓ | |
| `BackendKind` | ✓ | Data only, not executable |
| `ConnectorKind` | ✓ | Data only, not executable |
| `ProofRequirement` | ✓ | First-class field |
| `AuditRequirement` | ✓ | First-class field |
| `EscalationRequirement` | ✓ | |
| `RedLaneState` | ✓ | Includes `RED_LANE`, `UNKNOWN` |
| `RouteStatus` | ✓ | Includes `BLOCKED`, `PENDING` |

### RouteDecision dataclass fields

```
route_id, task_source, task_type, risk_class, complexity_class,
authority_class, runtime_impact, backend_kind, connector_kind,
proof_requirements, audit_requirement, escalation_requirement,
red_lane_state, allowed_actions, forbidden_actions, stop_conditions,
evidence_refs, unknowns, confidence, status
```

### Invariants upheld

| Invariant | How |
|---|---|
| Default confidence ≠ VERIFIED | `confidence = "LOW"` |
| Default status ≠ runnable | `status = RouteStatus.PENDING` |
| UNKNOWN authority ≠ runnable | `is_runnable()` checks explicitly |
| RED_LANE overrides ALLOWED | `is_runnable()` checks `red_lane_state is not CLEAR` |
| UNKNOWN red-lane is fail-closed | `is_runnable()` requires `CLEAR` specifically |
| No I/O | stdlib only: `dataclasses`, `enum`, `typing` |
| No runner/connector imports | verified by static scan + import-purity test |
| UNKNOWN representable | every enum has `UNKNOWN` member |
| BLOCKED representable | `RouteStatus.BLOCKED`, `AuthorityClass.BLOCKED` |
| RED_LANE representable | `RiskClass.RED_LANE`, `RedLaneState.RED_LANE` |
| Proof requirements first-class | `proof_requirements: list[ProofRequirement]` |
| Audit requirement first-class | `audit_requirement: AuditRequirement` |
| Backend/connector = data only | enum fields, no callable behavior |
| No live-write state | no such field or method |
| No merge-readiness claim | not present |

---

## Validation Results

| Check | Result |
|---|---|
| `python -m compileall -q src/dopemux/dcp` | PASS (exit 0) |
| `pytest -v tests/unit/dcp/test_routing_model.py` | PASS — 46/46 passed |
| `git diff --check` | PASS |
| Static no-go scan (forbidden imports in routing_model.py) | PASS — none found |
| Import smoke test | PASS — `routing_model_import=ok` |

---

## Embedded Audit Report

```
auditor_tool: embedded_self (AGY / Antigravity Gemini CLI)
auditor_model: Claude Sonnet 4.6 (Thinking)
invocation: embedded inline review of diff and proof
exit_code: N/A (non-executable audit)

auditor_verdict: PASS_WITH_RISKS

auditor_findings:
  1. PASS — Scope stayed inside allowed files only.
  2. PASS — Existing 0001 packet inspected; confirmed different deliverable type (schemas vs Python).
  3. PASS — Domain model performs no I/O (stdlib only: dataclasses, enum, typing).
  4. PASS — Domain model imports no external runner or connector clients.
  5. PASS — Domain model does not invoke shell, network, GitHub, MCP, Dopetask, OpenCode, Grok, ECC, Docker, or package managers.
  6. PASS — UNKNOWN, BLOCKED, and RED_LANE states are represented as first-class enum members.
  7. PASS — ProofRequirement and AuditRequirement are first-class fields on RouteDecision.
  8. PASS — Tests cover: serialization (to_dict/from_dict round-trip), UNKNOWN defaults, BLOCKED state, RED_LANE state, red-lane override, fail-closed UNKNOWN gate, proof requirements, audit requirements, import purity.
  9. PASS — No live-write readiness implied.
  10. PASS — No PR merge/readiness claim made.
  11. PASS — No stale evidence. All evidence is from direct file inspection in this session.
  12. PASS — No runners, connectors, Secure MCP, ECC, Dopetask, or Task Orchestrator implemented.

risks:
  - RISK_1 (LOW): pytest.ini uses `pythonpath = src` but the installed venv package shadows the worktree src/. Tests require PYTHONPATH=src prefix when run from the worktree. This is a local test-runner ergonomics issue, not a correctness issue. The installed package should be updated (pip install -e .) after this branch is merged to main.
  - RISK_2 (LOW): `tests/unit/dcp/__init__.py` was created to make the test directory a proper Python package. If existing test discovery assumes no __init__.py, check for conflicts.
  - RISK_3 (INFO): The 0001 test `test_dcp_model_routing_0001_domain.py` in `tests/dcp/` uses JSON schemas from `schemas/dcp/`. These schemas are a separate deliverable from this Python domain model. No conflict exists.

fixes_applied_from_audit:
  - Fixed `is_runnable()` to be fail-closed for UNKNOWN red-lane state (requires `CLEAR` specifically, not just `not RED_LANE`).

remaining_risks:
  - See RISK_1 above (venv PYTHONPATH ergonomics).
  - Agent runtime authority remains UNKNOWN per AGENTS.md §6.
  - Routing plane is not production-ready (this is only a domain model).
```

---

## Files Changed

```
src/dopemux/dcp/routing_model.py          (NEW — 310 lines)
src/dopemux/dcp/__init__.py               (MODIFIED — added routing model exports)
tests/unit/dcp/__init__.py                (NEW — empty package marker)
tests/unit/dcp/test_routing_model.py      (NEW — 46 unit tests)
task-packets/DMX-DCP-MODEL-ROUTING-MVP-0001R.md  (NEW — this document)
```

> **Note on proof files:** Per packet §17, proof files are only created if
> "proof directories are allowed by repo convention and supervisor packet
> allowlist is updated to include them." The `proof/DMX-DCP-MODEL-ROUTING-MVP-0001R/`
> path is outside the allowlist for this packet. Proof is returned in this
> response and in this document. `proof_files_created: false`,
> `proof_returned_in_response: true`.

---

## Stop Conditions Triggered

None.

---

## Remaining Risks

1. Installed venv package shadows worktree src — tests need `PYTHONPATH=src` until `pip install -e .` is re-run post-merge.
2. Agent runtime authority is UNKNOWN per `AGENTS.md` §6.
3. Routing plane is not production-ready — this packet delivers domain model only.

---

## Explicit Non-Claims

- DCP is NOT complete.
- Routing plane is NOT production-ready.
- OpenCode is NOT integrated.
- Grok is NOT integrated.
- Secure MCP is NOT implemented.
- ECC is NOT adopted.
- Dopetask execution is NOT enabled.
- Task Orchestrator state is NOT current.
- CI is NOT claimed clean.
- Live writes are NOT allowed.

Completion means only: **Minimal routing domain model was reconciled, implemented, tested, and audited within this packet scope.**

---

## Next Packet Recommendation

`DMX-DCP-MODEL-ROUTING-MVP-0002` — Routing Classification Engine:
Create a pure-function classifier that maps task attributes to a
`RouteDecision` skeleton, using `routing_model.py` types as input/output.
No live backends. No connector calls. Pure function + tests.
