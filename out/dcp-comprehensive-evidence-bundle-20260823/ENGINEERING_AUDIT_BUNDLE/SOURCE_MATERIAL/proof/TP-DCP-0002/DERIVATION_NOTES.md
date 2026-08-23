# TP-DCP-0002 — Derivation Notes

**Packet**: TP-DCP-0002
**Branch**: `dcp/contract-derivation-tp-0002`
**Derivation date**: 2026-06-04
**Implementer**: claude-sonnet (Sonnet)
**Base**: `main` @ `68f7435f6` (TP-DCP-0001 merge commit)

---

## 1. Sources Inspected

| Source | Path | Exists | Status |
|--------|------|--------|--------|
| approval_policy.yaml | `config/orchestrator/approval_policy.yaml` | YES | REPO_VALIDATED |
| policy.py | `src/dopemux/orchestrator/policy.py` | YES | REPO_VALIDATED |
| proof.py | `src/dopemux/orchestrator/validation/proof.py` | YES | REPO_VALIDATED |
| ARCHITECTURE.md | `ARCHITECTURE.md` | YES | REPO_VALIDATED |
| AGENTS.md | `AGENTS.md` | YES | REPO_VALIDATED |
| system-boundaries.md | `docs/03-reference/systems/system-boundaries.md` | YES | REPO_VALIDATED |
| queue_drain.py | `src/dopemux_pr_merge_specialist/queue_drain.py` | YES | REPO_VALIDATED |
| batch_resolve_and_merge.py | `scripts/batch_resolve_and_merge.py` | YES | REPO_VALIDATED |
| steward_gate.py | `src/dopemux_pr_merge_specialist/steward_gate.py` | YES | REPO_VALIDATED (was ABSENT at TP-DCP-0001 audit; now present — see note) |
| TP-DCP-0001 schemas | `schemas/dcp/` | YES | REPO_VALIDATED (on main post-#797 merge) |
| TP-DCP-0001 fixture | `tests/dcp/fixtures/dcp_core_fixture.json` | YES | REPO_VALIDATED |
| SYSTEM_BOUNDARIES.md (root) | `SYSTEM_BOUNDARIES.md` | MISSING | Use `docs/03-reference/systems/system-boundaries.md` per ARCHITECTURE.md §7 |
| TRUTH_INTERFACES.md | `TRUTH_INTERFACES.md` | MISSING | UNKNOWN |
| TRUTH_SYSTEMS.md | `TRUTH_SYSTEMS.md` | MISSING | UNKNOWN |
| TRUTH_CANONICALS.md | `TRUTH_CANONICALS.md` | MISSING | UNKNOWN |
| TRUTH_GAPS.md | `TRUTH_GAPS.md` | MISSING | UNKNOWN |
| RUNTIME_AUTHORITY_POINTERS.md | `RUNTIME_AUTHORITY_POINTERS.md` | MISSING | UNKNOWN |
| dopetask-canonical-spec.json | `schemas/dopetask-canonical-spec.json` | MISSING | UNKNOWN — no validation spec in repo |
| PROJECT.md | `PROJECT.md` | MISSING | UNKNOWN |
| PM_PLANE.md | `PM_PLANE.md` | MISSING | UNKNOWN |
| contracts/ | `contracts/` | MISSING | UNKNOWN |

**steward_gate.py note**: At TP-DCP-0001 audit time, `steward_gate.py` was ABSENT from `origin/main`. It is now present (`src/dopemux_pr_merge_specialist/steward_gate.py`) as of the ADHD cognitive-remediation stack merge (#798). The TP-DCP-0001 fixture for `DCP-RED-MERGE-SEAM-0001` noted "steward_gate.py absent." That fixture reflects the audit-time truth. The current truth is that steward_gate.py IS present and enforces a merge gate. This does NOT remove the red lane — both merge-seam paths (`queue_drain.py` execute=True, `batch_resolve_and_merge.py`) remain forbidden for DCP — but the "absent" note in the fixture is now stale. TP-DCP-0002 derivation notes this discrepancy without modifying the TP-DCP-0001 fixture.

---

## 2. Key Findings Per Source

### 2.1 `config/orchestrator/approval_policy.yaml`
**Provenance**: REPO_VALIDATED

Tier registry (verbatim IDs and modes from file):
| Tier | Name | Mode | automatic_allowed | approval_required | receipt_required | decision |
|------|------|------|-------------------|-------------------|------------------|----------|
| T0 | Read-only status | read | true | false | false | allow |
| T1 | Local analysis | analysis | true | false | true | allow |
| T2 | Draft artifact | draft | false | true | true | draft_only |
| T3 | Repo-local docs edit | write | false | true | true | gated |
| T4 | Source, config, or runtime state | write | false | true | true | gated |
| T5 | GitHub mutation | write | false | true | true | gated |
| T6 | Destructive, deploy, or release | destructive | false | true | true | gated |
| TX | Unknown | unknown | false | false | true | refuse |
| TU | Unclassified | unknown | false | false | true | refuse |

Relevant capabilities with canonical writers:
- `orchestrator.memory.record_decision` → canonical_writer: ConPort, tier: T4
- `orchestrator.memory.record_progress` → canonical_writer: ConPort, mirror_writer: dope-memory, tier: T4
- `orchestrator.github.merge` → canonical_writer: GitHub, tier: T5, typed_confirmation_required: true
- `orchestrator.github.comment` → canonical_writer: GitHub, tier: T5
- `orchestrator.transition.apply` → canonical_writer: task-orchestrator, tier: T4
- `orchestrator.proof.validate` → canonical_writer: proof-bundle-governance, tier: T1
- `orchestrator.destructive.clear_index` → canonical_writer: dope-context, tier: T6, decision: block
- `orchestrator.route.pm` → tier: TX, bridge_mediated: true, decision: refuse
- `orchestrator.context.refresh_index` → canonical_writer: dope-context, tier: T4

### 2.2 `src/dopemux/orchestrator/policy.py`
**Provenance**: REPO_VALIDATED

Key constants:
- `REQUIRED_TIERS = ["T0", "T1", "T2", "T3", "T4", "T5", "T6", "TX", "TU"]`
- `WRITE_MODES = {"write", "destructive"}`
- `T4_PLUS = {"T4", "T5", "T6"}`
- `REFUSAL_TIERS = {"TX", "TU"}`
- `DEFAULT_POLICY_PATH = Path("config/orchestrator/approval_policy.yaml")`

Dataclass fields for mutation/approval derivation:
- `AutomationTier`: id, name, mode, automatic_allowed, approval_required, receipt_required, decision, typed_confirmation_required
- `CapabilityPolicy`: capability_id, title, tier, mode, canonical_writer, automatic_allowed, approval_required, receipt_required, typed_confirmation_required, bridge_mediated, upstream_canonical_writer, mirror_writer, decision
- `CapabilityDecision`: capability_id, tier, mode, canonical_writer, automatic_allowed, approval_required, receipt_required, decision, allowed, reason, typed_confirmation_required

Business rule (line ~260): `allowed = (decision == "allow" and automatic_allowed and not approval_required and tier in {"T0", "T1"})`

### 2.3 `src/dopemux/orchestrator/validation/proof.py`
**Provenance**: REPO_VALIDATED

Proof status vocabulary (for DCP_APPROVAL_ARTIFACT freshness_state):
- `ALLOWED_PROOF_STATUSES`: PLAN_ONLY, SPECIFICATION_COMPLETE, IMPLEMENTATION_STARTED, IMPLEMENTATION_COMPLETE, READY_FOR_REVIEW, VERIFIED, BLOCKED
- `ALLOWED_VALIDATION_STATES`: NOT_STARTED, IN_PROGRESS, PASSED, FAILED, PARTIAL
- `READY_STATUSES`: READY_FOR_REVIEW, VERIFIED

### 2.4 `src/dopemux_pr_merge_specialist/queue_drain.py`
**Provenance**: REPO_VALIDATED_BY_AUDIT

- Line 23: imports `execute_or_dry_run` from `.runtime`
- Line 2402: `merge_res = execute_or_dry_run(merge_cmd, execute=True, ...)` — LIVE MERGE SEAM
- `queue_drain` function defined at line 2435
- `DCP-RED-MERGE-SEAM-0001` applies: DCP must never call/import/wire this path with `execute=True`

### 2.5 `ARCHITECTURE.md`
**Provenance**: REPO_VALIDATED

Major resource planes and authorities:
- Operator/control: `src/dopemux/` — CLI, startup, routing
- Execution: `scripts/taskx` → `scripts/dopetask` → external dopetask
- PM: split (Leantime, task-orchestrator, ConPort, dope-memory)
- Memory: split (dope-memory chronicle, ConPort structured, working-memory-assistant snapshot)
- Retrieval: split (dope-context deterministic, ConPort semantic/graph)
- Adapter/bridge: `dopecon-bridge` — routing/proxy, NOT authority
- Cognitive/operator-support: ADHD Engine — operator support, NOT PM/memory authority

Canonical source roots (observed):
- `src/dopemux/` — primary operator surface
- `src/dopemux_pr_merge_specialist/` — merge specialist (FORBIDDEN for DCP import)
- `src/dopemux_pr_steward/` — steward service
- `services/` — microservices
- `config/orchestrator/` — policy authority
- `schemas/` — contract schemas
- `tests/` — test suite
- `proof/` — proof bundles
- `task-packets/` — task packets
- `scripts/` — wrapper scripts (some forbidden)

---

## 3. Derivation Table — DCP_MUTATION_CLASS

| Class ID | Conceptual Posture | Tier | Mode | Derived From | Provenance | Confidence | Unknowns |
|----------|--------------------|------|------|--------------|------------|------------|---------|
| MC-READ-ONLY | No mutation | T0 | read | approval_policy.yaml T0 | REPO_VALIDATED | HIGH | None |
| MC-ANALYSIS | Local analysis only | T1 | analysis | approval_policy.yaml T1 | REPO_VALIDATED | HIGH | None |
| MC-LOCAL-ARTIFACT-DRAFT | Local draft artifact write | T2 | draft | approval_policy.yaml T2 | REPO_VALIDATED | HIGH | None |
| MC-REPO-DOCS | Repo-local docs edit | T3 | write | approval_policy.yaml T3 | REPO_VALIDATED | HIGH | None |
| MC-SCHEMA-CONTRACT | Schema/contract write | T4 | write | approval_policy.yaml T4 + capability canonical_writer=proof-bundle-governance | REPO_VALIDATED | HIGH | promotion path to REPO_CROSS_CHECKED undefined |
| MC-PROOF-ARTIFACT | Proof artifact write | T4 | write | approval_policy.yaml T4 + proof.py ALLOWED_PROOF_STATUSES | REPO_VALIDATED | HIGH | None |
| MC-SOURCE-CONFIG | Repo source/config write | T4 | write | approval_policy.yaml T4 mode=write | REPO_VALIDATED | HIGH | None |
| MC-CI-WORKFLOW | CI/workflow/config mutation | T4 | write | approval_policy.yaml T4 (config edits per tier description) | REPO_VALIDATED | MEDIUM | workflow-specific gating not fully enumerated in capabilities |
| MC-CONPORT-WRITE | ConPort authority write | T4 | write | policy.py canonical_writer=ConPort in capabilities | REPO_VALIDATED | HIGH | ConPort endpoint binding PROVISIONAL |
| MC-ORCHESTRATOR-WRITE | Task-Orchestrator write | T4 | write | policy.py canonical_writer=task-orchestrator; orchestrator.transition.apply T4 | REPO_VALIDATED | HIGH | task-orchestrator runtime authority partially conflicted (ARCHITECTURE.md §4 note) |
| MC-MEMORY-WRITE | Memory/chronicle/context write | T4 | write | policy.py mirror_writer=dope-memory; dope-memory chronicle per ARCHITECTURE.md | REPO_VALIDATED | MEDIUM | durable ledger authority for dope-memory vs ConPort split (ARCHITECTURE.md §3.4) |
| MC-GITHUB-MUTATION | GitHub mutation | T5 | write | approval_policy.yaml T5; orchestrator.github.* capabilities | REPO_VALIDATED | HIGH | typed_confirmation varies by sub-action |
| MC-DESTRUCTIVE | Destructive/deploy/release | T6 | destructive | approval_policy.yaml T6; orchestrator.destructive.clear_index | REPO_VALIDATED | HIGH | None |
| MC-DOPETASK-EXEC | Dopetask execution | PROVISIONAL | external | ARCHITECTURE.md §3.2 execution plane; scripts/dopetask | PROVISIONAL | LOW | No explicit tier in approval_policy.yaml; no capability entry; execution plane ownership unclear beyond wrapper path |
| MC-BRIDGE-MEDIATED | Bridge/proxy-mediated write | TX→PROVISIONAL | write | policy.py bridge_mediated=true; orchestrator.route.pm tier=TX | REPO_VALIDATED (bridge_mediated field); PROVISIONAL (tier mapping) | MEDIUM | TX refuses bridge-mediated writes by default; any bridge-mediated write path is PROVISIONAL until classified |
| MC-EXTERNAL-WRITE | CRM/channel/external write | T5-T6 | write | ARCHITECTURE.md external surfaces; approval_policy.yaml T5-T6 scope | PROVISIONAL | LOW | No explicit capability for CRM/channel; tier mapping inferred from T5/T6 GitHub-equivalent mutation posture |
| MC-MERGE-SEAM-FORBIDDEN | Forbidden merge automation seam | HARD_BLOCK | destructive | queue_drain.py execute=True line 2402; DCP-RED-MERGE-SEAM-0001 | REPO_VALIDATED_BY_AUDIT | CERTAIN | steward_gate.py now present but does not remove the hard block — DCP must never import/call queue_drain.py regardless of gate state |

**Rejected overclaims:**
- Tried to derive a "LIVE_WRITE_READY" class — REJECTED. LIVE_WRITE_READY is explicitly undefined and must remain undefined per TP-DCP-0002 §9.1 and TP-DCP-0001 invariants.
- Tried to promote MC-DOPETASK-EXEC to T4 — REJECTED. No approval_policy.yaml capability maps to Dopetask execution. PROVISIONAL is correct.
- Tried to map MC-BRIDGE-MEDIATED to a single tier — REJECTED. orchestrator.route.pm is TX (refuse); bridge-mediated writes have no automatic tier mapping. Left as PROVISIONAL.

---

## 4. Derivation Table — DCP_APPROVAL_ARTIFACT

| Field | Derived From | Source | Provenance | Confidence | Unknowns |
|-------|-------------|--------|------------|------------|---------|
| approval_id | Standard identity pattern | SYNTHESIS_INVENTED | SYNTHESIS_INVENTED | HIGH | None |
| schema_version | TP-DCP-0001 pattern const `.v0` | TP-DCP-0001 convention | REPO_VALIDATED (TP-DCP-0001) | HIGH | None |
| project_id | ARCHITECTURE.md §2 | ARCHITECTURE.md | REPO_VALIDATED | HIGH | None |
| repo_id | .repo_id marker (AGENTS.md §4.1) | AGENTS.md | REPO_VALIDATED | HIGH | None |
| requested_action_summary | CapabilityPolicy.title pattern | policy.py | REPO_VALIDATED | HIGH | None |
| mutation_class | DCP_MUTATION_CLASS class_id vocab | This packet (MC-* classes) | REPO_VALIDATED (tier vocab) | HIGH | None |
| approval_tier | REQUIRED_TIERS from policy.py | policy.py | REPO_VALIDATED | HIGH | None |
| requester | Invariant: requester != approver (anti-self-cert per AGENTS.md §6) | AGENTS.md | REPO_VALIDATED | HIGH | None |
| approver | Same invariant | AGENTS.md | REPO_VALIDATED | HIGH | None |
| supervisor_signoff | T4_PLUS approval gate; typed_confirmation_required pattern | policy.py | REPO_VALIDATED | MEDIUM | supervisor identity resolution not proven wired to runtime |
| approved_artifact_refs | proof bundle artifact_refs pattern | proof.py _validate_manifest | REPO_VALIDATED | HIGH | None |
| proof_refs | proof bundle proof_refs pattern | proof.py | REPO_VALIDATED | HIGH | None |
| head_sha_or_digest | TP-DCP-0001 placeholder pattern; proof.py | proof.py + TP-DCP-0001 | REPO_VALIDATED (placeholder pattern) | HIGH | live SHA not computed in .v0 |
| freshness_state | ALLOWED_PROOF_STATUSES from proof.py | proof.py | REPO_VALIDATED | HIGH | None |
| red_lanes_present | DCP_RED_LANE_TAXONOMY lane IDs | TP-DCP-0001 schemas/dcp/dcp_red_lane_taxonomy | REPO_VALIDATED | HIGH | None |
| forbidden_paths_acknowledged | DCP-RED-MERGE-SEAM-0001 paths | TP-DCP-0001 fixture | REPO_VALIDATED_BY_AUDIT | HIGH | None |
| explicit_exclusions | SYNTHESIS_INVENTED — no direct repo equivalent | SYNTHESIS_INVENTED | SYNTHESIS_INVENTED | MEDIUM | None |
| expiry_window | SYNTHESIS_INVENTED — no proof freshness window in policy.py | SYNTHESIS_INVENTED | SYNTHESIS_INVENTED | LOW | Proof freshness policy not in approval_policy.yaml |
| decision | policy.py decision field vocab: allow/draft_only/gated/refuse/block | policy.py | REPO_VALIDATED | HIGH | None |
| decision_timestamp | Standard timestamp pattern | SYNTHESIS_INVENTED | SYNTHESIS_INVENTED | HIGH | None |
| rationale | Standard rationale pattern | SYNTHESIS_INVENTED | SYNTHESIS_INVENTED | HIGH | None |
| provenance | TP-DCP-0001 meta-contract §6.0 | TP-DCP-0001 | REPO_VALIDATED | HIGH | None |
| validation | TP-DCP-0001 meta-contract §6.0 | TP-DCP-0001 | REPO_VALIDATED | HIGH | None |
| field_provenance | TP-DCP-0001 meta-contract §6.0 | TP-DCP-0001 | REPO_VALIDATED | HIGH | None |
| known_unknowns | TP-DCP-0001 meta-contract §6.0 | TP-DCP-0001 | REPO_VALIDATED | HIGH | None |
| validation_state | TP-DCP-0001 §6.0; SYNTHESIS_INVENTED contract | TP-DCP-0001 | REPO_VALIDATED (pattern) | HIGH | const-pinned PROVISIONAL_UNVERIFIED_ENFORCEMENT for .v0 |

**Rejected overclaims:**
- Tried to derive a `live_execution_permission` field — REJECTED. Approval artifact is a record, not a write executor. Must not imply live-write readiness.
- Tried to infer a `merge_authorized` boolean — REJECTED. This would conflate approval with merge execution authority. DCP-RED-MERGE-SEAM-0001 prohibits this.

---

## 5. Derivation Table — DCP_PROJECT_RESOURCE_MAP

| Field / Surface | Derived From | Source | Provenance | Confidence | Unknowns |
|-----------------|-------------|--------|------------|------------|---------|
| project_id | ARCHITECTURE.md | ARCHITECTURE.md | REPO_VALIDATED | HIGH | None |
| repo_id | .repo_id file marker | AGENTS.md §4 | REPO_VALIDATED | HIGH | None |
| repo_root_marker | `.repo_id` file (AGENTS.md §4.1) | AGENTS.md | REPO_VALIDATED | HIGH | dopetaskroot marker also present per repo; both observed |
| canonical_source_roots | src/dopemux/, src/dopemux_pr_merge_specialist/, src/dopemux_pr_steward/, services/ | ARCHITECTURE.md §3 | REPO_VALIDATED | HIGH | services/ boundary not fully enumerated |
| schema_roots | schemas/ (observed directory) | filesystem observation | REPO_VALIDATED | HIGH | None |
| test_roots | tests/ (observed directory) | filesystem observation | REPO_VALIDATED | HIGH | None |
| proof_roots | proof/ (observed directory; gitignore forces git add -f) | filesystem + TP-DCP-0001 | REPO_VALIDATED | HIGH | proof/ is gitignored at .gitignore:362 (TP-DCP-0001 PROOF.json) |
| task_packet_roots | task-packets/ (observed directory) | filesystem observation | REPO_VALIDATED | HIGH | None |
| config_roots | config/orchestrator/ (approval_policy.yaml observed) | filesystem + policy.py | REPO_VALIDATED | HIGH | None |
| runtime_authority_pointers | policy.py DEFAULT_POLICY_PATH, AGENTS.md truth order | policy.py + AGENTS.md | REPO_VALIDATED | HIGH | TRUTH_*.md files absent from root; docs/03-reference/truth/ not fully inspected |
| forbidden_paths | queue_drain.py execute=True; batch_resolve_and_merge.py | queue_drain.py + TP-DCP-0001 | REPO_VALIDATED_BY_AUDIT | CERTAIN | None |
| red_line_paths | DCP-RED-MERGE-SEAM-0001 paths; DCP red lane taxonomy | TP-DCP-0001 | REPO_VALIDATED | HIGH | None |
| bridge_proxy_surfaces | dopecon-bridge (ARCHITECTURE.md §3.6) | ARCHITECTURE.md | REPO_VALIDATED | HIGH | dopecon-bridge runtime authority is advisory, not domain authority |
| memory_context_chronicle_surfaces | dope-memory, ConPort, working-memory-assistant (ARCHITECTURE.md §3.4) | ARCHITECTURE.md | REPO_VALIDATED | MEDIUM | endpoints PROVISIONAL; split authority not resolved |
| task_orchestrator_surfaces | task-orchestrator runtime + approval_policy.yaml capabilities | ARCHITECTURE.md §3.3 + policy.py | REPO_VALIDATED | MEDIUM | runtime authority conflicted per ARCHITECTURE.md §4 note |
| dopetask_surfaces | scripts/dopetask; scripts/taskx | ARCHITECTURE.md §3.2 | REPO_VALIDATED | MEDIUM | external dopetask implementation out of scope; only wrapper path observed |
| github_ci_surfaces | .github/workflows/ (observed); T5/T6 capabilities | approval_policy.yaml T5-T6 | REPO_VALIDATED | HIGH | None |
| endpoint_bindings | ConPort port 5455 (MCP_ConPort.md); dope-context port 6333 (Qdrant); working-memory-assistant | PROVISIONAL/UNKNOWN — no runtime proof in this checkout | PROVISIONAL | LOW | all endpoint bindings remain PROVISIONAL per invariant §11 of TP-DCP-0002 |
| canonical_writers_map | policy.py canonical_writer fields across capabilities | policy.py | REPO_VALIDATED | HIGH | None |
| known_unknowns | Accumulated during derivation | This analysis | N/A | N/A | See below |
| provenance | TP-DCP-0001 meta-contract §6.0 | TP-DCP-0001 | REPO_VALIDATED | HIGH | None |

**Rejected overclaims:**
- Tried to encode live endpoint URLs as REPO_CROSS_CHECKED — REJECTED. No runtime proof in this checkout resolves endpoint bindings to active authority.
- Tried to list all services/ subdirectories as canonical surfaces — REJECTED. `services/` boundary not fully enumerated; only ARCHITECTURE.md §3 planes included.

---

## 6. Known Unknowns Accumulated

1. TRUTH_*.md files (TRUTH_INTERFACES.md, TRUTH_SYSTEMS.md, TRUTH_CANONICALS.md, TRUTH_GAPS.md) absent from repo root — referenced by AGENTS.md §2 as authority sources but not found.
2. RUNTIME_AUTHORITY_POINTERS.md absent — referenced by TP-DCP-0002 §6 but not in repo root.
3. PROJECT.md, PM_PLANE.md absent — referenced by AGENTS.md §2 but not in repo root.
4. dopetask-canonical-spec.json absent from schemas/ — no packet format validation schema available.
5. Dopetask execution tier not registered in approval_policy.yaml — MC-DOPETASK-EXEC is PROVISIONAL.
6. ConPort deployed-primary endpoint (port 5455) — PROVISIONAL; no runtime proof in checkout.
7. dope-memory endpoint — PROVISIONAL; no runtime proof in checkout.
8. dopecon-bridge API surfaces — PROVISIONAL; runtime explicitly denies domain authority.
9. steward_gate.py now present on main (was absent at TP-DCP-0001 audit). Gate enforcement status for queue_drain.py not fully verified — red lane remains active regardless.
10. DCP_APPROVAL_ARTIFACT `expiry_window` semantics — no proof freshness window defined in approval_policy.yaml; field is SYNTHESIS_INVENTED.
