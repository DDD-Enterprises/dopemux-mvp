# TP-DCP-0002 — Independent Audit (Opus)

**Packet**: TP-DCP-0002 — Derive Mutation Classes, Approval Artifact, Project Resource Map
**Branch**: `dcp/contract-derivation-tp-0002`
**HEAD commit**: `c426afdee` (`c426afdeed2aea721a878f1a9122b448ce203fa8`)
**Base**: `main` @ `68f7435f6` (TP-DCP-0001 merge)
**Audit date**: 2026-06-03
**Implementer identity**: Sonnet (claude-sonnet-4-6)
**Auditor identity**: Opus (this audit) — distinct from implementer

---

## VERDICT: PASS_WITH_RISKS

All 18 criteria are substantively met. No criterion FAILED. One criterion (17, proof
freshness) is **PARTIAL**: the committed PROOF.json still reads `commit_sha: "PENDING —
updated after commit"`; the correct value `c426afdee` exists only as an **uncommitted**
working-tree edit. This is the same SHA-fixed-point bootstrap that TP-DCP-0001 resolved
with a dedicated follow-up commit (`b57201583`) and is a process/freshness note, not a
contract or scope violation. Residual `.v0` risks (3 PROVISIONAL mutation classes, several
SYNTHESIS_INVENTED fields) are all by-design for a derivation packet and correctly tagged,
which is why the verdict is PASS_WITH_RISKS rather than plain PASS.

---

## Method

Independent of the implementer's PROOF.json. Steps performed by the auditor:

1. Read all 11 implementation/proof files in the worktree.
2. Verified authority-source ground truth directly against repo runtime code/config
   (`policy.py` constants, `proof.py` status vocab, `approval_policy.yaml` tier registry,
   `queue_drain.py:2402` `execute=True`, existence of `batch_resolve_and_merge.py` and
   `steward_gate.py`).
3. Re-ran the full DCP test suite independently: `python3 -m pytest tests/dcp -q` → **25 passed**.
4. Ran the optional negative tests directly against the fixtures (posture, requester≠approver,
   endpoint vocab, red-line presence, LIVE_WRITE_READY property-key scan).
5. Verified git scope: `git diff --name-status 68f7435f6 c426afdee` (12 files, all in
   allowlist, zero forbidden paths) and tree status.
6. Spot-checked that REPO_VALIDATED path claims in the resource map exist on disk.

---

