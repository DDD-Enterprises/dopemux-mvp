# DCP Architecture Synthesis — Revised Delta (GPT-5.5 Pro, REV1, 2026-06-03)

> [!NOTE]
> **Provenance**: `SYNTHESIS_INVENTED`  
> **Status**: Preserved Decision Input (Audited / Authoritative for TP-DCP-0001 Scope)

> Applies the 5 Opus audit must-fixes (`GO_WITH_FIXES`). Changed sections only: **§4, §5, §6, §10, §11**. Decision artifact revision, not a build plan. No redesign — every audit finding was REVISE, not KILL. D1–D16 postures, the four-surface TO model, the dry-run set, and the red-lane contract remain intact. Status: `READY_FOR_DELTA_ONLY_OPUS_RECHECK`.

> **PRECEDENCE:** This REV1 delta **supersedes** the original synthesis §1, §2 (packet-1 lock-scope), and §8 wherever they differ on the contract floor. The 3 shapeless contracts (`DCP_MUTATION_CLASS`/`DCP_APPROVAL_ARTIFACT`/`DCP_PROJECT_RESOURCE_MAP`) are **DEFERRED** from `TP-DCP-0001`; the original's "lock 5 first" wording does not apply. (Closes the Stage-3 delta-recheck residual.) Two cosmetic nits noted in `DCP_DELTA_RECHECK.md` (CONTROL_SNAPSHOT `UNVERIFIED_ENFORCEMENT` qualifier; split §10 provenance-acceptance into presence-lint + correctness-review) are non-gating polish for build time.

