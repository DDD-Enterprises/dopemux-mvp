# DCP Architecture Synthesis — Decision Artifact (GPT-5.5 Pro, 2026-06-03)

> [!NOTE]
> **Provenance**: `SYNTHESIS_INVENTED`  
> **Status**: Preserved Decision Input (Audited / Superseded-in-Part)

> Source: operator-run GPT-5.5 Pro synthesis from `DCP_5_5_SYNTHESIS_INPUT_PACK.md` + `DCP_PRE_SYNTHESIS_CONTRADICTION_LEDGER.md` + `DCP_SYNTHESIS_CHATGPT_PROMPT.md`. Treats the input pack as authoritative campaign compression (not the architecture decision) and the contradiction ledger as a guardrail artifact (preserves authority leaks, does not resolve them). Repo runtime evidence outranks external DR; open PRs + generated TP series stay CLAIMED_ONLY; UNKNOWN is not promoted. **This is the decision artifact audited in Stage 3.**

> ⚠ **SUPERSEDED-IN-PART by `DCP_ARCHITECTURE_SYNTHESIS_GPT55_REV1.md`** (reconciliation added by the Stage-3 delta re-check; closes the `GO_WITH_FIXES` residual). Where this original and REV1 differ on the **`TP-DCP-0001` contract-floor scope, REV1 §4/§10 are authoritative.** Specifically: the **"lock 5 contracts first"** wording in §1 and §8 is **superseded** — `DCP_MUTATION_CLASS`, `DCP_APPROVAL_ARTIFACT`, `DCP_PROJECT_RESOURCE_MAP` are **DEFERRED** out of packet 1 (only `DCP_RED_LANE_TAXONOMY` + provisional envelopes lock in TP-DCP-0001). The §2 D-table decisions stand, but their packet-1 *lock-scope* follows REV1.

## 1. Executive decision
- **Build DCP Core inside `dopemux-mvp`** as a generic, read-first control-plane core exposed via a new `dopemux dcp` namespace, logically separated from Dopemux-specific and dNh-specific adapters. Physical home: Dopemux repo (observed operator control surface; mixed CLI/services/adapters/artifact workspace). Logical model: `core contracts + per-project profiles + read-only adapters + proof/readiness artifacts`.
- **DCP Core is NOT** jpicklyk TO, Dopemux FastAPI services/task-orchestrator, Dopetask, ConPort, dope-memory, dope-context, dopecon-bridge, or the cockpit. It is the evidence/readiness/proof/action-planning authority; reads all surfaces, writes none until `LIVE_WRITE_READY` is proven (currently undefined).
- **v1 = artifact-first + CLI-first + projection-only.** Governed TUI may be wrapped later as optional read-only projection — not the floor, not design-cleared, not implementer-mode-ready. Web Palette = UNKNOWN/OPEN_SCOPE.
- **First build packet = contract-locking only**: red-lane taxonomy, receipt schemas, mutation classes, approval artifact, project path/resource maps. No live adapters/writes/merge/Dopetask-exec/chronicle-append/CRM/channel writes.
- **PR/autoreview/merge plane = quarantine-or-mine only.** `tools/pr_steward` + `tools/pr_action_bridge/compiler.py` are zero-mutation; `src/dopemux_pr_merge_specialist` is mutation-capable, `steward_gate.py` seam absent/unverified.

