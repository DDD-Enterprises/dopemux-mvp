# DCP Contract-Promotion + Tooling Layer v1 — Scope

**Date:** 2026-06-12 · **Status:** proposed (operator approval gates Phase-4 load)

## 1. System definition

**The system**: the path from current state (5 contracts at `.v0`, scanner tests-only, zero receipt/approval producers, no `dcp` CLI) to an **enforced, evidence-emitting DCP tooling core**: contracts promoted and runtime-coupled, deterministic guards wired locally + in CI, every helper run emitting a receipt, supervisor acceptance recorded as a real artifact, and the `dopemux dcp` CLI as the standardizing surface.

One sentence: **make the contracts real, then make the tooling speak them.**

## 2. In scope (v1)

| # | Workstream | Maps to |
|---|---|---|
| S1 | Promotion mechanics: contracts manifest, versioning semantics, "locked" definition, det-vs-LLM ADR | P1, PAL amendment 1+4, Appendix B(1)(10) |
| S2 | C1: taxonomy → schema-driven scanner (lane↔rule coupling, coverage closure, CI direct gate, pre-commit entry) | P1, W4/W8 guard slices |
| S3 | C2: helper-receipt v1 (field reconcile vs DR-015 §8 + runtime analogs) + emitter library + receipt store | P8, Appendix B(3) |
| S4 | C3: mutation-class instance + runtime classifier + hook annotation | P1 |
| S5 | C4: `dcp accept` → approval-artifact producer + reader (the `supervisor_accepted` first slice) | P7 quick win, Appendix B(7 partial) |
| S6 | C5: resource-map builder + drift-consistency CI (path sections only) | P1 |
| S7 | `dopemux dcp` CLI v1: `preflight · status · red-lines · verify-proof · evidence-pack · accept · receipts` as thin wrappers | P2, Appendix B(4) |
| S8 | Hook upgrades: taxonomy-driven surface guard, fail-closed fallback policy, receipts-on-denial, mutation-class annotation | Appendix B(3) |
| S9 | TOOLING-0001 resolutions: (1) surface split ADR, (2) governance-metadata registry, (3) MCP catalog schema lint | §8.3, D15 operationalization |
| S10 | Plugin packaging **design** (source-first → `.claude-plugin` compile), build staged last | P4, Appendix B(5 partial) |

## 3. Out of scope (explicit)

| Excluded | Why | Owner |
|---|---|---|
| P6 MCP HTTP-singleton cutover | adjacent system — **PAL amendment designates it CRITICAL PATH in the parallel DX-overhaul wave**; multi-worktree hook reliability is degraded until it lands (acknowledged, not hidden — TP-105 carries the risk note) | DX-overhaul wave 1 |
| P5 doctrine sync; **Appendix B(2) command-surface spec + hard-delete list**; command deletion/cleanup (Appendix B(9)) | DX-overhaul migration plan; TP-115 provides only the metadata substrate | DX-overhaul |
| Defining `LIVE_WRITE_READY` | D8's owner; this system fails closed on it | future packet |
| C5 endpoint-bindings promotion | blocked on endpoint/topology resolution (schema const-pins them PROVISIONAL) | post-P6 |
| W8 auto-fix lane, full evidence/verdict pipeline beyond `accept` | builds ON this system once receipts exist | P7 packet |
| Live writers of any kind; steward/classifier rewiring beyond a read adapter | v1 read-mostly posture (D8); pr_steward is its own surface | — |
| dNh-CRM profile content | cross-project profile model designed (S10) but only dopemux profile built | dnh repo |
| `services/repo-truth-extractor` parallel `classify_artifact` dedup | pre-existing debt, not on promotion path | backlog |

## 4. Definition of done — promotion ladder

Levels are **criteria**, expressed in existing vocab (no new state enums):

| Level | Name | Criteria |
|---|---|---|
| L0 | DRAFT | `.v0`, `PROVISIONAL_UNVERIFIED_ENFORCEMENT`, structural tests |
| L1 | RECONCILED | `.v0`, `REPO_CROSS_CHECKED` — every field repo-derived or explicitly provenance-tagged |
| L2 | WIRED | L1 + a runtime producer or consumer exists + coupling exercised by tests in CI |
| L3 | LOCKED | L2 + CI enforces conformance **on the enforcement path** (not just unit tests) + contract files under change-control lane (`DCP-RED-PROOF-CONTRACT-SCHEMA-MUTATION` active, hard_block) + version bumped `.v0`→`.v1` (schema_version + semver together). **"L3(split)"** (only sanctioned variant): L3 for path sections while endpoint bindings remain PROVISIONAL — applies to C5 only |

**v1 exit state (the gate-open criteria):**

| Contract | Target |
|---|---|
| C1 taxonomy | **L3** |
| C5 resource map (path sections) | **L3** (endpoint bindings stay PROVISIONAL, documented) |
| C2 helper receipt | **L2** |
| C3 mutation class | **L2** |
| C4 approval artifact | **L2** |

Plus: `dcp` CLI v1 shipped, every CLI/hook run emits a receipt, scanner runs as a direct CI gate, TOOLING-0001 three decisions recorded as ADR + manifest + lint.

When this state holds, the `BUILD_AFTER_CORE_CONTRACTS` gate **opens** for the broader tooling layer (plugin build-out, advanced CLI verbs, V2 surfaces).

## 5. Non-negotiable invariants carried

- DCP-RED-MERGE-SEAM-0001 untouched; nothing in this system imports/calls/wraps the merge seam.
- No live external writes; no endpoint binding; no self-certification (auditor ≠ implementer per packet); no auto-approve anywhere.
- Hard blocks live only in deterministic code (hooks/CLI/CI); LLM surfaces advisory-only.
- Critical checks duplicate in CI (client hooks = AUTHORITY-AS-CONFIGURED only).
- Receipts even on denial; no raw secrets in receipts.

## 6. Key risks (carried into design + plan)

| Risk | Mitigation |
|---|---|
| PR #858 in flight (CI unverified) — sequencing collision on `native_hooks.py` + hooks | plan sequences S8 after #858 lands or rebases onto it; surface-guard upgrade designed as delta on #858's import pattern |
| Schema evolution at L1 (adding detector fields) could be mistaken for drift | every added field carries provenance `REPO_VALIDATED` citing `red_lane_rules.py`; change happens in the sponsoring TP with audit |
| Editing `schemas/dcp/**` trips #858's warn surface | expected + correct; TPs note it |
| Fail-closed hooks could brick sessions on bugs | tiered policy: hard_block lanes fail closed; advisory surfaces fail open (design §6) |
| `test_16_no_forbidden_files_modified` CI deselect unexplained | TP-104 must investigate before changing the gate |
