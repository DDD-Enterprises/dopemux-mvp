---
id: TP-DMX-TRUST-GATE-FAIL-CLOSED-001
title: DCP Evidence Completeness and False-Ready Repair
type: explanation
owner: '@hu3mann'
author: Claude
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: L3 fail-closed repair for DCP red-lane scanner false PASS and control-snapshot false READY on incomplete evidence.
---
# TP-DMX-TRUST-GATE-FAIL-CLOSED-001 - DCP Evidence Completeness and False-Ready Repair

**Packet ID**: TP-DMX-TRUST-GATE-FAIL-CLOSED-001
**Repository**: DDD-Enterprises/dopemux-mvp
**Base branch**: main
**Risk lane**: L3
**Stage**: implementation
**Merge authority**: NONE (this packet does not authorize merge, close, mark-ready, force-push, history rewrite, or production mutation)

## 1. Objective

Repair the DCP control-evidence path so incomplete, malformed, stale, conflicting, or
identity-unproven evidence cannot be promoted into an unsupported `PASS` or `READY`
result.

Fixes exactly:

- `DMX-W1-04-F001` - red-lane scanner false `PASS`
- `DMX-W1-04-F002` - control snapshot false `READY`

Out of scope: MCP gate, RTE, PM, memory, lifecycle, or any other Wave 1 remediation;
F003 and later findings from the core CLI/fleet audit.

## 2. Evidence and authoring base

Deep-audit source revision: `H0=5d694cc9898e5046b5da03319f20f48599c40ca8`.

Authenticated GitHub state observed at packet authoring:
`CURRENT_MAIN=3e8fcc1c70c5b859dd651a1cd33c85eab837c93e`, `MERGE_BASE(H0,CURRENT_MAIN)=H0`,
22 commits ahead of H0, none of which touched the paths implicated in F001/F002 (verified
`git diff --stat` empty over the allowlisted paths at execution time).

`UNDEFINED_AND_BLOCKING` continues to mean live-write readiness is not operational; this
packet does not redefine it or grant live-write authority.

## 3. Scope

### IN

```text
src/dopemux/dcp/red_lane.py
src/dopemux/dcp/red_lane_scanner.py
src/dopemux/dcp/control_snapshot.py
src/dopemux/dcp/proof_family.py

tests/dcp/test_dcp_0004_control_snapshot.py
tests/dcp/test_dcp_0005_red_lane_scanner.py
tests/dcp/test_dcp_0003_proof_family_dispatch.py

tests/dcp/fixtures/tp_dcp_0004_*/

task-packets/TP-DMX-TRUST-GATE-FAIL-CLOSED-001.md
task-packets/TP-DMX-TRUST-GATE-FAIL-CLOSED-001.json

proof/TP-DMX-TRUST-GATE-FAIL-CLOSED-001/**
```

### OUT

`schemas/**`, `src/dopemux/mcp/**`, `services/**`, `src/dopemux/pm/**`,
`src/dopemux/memory/**`, `scripts/audit/**`, `.github/**`, `config/**`, `docs/**`,
existing historical `proof/**`, existing TP-DCP-0001 through TP-DCP-0005 artifacts,
PR Steward implementation, embedded-audit implementation, credentials/signers,
deployment/runtime configuration, production/service state.

## 4. Invariants

1. DCP remains a coordinator/control surface, not an execution-authority grantor.
2. `PASS` and `READY` may only derive from evidence positively established by the
   relevant control contract.
3. Missing evidence remains `UNKNOWN`.
4. Malformed or contradictory evidence remains `CONFLICTING` or blocking.
5. Stale required evidence remains blocking.
6. `UNDEFINED_AND_BLOCKING` continues to mean live-write readiness is not operational.
7. No missing guard may be silently converted to `NONE`, `PRESERVED`, or another safe
   state unless the safe fact is actually observed.
8. Missing implementer or auditor identity must not prove absence of self-certification.
9. `RedLaneScanner.main()` exits zero only for a legitimately complete `PASS`.
10. `recommended_next_action` must agree with the actual status.
11. TP-DCP-0004's own not-yet-produced proof may remain a self-generation warning; it
    must not launder missing prerequisite evidence from TP-DCP-0001 through TP-DCP-0003.
12. Valid current read-only fixtures must continue to work without inventing live-write
    authority.
13. No network, provider, GitHub mutation, service mutation, or credential access is
    required for implementation or deterministic validation.
14. One canonical proof-family classification path is preferred over another independent
    parser when practical.
15. No `DONE`, `READY`, or `PASS` claim without current evidence.

## 5. Root cause and repair

### DMX-W1-04-F001 (red_lane_scanner.py)

`_scan_artifacts` set `self_certification_status = "NONE"` in the `else` branch of
`if impl and auditor and impl == auditor`, which also covers the case where either
identity is entirely absent. An empty `{}` proof (or any proof missing one or both
identity fields) therefore produced `self_certification_status = "NONE"` — a
positively-safe claim with no supporting evidence — and no other guard in the empty-proof
case carried a literal `"UNKNOWN"` value, so `scan()`'s `is_unknown` check never fired and
`final_status` defaulted to `Status.PASS`.

Fix: split the identity branch so `NONE` is only reachable when both identities are
observed and distinct; either identity missing now yields `UNKNOWN`. A JSON parse failure
on a proof artifact (or a non-object JSON root) now raises an explicit `MALFORMED_PROOF`
BLOCKER finding instead of silently `continue`-ing past it.

### DMX-W1-04-F002 (control_snapshot.py)

`_readiness()` only special-cased `AuthorityLabel.CONFLICTING` and
`FreshnessStatus.STALE` per packet state; a prerequisite packet (TP-DCP-0001/0002/0003)
with no task-packet file and no proof at all classifies as `AuthorityLabel.UNKNOWN` but
fell through both branches untouched, leaving `blocking` empty and `status` at its
default `"READY"`.

Fix: added an `elif` branch that appends a blocking reason for any prerequisite packet
left in `UNKNOWN` or `CLAIMED` state, so missing/unproven prerequisite evidence blocks
readiness instead of being silently ignored.

## 6. Regression coverage added

`tests/dcp/test_dcp_0005_red_lane_scanner.py`: empty-proof non-PASS, head-only-proof
non-PASS, missing-implementer-identity UNKNOWN, missing-auditor-identity UNKNOWN,
distinct-identities-still-NONE (positive case), malformed-proof non-PASS with
`MALFORMED_PROOF` finding, no-proof-paths non-PASS, CLI nonzero exit on incomplete proof.

`tests/dcp/test_dcp_0004_control_snapshot.py`: new fixture
`tests/dcp/fixtures/tp_dcp_0004_missing_tp0002_evidence/` (a copy of the existing valid
fixture with all TP-DCP-0002 task-packet and proof artifacts removed) proving readiness
is not `READY` and the blocking reason names the missing packet.

## 7. Validation gates

```bash
python -m pytest -q tests/dcp/test_dcp_0003_proof_family_dispatch.py tests/dcp/test_dcp_0004_control_snapshot.py tests/dcp/test_dcp_0005_red_lane_scanner.py
python -m pytest -q tests/dcp
git diff --check
pre-commit run --files <changed files>
```

See `proof/TP-DMX-TRUST-GATE-FAIL-CLOSED-001/` for exact command logs, results, and the
independent audit verdict.

## 8. Authority

Merge, close, mark-ready, force-push, history rewrite, branch deletion, deployment, and
production mutation are **not** authorized by this packet.