## Criteria Table (TP-DCP-0002 §15)

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Scope limited to the three contracts (no out-of-scope changes) | **PASS** | `git diff --name-status 68f7435f6 c426afdee`: 12 files — 3 schemas, 3 fixtures, 1 new test, `test_dcp_contracts.py` (defer-guard flip), `README.md`, `TP-DCP-0002.md`, `PROOF.json`, `DERIVATION_NOTES.md`. All in the §7 allowlist. |
| 2 | No forbidden files touched (merge_specialist except read-only, `batch_resolve_and_merge.py`, `.github/workflows/`) | **PASS** | Grep of diff name-list against forbidden prefixes → "NO FORBIDDEN PATHS". `test_16` re-run confirms. |
| 3 | No import/call/wrap of merge-specialist code | **PASS** | Sole added `.py` (`test_dcp_0002_contract_derivation.py`) imports only `json, subprocess, sys, pathlib, jsonschema` — no merge-specialist module. `test_11` (schema string scan) and `test_16` (git diff guard) both pass. Criterion is about imports/calls, satisfied beyond the schema-string check. |
| 4 | DCP-RED-MERGE-SEAM-0001 remains a hard block (`MC-MERGE-SEAM-FORBIDDEN`: `side_effect_posture=hard_block`, `approval_tier=HARD_BLOCK`) | **PASS** | Fixture NT1: `side_effect_posture=hard_block`, `approval_tier=HARD_BLOCK`, `allowed_in_v1=False`, `live_write_ready_required=False`, `red_lane_triggers=[DCP-RED-MERGE-SEAM-0001]`, `provenance=REPO_VALIDATED_BY_AUDIT`. `test_13` enforces all of these. |
| 5 | LIVE_WRITE_READY not defined in any schema | **PASS** | Property-key/enum scan across all `schemas/dcp/*.schema.json` → none. The token appears only as substring text in descriptions (documenting it is forbidden) and within the *flag* name `live_write_ready_required` (a per-class gate-requirement boolean, not the gate definition). `test_9` passes. |
| 6 | No live external writes (contract-only, read-only derivation) | **PASS** | All changes are schema/fixture/doc/test files. `test_17` (structural: no network/API). `PROOF.json live_writes_performed=false`. No runtime code added. |
| 7 | Contract-level provenance present (provenance block: tag + source_ref) | **PASS** | All three schemas declare `provenance{tag,source_ref}` + `validation{state,notes}` in `properties` and `required`; all three fixtures carry populated blocks. `test_4` passes. |
| 8 | Field-level provenance covers all data fields (`field_provenance`) | **PASS** | All three fixtures carry `field_provenance` covering every top-level data field. `test_5`/`test_6` pass. NOTE: coverage is **top-level**, matching the TP-DCP-0001 `test_per_field_provenance_coverage` convention; nested array-element fields (`classes[]`, `endpoint_bindings[]`) carry their own per-entry `provenance`/`provenance_tag` instead. |
| 9 | Repo-derived fields cite repo evidence in derivation notes | **PASS** | `DERIVATION_NOTES.md` §2–§5 tables map each field to a concrete repo source; auditor independently confirmed the cited constants/lines match ground truth (see Authority Verification below). |
| 10 | External/invented fields not promoted to repo authority | **PASS** | `test_8` (no-laundering) passes. Mutation-class per-class provenance: 13 REPO_VALIDATED, 1 REPO_VALIDATED_BY_AUDIT, 3 PROVISIONAL — the 3 PROVISIONAL classes all carry `approval_tier=PROVISIONAL` (no elevation to a concrete tier). SYNTHESIS_INVENTED fields in the approval artifact (`expiry_window`, `explicit_exclusions`, etc.) are tagged SYNTHESIS_INVENTED in `field_provenance`, not REPO_VALIDATED. |
| 11 | ConPort/dope-memory endpoint uncertainty preserved (bindings PROVISIONAL/UNKNOWN) | **PASS** | NT3: every `endpoint_bindings` entry is PROVISIONAL or UNKNOWN (conport, qdrant-dope-context = PROVISIONAL; working-memory-assistant = UNKNOWN; adhd-engine = PROVISIONAL). Schema enum hard-constrains `binding_status`/`provenance_tag` to `{PROVISIONAL, UNKNOWN}`. `test_15` passes. |
| 12 | Task-Orchestrator non-authority for DCP (surfaces listed, not elevated) | **PASS** | `task_orchestrator_surfaces` lists ORCH-TRANSITION (T4) and ORCH-QUEUE-STATUS (T0) with `canonical_writer=task-orchestrator`; description states "Task-Orchestrator is not DCP authority". Not added to DCP authority pointers. |
| 13 | Dopetask execution out of scope (`MC-DOPETASK-EXEC` describes, does not execute; `allowed_in_v1=false`) | **PASS** | `MC-DOPETASK-EXEC`: `approval_tier=PROVISIONAL`, `allowed_in_v1=false`, `provenance=PROVISIONAL`, known_unknowns explicitly note "DCP must not execute Dopetask". `dopetask_surfaces` mark wrappers `wrapper_only` and external `external_out_of_scope`. |
| 14 | Approval artifact is not a write executor (no live-write fields; `supervisor_signoff.provided=false`) | **PASS** | NT2: `supervisor_signoff.provided=false`. No `live_*`/`execute_*`/`merge_authorized` field exists (`test_10` confirms no live-write indicators). Schema description: "does NOT execute the mutation and must not become a write executor." Derivation notes record `live_execution_permission` and `merge_authorized` were attempted and REJECTED. |
| 15 | Project resource map does not bind live endpoints as truth | **PASS** | Same as #11; all endpoint bindings PROVISIONAL/UNKNOWN; derivation notes record live-URL-as-REPO_CROSS_CHECKED was attempted and REJECTED. |
| 16 | Tests pass | **PASS** | Auditor re-ran `python3 -m pytest tests/dcp -q` → `25 passed in 0.12s` (8 TP-DCP-0001 + 17 TP-DCP-0002), matching PROOF.json's claim. |
| 17 | Proof fresh to final commit (`commit_sha` = `c426afdee`) | **PARTIAL** | `git rev-parse HEAD` = `c426afdee` ✓. The **working-tree** PROOF.json reads `commit_sha: c426afdee` ✓. BUT the **committed** PROOF.json (`git show HEAD:proof/TP-DCP-0002/PROOF.json`) reads `commit_sha: "PENDING — updated after commit"`. The correct SHA exists only as an uncommitted edit (`git status`: ` M proof/TP-DCP-0002/PROOF.json`; diff = only the `PENDING → c426afdee` line). A file committed in commit X cannot embed X's own SHA without a follow-up commit — TP-DCP-0001 used `b57201583` for exactly this. The committed bundle is therefore not yet SHA-fresh. See Residual Risks. |
| 18 | Auditor and implementer distinct | **PASS** | Implementer = Sonnet (claude-sonnet-4-6, per PROOF.json/TP/DERIVATION_NOTES); auditor = Opus (this file). Approval fixture also models this: `requester=claude-sonnet-implementer` ≠ `approver=claude-opus-auditor`. |