## 2. D1–D16 decisions
| ID | Decision | Status |
|---|---|---|
| D1 Core location | DCP Core in Dopemux repo under new DCP namespace + `dopemux dcp` CLI; generic-by-contract, not Dopemux-only. | DECIDED |
| D2 TO posture | jpicklyk = projection/work-graph target; Dopemux FastAPI TO = coordination/future-cockpit bridge; neither is DCP Core. No live TO writes until LIVE_WRITE_READY proven. | DECIDED |
| D3 Dopetask scope | Execution/proof-lifecycle adapter spine ONLY for reading existing bundles. No launcher/runner execution paths. | DECIDED |
| D4 Generic/project split | Generic core + project profiles; preserve Dopemux/dNh asymmetry; DR-015 packaging names not runtime-mandated. | DECIDED |
| D5 Cockpit MVP | Artifact + CLI MVP; optional governed TUI read-only later; web Palette UNKNOWN. | DECIDED / PARTLY UNKNOWN |
| D6 Automation ladder | v1 automates evidence compression, proof inspection, readiness derivation, dry-run action planning; human gate for approval/live-writes/merges/red-lane overrides. UX ladder provisional (step-count evidence deferred). | PROVISIONAL |
| D7 First build packet | Contract-locking packet only; no live adapter impl. | DECIDED |
| D8 Dry-run set | Live TO writes, Dopetask exec, GitHub mutation, dNh runtime writes, PR repair/merge, CRM/channel writes remain dry-run/forbidden. | DECIDED |
| D9 Proof representation | B+C: `DCP_PROOF_POINTER` + shape-family dispatcher; no retroactive migration. | DECIDED |
| D10 Red lanes | Universal red lanes + project overlays; autoreview/merge stack quarantine/mine only. | DECIDED |
| D11 Memory split | ConPort/dope-memory/dope-context/dopecon-bridge separate; DCP v1 = read/export/pointer only. | DECIDED |
| D12 Chronicle receipt model | DCP chronicle-receipt schema as artifact contract; no append to live dope-memory in v1. | DECIDED |
| D13 Retrieval source trace | Every hit carries source path/system, version/freshness, authority tier, confidence, derived flag, canonical writer. | DECIDED |
| D14 Cockpit timeline source | v1 timeline artifacts-first; chronicle enrich later only after endpoint/deployed-primary resolution. | DECIDED |
| D15 Tooling boundaries | Contracts first; deterministic hooks/CLI enforce; LLM skills synthesize; humans approve; plugin v1 defaultEnabled:false. | DECIDED |
| D16 Mirrors/proxies | Mirrors/bridges/proxies/indexes/cache-freshness never authority; every payload carries upstream authority metadata. | DECIDED |

## 3. Layered architecture
- **DCP Core** — AUTHORITY for evidence/readiness/proof/action-intent artifacts ONLY; reads all; writes only DCP-owned local artifacts. Owns snapshots, readiness derivation, proof pointers, policy interpretation, dry-run action plans. Does not own runtime truth.
- **Project exporter** — adapter/profile bridge; exports repo views into `CONTROL_SNAPSHOT`-style artifacts with project extension blocks; local DCP export artifacts only.
- **Memory/context/chronicle adapters** — read/export/pointer; ConPort/dope-memory/dope-context/dopecon-bridge stay separate; no live writes; endpoint binding provisional where runtime conflicting.
- **Proof/provenance adapter** — shape-family dispatcher + `DCP_PROOF_POINTER`; `auditorVerdict` separate from `validationState`; local proof index/pointers only.
- **TO projection adapter** — read-only/dry-run; jpicklyk projection only after canonical root/state ambiguity resolved; FastAPI TO = coordination/cockpit bridge, not DCP authority.
- **Supervised action broker** — dry-run action planning only; emits action-intent artifacts with mutation class + required approval; no live submit in v1.
- **Cockpit/UI** — projection/operator view; artifact+CLI first; optional governed TUI later read-only; web Palette open.
- **Tooling hooks/skills/plugin** — contracts first; hooks/CLI enforce (local + CI); skills synthesize; humans approve; plugin v1 defaultEnabled:false.

