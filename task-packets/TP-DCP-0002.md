---
id: TP-DCP-0002
title: Tp Dcp 0002
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-04'
last_review: '2026-06-04'
next_review: '2026-09-02'
prelude: Tp Dcp 0002 (explanation) for dopemux documentation and developer workflows.
---
# TP-DCP-0002 — Derive Mutation Classes, Approval Artifact, and Project Resource Map

**Packet ID**: TP-DCP-0002
**Project**: DCP — Data Control Plane
**Target**: `dcp/contract-derivation-tp-0002` branch
**Implementer**: claude-sonnet
**Auditor**: claude-opus (distinct from implementer)
**Status**: IMPLEMENTATION_COMPLETE — pending Opus audit
**Base**: `main` @ `68f7435f6` (TP-DCP-0001 merge commit)

---

## Objective

Derive and lock the next three DCP v0 contracts from repo authority:

1. `DCP_MUTATION_CLASS.v0`
2. `DCP_APPROVAL_ARTIFACT.v0`
3. `DCP_PROJECT_RESOURCE_MAP.v0`

These were intentionally deferred from TP-DCP-0001 because they had repo authority available but no locked field shape. This packet derives them from observed repo code/config/docs and adds schema/tests/fixtures/proof without creating runtime behavior.

---

## Authority Sources Inspected

| Source | Path | Status |
|--------|------|--------|
| approval_policy.yaml | `config/orchestrator/approval_policy.yaml` | REPO_VALIDATED |
| policy.py | `src/dopemux/orchestrator/policy.py` | REPO_VALIDATED |
| proof.py | `src/dopemux/orchestrator/validation/proof.py` | REPO_VALIDATED |
| ARCHITECTURE.md | `ARCHITECTURE.md` | REPO_VALIDATED |
| AGENTS.md | `AGENTS.md` | REPO_VALIDATED |
| system-boundaries.md | `docs/03-reference/systems/system-boundaries.md` | REPO_VALIDATED |
| queue_drain.py | `src/dopemux_pr_merge_specialist/queue_drain.py` | REPO_VALIDATED (execute=True line 2402) |
| batch_resolve_and_merge.py | `scripts/batch_resolve_and_merge.py` | REPO_VALIDATED (exists) |
| steward_gate.py | `src/dopemux_pr_merge_specialist/steward_gate.py` | REPO_VALIDATED (NOW PRESENT — was absent at TP-DCP-0001 audit) |
| TP-DCP-0001 schemas | `schemas/dcp/` | REPO_VALIDATED (post-#797 merge) |

Full derivation table: `proof/TP-DCP-0002/DERIVATION_NOTES.md`

---

## Files Changed

### New Files
- `schemas/dcp/dcp_mutation_class.schema.json`
- `schemas/dcp/dcp_approval_artifact.schema.json`
- `schemas/dcp/dcp_project_resource_map.schema.json`
- `tests/dcp/fixtures/tp_dcp_0002_mutation_class.fixture.json`
- `tests/dcp/fixtures/tp_dcp_0002_approval_artifact.fixture.json`
- `tests/dcp/fixtures/tp_dcp_0002_project_resource_map.fixture.json`
- `tests/dcp/test_dcp_0002_contract_derivation.py`
- `task-packets/TP-DCP-0002.md` (this file)
- `proof/TP-DCP-0002/DERIVATION_NOTES.md`
- `proof/TP-DCP-0002/PROOF.json`
- `proof/TP-DCP-0002/AUDIT.md`

### Updated Files
- `tests/dcp/test_dcp_contracts.py` — defer guard (test `(e)`) updated: deferred schemas are now present (TP-DCP-0002 delivered them); guard flipped to positive presence check
- `schemas/dcp/README.md` — update deferred contracts section

---

## Invariants Confirmed

- `LIVE_WRITE_READY` remains undefined — not defined in any schema
- DCP remains read-first and contract-first — no live writes
- DCP must not become merge authority — approval artifact is a record, not an executor
- `DCP-RED-MERGE-SEAM-0001` preserved — hard-block class `MC-MERGE-SEAM-FORBIDDEN` in mutation class registry
- `auditorVerdict` and `validationState` remain separate concepts — inherited from TP-DCP-0001
- Lifecycle status is not proof freshness — `contract_status` enum distinct from `validation_state`
- Provenance tagging required at contract and field level — all fixtures have `field_provenance`
- External DR may inform labels but not become repo authority — no DR-016 fields in these contracts
- Bridges, adapters, mirrors, indexes, retrieval outputs are never source authority — resource map marks bridge surfaces as routing-only
- ConPort and dope-memory endpoint bindings remain PROVISIONAL — all endpoint_bindings use PROVISIONAL or UNKNOWN
- Agents do not own PM truth — no agent-ownership claims in resource map
- Task-Orchestrator does not become DCP authority — orchestrator surfaces listed but not elevated
- Dopetask execution remains out of scope — `MC-DOPETASK-EXEC` class describes but does not execute
- No self-certification — implementer (Sonnet) ≠ auditor (Opus)

---

## Validation

```
python3 -m pytest tests/dcp -q
→ 25 passed (8 TP-DCP-0001 + 17 TP-DCP-0002)
git diff --check → exit 0
python3 -m json.tool <all 6 JSON files> → exit 0 for each
```

---

## Rollback

```bash
git restore schemas/dcp/dcp_mutation_class.schema.json \
            schemas/dcp/dcp_approval_artifact.schema.json \
            schemas/dcp/dcp_project_resource_map.schema.json \
            tests/dcp/test_dcp_0002_contract_derivation.py \
            tests/dcp/test_dcp_contracts.py \
            schemas/dcp/README.md
git restore tests/dcp/fixtures/tp_dcp_0002_*.fixture.json
git restore task-packets/TP-DCP-0002.md
rm -rf proof/TP-DCP-0002
```