---

## Authority Verification (independent ground-truth)

| Claim (from DERIVATION_NOTES) | Ground truth (auditor-verified) | Match |
|-------------------------------|----------------------------------|-------|
| `REQUIRED_TIERS = [T0..T6, TX, TU]` | `policy.py:20` identical | ✓ |
| `WRITE_MODES = {write, destructive}` | `policy.py:21` identical | ✓ |
| `T4_PLUS = {T4,T5,T6}` | `policy.py:22` identical | ✓ |
| `REFUSAL_TIERS = {TX,TU}` | `policy.py:23` identical | ✓ |
| `ALLOWED_PROOF_STATUSES` (7 values) | `proof.py:12-20` identical; schema `freshness_state` = those 7 + `UNKNOWN` (documented) | ✓ |
| Tier registry names/modes/decisions (T0-T6/TX/TU) | `approval_policy.yaml` `tiers:` block matches the derivation table row-for-row | ✓ |
| `queue_drain.py` `execute=True` at line 2402 | `queue_drain.py:2402` `merge_res = execute_or_dry_run(merge_cmd, execute=True, ...)` confirmed | ✓ |
| `scripts/batch_resolve_and_merge.py` exists | present (2724 bytes) | ✓ |
| `steward_gate.py` now present (was absent at TP-DCP-0001) | present (6078 bytes); README + fixtures correctly note it does not remove the hard block | ✓ |
| Resource-map REPO_VALIDATED paths (`.repo_id`, `vendor/dopetask`, `scripts/taskx`, `scripts/dopetask`, `src/dopemux`, `src/dopemux_pr_steward`, `services/adhd_engine`, `tools/pr_action_bridge`) | all exist on disk | ✓ |

---

## Test Run Output (auditor, independent)

```
$ cd /Users/hue/code/dopemux-mvp-wt-dcp-build && python3 -m pytest tests/dcp -q
.........................                                                 [100%]
$ python3 -m pytest tests/dcp -v   (tail)
============================== 25 passed in 0.12s ==============================
```