## What changed vs prior synthesis
1. **Contract floor no longer flat `DECIDED`** — every generic DCP contract carries a provenance tag: `REPO_VALIDATED` / `EXTERNAL_PROPOSED (DR-016)` / `SYNTHESIS_INVENTED`.
2. **External/invented field lists demoted to provisional** — `DCP_EVIDENCE_HIT`, `DCP_CHRONICLE_RECEIPT`, `DCP_HELPER_RECEIPT`, `DCP_PROOF_POINTER` may not leave `.v0` without repo-local field-vocab reconciliation.
3. **In-main ungated merge seam → named universal red line** — DCP must never import/call/wrap/wire `src/dopemux_pr_merge_specialist/queue_drain.py`'s `execute=True` path, nor `scripts/batch_resolve_and_merge.py`. *(Both paths ground-truth-verified IN origin/main.)*
4. **TP-DCP-0001 acceptance fixed** — static fixture validation insufficient; per-field provenance required. Local pytest + read-only `git rev-parse`/`git status` allowed; live external/mutation subprocesses forbidden.
5. **`auditor ≠ implementer` is now a packet acceptance gate** — no self-certifying loop may certify the packet that defines self-certification as a red lane.
6. **The 3 shapeless repo-grounded contracts deferred** — `DCP_MUTATION_CLASS`, `DCP_APPROVAL_ARTIFACT`, `DCP_PROJECT_RESOURCE_MAP` stay architecture-required but are NOT locked in packet 1. Chose **DEFER** (GPT-5.5 hadn't re-verified the repo files). *(Audit-side note: those files DO exist — `config/orchestrator/approval_policy.yaml`, `src/dopemux/orchestrator/policy.py` — so derive is achievable; defer is the conservative choice.)*
7. **`DCP_CONTROL_SNAPSHOT` narrowed** — packet 1 locks only its envelope + authority-metadata wrapper; per-surface projection fields provisional pending resource maps + canonical-root.

---
## §4. Generic vs project-specific split — revised
**Decision preserved:** generic DCP Core (deny-by-default contracts/provenance/red-lanes/artifacts) + Dopemux profile (split-authority, governance red lanes, no fake unified owner) + dNh profile (file-path red-lane classifier + external-action lanes; no forced symmetry) + packaging names as architecture language not runtime-mandated. No D1–D16 posture reopened.

### Revised generic contract registry
| Contract | Provenance | Status | TP-DCP-0001 |
|---|---|---|---|
| `DCP_RED_LANE_TAXONOMY` | REPO_VALIDATED core + per-lane provenance required | LOCKED_V0_ALLOWED | In scope (envelope; each lane source-tagged) |
| `DCP_CONTROL_SNAPSHOT` | SYNTHESIS_INVENTED | PROVISIONAL | Envelope only (per-surface fields deferred) |
| `DCP_PROOF_POINTER` | SYNTHESIS_INVENTED | PROVISIONAL — UNVERIFIED_ENFORCEMENT | Pointer shell only (no live SHA/hash) |
| `DCP_EVIDENCE_HIT` | EXTERNAL_PROPOSED (DR-016) | PROVISIONAL — UNVERIFIED_ENFORCEMENT | Envelope only w/ per-field provenance (17-field shape DR-016-seeded) |
| `DCP_CHRONICLE_RECEIPT` | EXTERNAL_PROPOSED (DR-016) | PROVISIONAL — UNVERIFIED_ENFORCEMENT | Envelope only w/ per-field provenance |
| `DCP_HELPER_RECEIPT` | EXTERNAL_PROPOSED (DR-016) | PROVISIONAL — UNVERIFIED_ENFORCEMENT | Envelope only (no repo-runtime helper-receipt exists) |
| `DCP_MUTATION_CLASS` | REPO_VALIDATED source target, shape not derived here | DEFERRED_FROM_TP-DCP-0001 | Out of packet 1 |
| `DCP_APPROVAL_ARTIFACT` | REPO_VALIDATED source target, shape not derived here | DEFERRED_FROM_TP-DCP-0001 | Out of packet 1 |
| `DCP_PROJECT_RESOURCE_MAP` | REPO_VALIDATED source target, shape not derived here | DEFERRED_FROM_TP-DCP-0001 | Out of packet 1 |

---
## §5. Red-lane contract — revised
### 5.1 New top-level named red line — `DCP-RED-MERGE-SEAM-0001`
`execute_or_dry_run(merge_cmd, execute=True)` at `queue_drain.py:617/2006/2017` IS in origin/main; `steward_gate.py` absent. **DCP must NEVER:** import `src/dopemux_pr_merge_specialist`; call/wrap `queue_drain.py`; invoke the `execute=True` seam; call `scripts/batch_resolve_and_merge.py`; adopt the PR-merge specialist as a DCP authority lane; allow any helper/auditor/steward/broker to self-certify merge readiness. Universal for TP-DCP-0001 and every later packet (Opus #1 build-time red line).
### 5.2 Universal red lanes (provenance-aware)
In-main merge seam (hard block, REPO_VALIDATED_BY_AUDIT); branch-protection mutation; CODEOWNERS mutation; workflow permission escalation; secrets in argv/cache/logs (hard block); self-certifying loop (hard block); `pull_request_target`+untrusted checkout (hard block); proof contract/schema mutation; agent-approved merge w/o supervisor (hard block); identity/contact merge or destructive external write (project gate); AI-agent-authority-collapse (hard block unless role separation proven).
### 5.3 Build-time red-line bundle (every packet)
1. Never wire the in-main merge seam. 2. Never compute live SHAs/hashes against a target repo tree for static fixtures. 3. Never let the contract-locking packet self-certify. 4. Never bind ConPort/dope-memory/TO endpoints in v1. 5. Never promote external DR corroboration into repo authority.

---
## §6. Proof / receipt model — revised
### 6.0 Contract status rule
`.v0` = unstable VERSION, not authority. Every contract+field carries:
```yaml
provenance: { tag: REPO_VALIDATED|EXTERNAL_PROPOSED|SYNTHESIS_INVENTED, source_ref: string }
validation: { state: REPO_CROSS_CHECKED|PROVISIONAL_UNVERIFIED_ENFORCEMENT|DEFERRED, notes: string }
```
### 6.1 `DCP_PROOF_POINTER` — SYNTHESIS_INVENTED / PROVISIONAL — pointer shell only
schema_version dcp-proof-pointer.v0; pointer_id, project_id, repo_id, source_family, source_artifact_ref; source_artifact_digest{value optional-in-fixture, provenance, validation_state}; source_head_sha{value optional-in-fixture, provenance, validation_state}; validation_state; auditor_verdict; freshness_state; authority_tier; confidence; derived; field_provenance. **Invariant:** `auditor_verdict` ≠ `validation_state`. No live hash/SHA computation in packet 1.
### 6.2 `DCP_CHRONICLE_RECEIPT` — EXTERNAL_PROPOSED(DR-016) / PROVISIONAL — envelope only
schema_version dcp-chronicle-receipt.v0; receipt_id, receipt_type, project_id, timestamp_utc, artifact_refs, proof_refs, authority_label, red_lanes, field_provenance, validation_state=PROVISIONAL_UNVERIFIED_ENFORCEMENT. Other 22-list fields are CANDIDATE until repo-local vocab reconciliation. Separate from proof bundles; not runtime state.
### 6.3 `DCP_EVIDENCE_HIT` — EXTERNAL_PROPOSED(DR-016) / PROVISIONAL — envelope only
schema_version dcp-evidence-hit.v0; hit_id, source_system, source_ref, retrieved_at_utc, authority_tier, confidence, derived, canonical_writer, freshness_state, field_provenance, validation_state=PROVISIONAL. 17-field DR-016 shape not repo-validated; envelope may lock, field vocab may not.
### 6.4 `DCP_HELPER_RECEIPT` — EXTERNAL_PROPOSED(DR-016) / PROVISIONAL — envelope only
schema_version dcp-helper-receipt.v0; helper_receipt_id, helper_tool, helper_model, invocation_ref, output_ref, exit_code(optional), mutation_performed, red_lane_flags, remaining_risks, field_provenance, validation_state=PROVISIONAL. Advisory; cannot certify readiness.
### 6.5 `DCP_CONTROL_SNAPSHOT` — SYNTHESIS_INVENTED / PROVISIONAL — envelope only
schema_version dcp-control-snapshot.v0; snapshot_id, project_id, created_at_utc, source_pack_refs, authority_order_ref; surfaces{status: PROVISIONAL, note: per-surface projection fields deferred pending DCP_PROJECT_RESOURCE_MAP + canonical-root}; field_provenance. Do not lock per-surface projection fields until resource map exists.

---
## §10. First build packet — `TP-DCP-0001 · DCP Core Provenance Contracts + Read-Only Control Snapshot Envelope`
**Objective:** establish a provenance-safe DCP contract floor + a read-only control-snapshot envelope, without promoting external DR or synthesis-invented field lists to repo authority.
**Scope IN:** `DCP_RED_LANE_TAXONOMY.v0` (incl. the named merge-seam red line; every lane provenance-tagged); `DCP_CONTROL_SNAPSHOT.v0` (envelope + authority metadata only; per-surface fields provisional); `DCP_PROOF_POINTER.v0` (pointer shell, no live hash); `DCP_EVIDENCE_HIT.v0` / `DCP_CHRONICLE_RECEIPT.v0` / `DCP_HELPER_RECEIPT.v0` (provisional envelopes + field-provenance requirements); static fixture authored only from supplied evidence text; schema validation tests; proof artifact showing provenance coverage.
**Scope OUT:** `DCP_MUTATION_CLASS`/`DCP_APPROVAL_ARTIFACT`/`DCP_PROJECT_RESOURCE_MAP` shape lock; live reads from ConPort/dope-memory/dope-context/TO/GitHub/CRM/bridge/Dopetask; live writes of any kind; PR merge/repair/action-bridge live submit; Dopetask exec; cockpit impl; plugin/hook enforcement.
**Invariants:** LIVE_WRITE_READY undefined+blocking; open PRs #765–#792 + generated TPs CLAIMED_ONLY; #758–#762 merge-state ≠ code-present-and-usable-in-main (except the audit-resolved advisory PR-Steward surface); `DCP-RED-MERGE-SEAM-0001` absolute (never import/call/wrap/wire `queue_drain.py` execute=True or `scripts/batch_resolve_and_merge.py`); auditorVerdict ≠ validationState; ConPort/dope-memory endpoints provisional, no binding v1; mirrors/proxies/indexes/cache-freshness never authority; static fixture SHAs/hashes are illustrative placeholders from pasted evidence only; no filesystem traversal of target repo for fixture population.
**Acceptance:** every contract has schema_version + provenance + validation_state; every field either cross-checked against a cited repo artifact OR tagged EXTERNAL_PROPOSED/SYNTHESIS_INVENTED; embedded audit verifies provenance coverage (not merely fixture round-trip); static fixture validation insufficient unless provenance validation passes; local pytest allowed; read-only `git rev-parse`/`git status` allowed only for proof metadata; no live external/network/GitHub/Dopetask/chronicle/ConPort/TO/CRM/bridge/mutation subprocess; embedded audit performed by an actor DISTINCT from the contract author; supervisor sign-off recorded separately; proof bundle includes contradiction carry-forward; any attempt to lock the 3 deferred contracts without direct repo derivation STOPS the packet.

---
## §11. Preserved risks / contradiction carry-forward — revised (highlights)
- **L-01/K-19** partially resolved (advisory PR-Steward in origin/main; unmerged CLI bits CLAIMED_ONLY; #758–762 still don't prove all-code-in-main).
- **L-09** resolved sharper/more dangerous → now `DCP-RED-MERGE-SEAM-0001` (execute=True confirmed in origin/main, guard absent).
- **L-02/03/04/05/06/07/08/10/11/12/14/15, K-23/26/44** still open (handled as before: endpoints provisional, DR-011 advisory, TUI read-only, etc.).
- **K-27** resolved for naming only (`.v0` correct; `.v0` ≠ provenance solution).
- **K-46** still master gate (LIVE_WRITE_READY undefined+blocking).
- **Newly explicit:** DR-016 field-vocab is external-seeded (13 repo-only UNKNOWNs pending before any receipt/evidence/helper exits `.v0`); self-certification gap (packet must not self-certify); static-fixture circularity (provenance coverage is the gate, not round-trip); live-SHA temptation (fixture hashes are placeholders only).

**REVISED STATUS:** `READY_FOR_DELTA_ONLY_OPUS_RECHECK` — Opus should verify only that the 5 fixes landed (provenance tags, §10 acceptance gate, subprocess re-scope, auditor≠implementer, merge-seam invariant, deferred contracts, provisional CONTROL_SNAPSHOT) + no new break.