## 4. Generic vs project-specific split
**Generic DCP Core contracts:** `DCP_CONTROL_SNAPSHOT`, `DCP_PROOF_POINTER`, `DCP_EVIDENCE_HIT`, `DCP_CHRONICLE_RECEIPT`, `DCP_HELPER_RECEIPT`, `DCP_APPROVAL_ARTIFACT`, `DCP_MUTATION_CLASS`, `DCP_RED_LANE_TAXONOMY`, `DCP_PROJECT_RESOURCE_MAP`. Core = deny-by-default; profiles may only add stricter rules, never weaken core denies.
**Dopemux profile** (split-authority, governance-level red lanes, no runtime file-path classifier): system maps, service/resource paths, contradiction gates, mutation classes, approval-tier bindings; must not invent a unified PM/memory/execution owner.
**dNh profile** (event-sourced, file-path-anchored red-lane classifier, 11 confirmed + 1 probable lanes): file-path classifier + external-action lanes; must not inherit Dopemux governance-only model.
**Packaging:** `dcp-core + profile contracts` as architecture language, not necessarily package names (ledger warns the package-name triplet comes from external DR; don't launder into repo authority).

## 5. Red-lane contract
**Universal (supervisor gate + fail closed):** branch-protection mutation, CODEOWNERS mutation, workflow permission escalation, secrets in argv/cache/logs/artifacts (hard block), self-certifying implementer/auditor/supervisor loop (hard block), `pull_request_target` w/ untrusted checkout (hard block), proof contract/schema mutation, agent-approved merge without supervisor (hard block), identity/contact merge or destructive external write, AI-agent-authority-collapse (hard block unless role separation proven).
**Dopemux:** `DPMX_LIVE_OK` removal/bypass, `scripts/dopetask` exec without consent, dope-memory/chronicle append, GitHub PR merge via specialist, approval-policy fingerprint mutation, TO live-write, launchd service mgmt (mapped to tiers T5/T6/TX).
**dNh:** Telegram send/callbacks, iMessage/AppleScript/chat.db ingest, Twenty CRM writeback, identity/contact merge, mirror-dispatcher dedupe-claim writes, RAG worker/index writes, browser/OpenClaw automation, proof authorship, CI/branch-protection changes, probable WhatsApp outbound (UNKNOWN).

## 6. Proof / receipt model
**6.1 `DCP_PROOF_POINTER`** (pointer-first, digest-anchored): schema_version "dcp-proof-pointer.v0", pointer_id, project_id, repo_id, source_family, source_artifact_path, source_artifact_sha256, source_head_sha, source_branch, captured_at_utc, validation_state, auditor_verdict, freshness_state, dirty_worktree, mixed_sha_artifact_set, evidence_index_ref, authority_tier, confidence, derived, supersedes. Five incompatible PROOF.json families → shape-family dispatch (no false unified contract). `auditorVerdict ≠ validationState`; freshness SHA-derived not lifecycle-derived.
**6.2 `DCP_CHRONICLE_RECEIPT`** (temporal receipts referencing proof, not containing/validating it; not runtime state): receipt_id, receipt_type, project_id, repo_id, series_id, tp_id, source_system, source_sha, artifact_refs[], proof_refs[], evidence_refs[], actor, tool, mutation_class, action_intent_id, approval_ref, authority_label, red_lanes[], timestamp_utc, supersedes, compensates, digest.
**6.3 `DCP_EVIDENCE_HIT`** (source-traced, not truth): hit_id, source_system, source_path_or_ref, source_version_or_sha, source_timestamp_utc, index_timestamp_utc, retrieval_timestamp_utc, artifact_timestamp_utc, canonical_writer, authority_tier, confidence, derived, freshness_state, query_ref, excerpt_ref, line_range_or_selector, adapter_id.
**6.4 `DCP_HELPER_RECEIPT`** (tainted-advisory unless deterministically validated; no helper marks own work ready; implementer/auditor/supervisor separate): helper_receipt_id, helper_tool, helper_model, invocation_ref, input_digest, output_ref, exit_code, mutation_performed, authority_claims[], warnings[], red_lane_flags[], fixes_applied[], remaining_risks[], taint_label, proof_refs[].

## 7. Cockpit MVP + evolution
v1 = DCP MD/JSON artifacts + `dopemux dcp` read commands (**approved floor**). v1 optional = governed TUI read-only projection (**only with gate badges, no live writes**). Later = GitHub/TO projection panels (dry-run/read-only). Later = web Palette (**UNKNOWN/OPEN_SCOPE**). Never in v1 = Claude Design pickup, implementer mode, live-write cockpit actions (**forbidden**).
PRESERVED RISK: "adopt existing governed TUI" carries the design-gate caveat inline — code consumable read-only, NOT design-cleared, implementer mode unbuilt (all cockpit TP gates carry `safe_for_claude_design:"NO"`).

## 8. Tooling layer staging
Lock 5 contracts first: red-lane taxonomy, receipt schema, mutation classes, approval artifact, project path/resource maps. Then: `dopemux dcp` CLI (standardize read/snapshot/proof-inspect/dry-run-plan); deterministic hooks (enforce hard blocks, local+CI; client hooks insufficient alone); skills/subagents (synthesize, advisory); plugin (defaultEnabled:false, no monitors/channels/default-agent); CI duplicates hard gates; humans approve red lanes/live-writes/overrides/merges.

## 9. What stays dry-run / forbidden in v1
Live TO writes (until LIVE_WRITE_READY proven), jpicklyk writes, Dopetask execution + launcher/runner, GitHub PR merge/auto-merge, PR repair/action-bridge live submit, autoreview/PR-merge-specialist adoption (quarantine/mine only), dope-memory chronicle append, ConPort writes, dopecon-bridge writes, CRM/Twenty writeback, Telegram/iMessage/WhatsApp outbound, browser/OpenClaw automation — all forbidden in v1. CODEOWNERS/branch-protection/workflow changes = supervisor-gated red lane (not DCP-autonomous). Secret-bearing paths = hard block. Cockpit live actions forbidden. Any open-PR/generated-TP-dependent feature = CLAIMED_ONLY/UNKNOWN.

## 10. First build packet — `TP-DCP-0001 · DCP Core Contracts + Read-Only Control Snapshot`
**Objective:** establish the DCP contract floor + one local read-only snapshot artifact shape. No live adapters/mutation/cockpit/PR-merge.
**Scope IN:** DCP contract docs/schemas (red-lane taxonomy, mutation classes, approval artifact, evidence hit, proof pointer, chronicle receipt, helper receipt, project path/resource map, read-only control snapshot); a static sample fixture from supplied evidence (not live repo calls); schema validation tests.
**Scope OUT:** no live reads from ConPort/dope-memory/dope-context/TO/GitHub; no write integration; no merge/review automation; no Dopetask execution; no cockpit; no plugin/hook enforcement.
**Invariants:** LIVE_WRITE_READY remains undefined+blocking; open PRs #765-792 + generated TPs CLAIMED_ONLY; #758-762 merge-state ≠ code-present-and-usable-in-main; auditorVerdict ≠ validationState; ConPort/dope-memory endpoints provisional; mirrors/proxies/indexes never authority.
**Acceptance:** all contract schemas strict; every schema has schema_version but avoid final "v1" naming where K-27 proof-version alignment unresolved (use `.v0`); static fixture validates; no subprocess/network/GitHub/Dopetask/chronicle/ConPort/TO/CRM/bridge calls; embedded audit reviews only the contract artifact; proof bundle includes contradiction carry-forward.

## 11. Preserved risks / contradiction carry-forward
L-01/K-19 (#758-762 merge≠code-in-main → CLAIMED_ONLY until origin/main verified); L-02/K-30/K-31 (ConPort/dope-memory endpoints provisional, no binding v1); L-03/K-33 (DR-011 advisory, never authority); L-04/K-37/K-38 (cockpit "adopt" not design-cleared); L-05 (COCKPIT packet non-uniform on merge status); L-06 (tooling config ≠ enforcement; duplicate in CI); L-07 (4+S5 TO separation sound but memo ≠ runtime authority; verify root/compose coupling); L-08 (preserve Dopemux/dNh asymmetry; package names optional); L-09 (60-module PR-merge plane mutation-capable; quarantine/mine; no adoption until steward gate + reachability traced); L-10 (D5/D6 closure provisional, UX evidence deferred); L-11/K-23 (SHA-derived freshness; lifecycle ≠ freshness); L-12 (projection blocked until canonical root/resource maps exist); L-13/K-44 (Gemini→Antigravity cutover date-sensitive; auditor route UNKNOWN until rechecked); L-14 (cite runtime/source packet level when load-bearing); L-15/K-38/K-39 (web Palette/neon_dashboard open; not in cockpit MVP); K-26 (PAL clink config AVAILABLE, execution NEEDS_SUPERVISOR); K-27 (dNh proof v1 vs 1.2 → use .v0); K-46 (LIVE_WRITE_READY undefined → master hard gate).

## 12. Weakest assumptions (flagged for Opus audit)
1. DCP physical location (Dopemux repo/`dopemux dcp`) — separate package may be better post-contract-stabilization.
2. Artifact-first cockpit — safest floor, but CLI-first may create operator drag.
3. No DCP-owned chronicle append in v1 — DR-014 allows an optional DCP-owned append-only namespace; test whether artifact receipts alone suffice.
4. `DCP_PROOF_POINTER.v0` + dispatcher — avoids false-unified-proof but may create a new schema family too early; test minimality.
5. Profile model — preserves asymmetry but packaging/enforcement boundaries not runtime-proven; pressure-test leakage.
6. Autoreview quarantine — conservative; check if any zero-mutation parts can graduate earlier.
7. Artifacts-first timeline — may underserve temporal debugging; challenge whether dope-memory read-only enrichment can be admitted sooner.
8. No live adapters in first packet — max-safe but may delay feedback; verify static fixtures are enough to lock schemas.
9. Approval artifact shape — needs explicit compatibility with existing `approval_policy.yaml` tiers without treating policy as enforced on S3 routes.
10. Freshness model — SHA-derived clean for repo artifacts; cross-system sources without SHA need a rigorous equivalent.