Negative tests (auditor-run, all confirmed):
```
NT1 MC-MERGE-SEAM-FORBIDDEN: side_effect_posture=hard_block, approval_tier=HARD_BLOCK,
    allowed_in_v1=False, live_write_ready_required=False               -> as required
NT2 approval: requester='claude-sonnet-implementer' approver='claude-opus-auditor'
    distinct=True; supervisor_signoff.provided=False                   -> as required
NT3 endpoint_bindings out-of-vocab: NONE (all PROVISIONAL/UNKNOWN)     -> as required
NT4 LIVE_WRITE_READY property-key scan across all schemas: none        -> as required
NT5 DCP-RED-MERGE-SEAM-0001 in red_lines of all three fixtures: True   -> as required
```

Git scope (auditor-run):
```
$ git diff --name-only 68f7435f6 c426afdee | grep -E '^(src/dopemux_pr_merge_specialist/|scripts/batch_resolve_and_merge\.py|\.github/workflows/)'
NO FORBIDDEN PATHS
$ git status --porcelain
 M proof/TP-DCP-0002/PROOF.json     (uncommitted SHA bump only)
```

---

## Residual Risks / UNKNOWNs

1. **[Process — crit 17] Committed proof bundle is not SHA-fresh.** The committed
   PROOF.json reads `commit_sha: "PENDING — updated after commit"`; the correct value
   `c426afdee` is an uncommitted working-tree edit. Remediation: commit the PROOF.json
   SHA bump as a follow-up (as TP-DCP-0001 did with `b57201583`). Until then a
   squash-merge/orchestrator pickup that relies only on committed content will carry a
   `PENDING` SHA. Low severity (single-line, content otherwise correct), but it must be
   committed before the bundle is final. `pr_url` is also `PENDING` (expected — no PR yet).
2. **[By-design .v0] 3 PROVISIONAL mutation classes** — MC-DOPETASK-EXEC, MC-BRIDGE-MEDIATED,
   MC-EXTERNAL-WRITE — have no registered tier in `approval_policy.yaml`. Correctly tagged
   PROVISIONAL with `allowed_in_v1=false`; tier resolution deferred to a future packet.
3. **[By-design .v0] SYNTHESIS_INVENTED fields** in the approval artifact (`expiry_window`,
   `explicit_exclusions`, `approval_id`, timestamps, rationale) have no repo equivalent.
   Correctly tagged; the envelope's `validation_state` is const-pinned
   `PROVISIONAL_UNVERIFIED_ENFORCEMENT`.
4. **[By-design] All endpoint bindings PROVISIONAL/UNKNOWN** — no runtime proof in this
   checkout. Preserved per invariant §11.
5. **[Carried unknown] TRUTH_*.md / RUNTIME_AUTHORITY_POINTERS.md / PROJECT.md / PM_PLANE.md**
   referenced by AGENTS.md §2 are absent from repo root; recorded as known_unknowns. Not a
   regression introduced by this packet.
6. **[Minor nuance]** `repo_root_marker.secondary = "vendor/dopetask"` — `vendor/dopetask`
   is a directory (confirmed present), described as a "dopetask presence marker" rather than
   a literal marker file. Tagged REPO_VALIDATED at field level; the path exists, so the claim
   is true; phrasing is the only soft spot. Not a fault.

---

## Validation Summary (PASS / FAIL / NOT_RUN)

- **PASS**: criteria 1–16, 18; independent pytest (25 passed); all authority-source
  ground-truth checks; all negative tests; forbidden-path scan; path-existence spot-checks.
- **PARTIAL**: criterion 17 (committed PROOF.json `commit_sha` = `PENDING`; correct SHA only
  in uncommitted working tree).
- **FAIL**: none.
- **NOT_RUN**: live external writes / runtime endpoint resolution — intentionally out of
  scope for a contract-only `.v0` derivation packet (not a gap).

---

**Implementer identity: Sonnet | Auditor identity: Opus**
