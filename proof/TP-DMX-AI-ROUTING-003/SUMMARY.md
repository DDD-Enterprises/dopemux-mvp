---
id: TP-DMX-AI-ROUTING-003-SUMMARY
title: Proof Summary — TP-DMX-AI-ROUTING-003
type: proof_summary
owner: '@hu3mann'
date: '2026-06-06'
---

# Proof Summary — TP-DMX-AI-ROUTING-003

## Change Summary

Three governance-integration residues from PR #837 (`TP-DMX-AI-ROUTING-001/002`) were repaired in three commit-sized slices on branch `claude/tp-dmx-ai-routing-003-governance-residue`:

- **G0**: Registered `TP-DMX-AI-ROUTING-001` and `TP-DMX-AI-ROUTING-002` in `task-packets/INDEX.md` Completed table (both `IMPLEMENTATION_COMPLETE`, PR #837 merged). Satisfies INDEX rule: "If it's not indexed here, it didn't happen."
- **G1**: Removed phantom stage names `plan_challenge` and `slice_review` from `task-packets/TEMPLATE_TASK_PACKET.md` Model Routing section. Stage list now matches `config/ai/model-routing.policy.yaml` verbatim: `cheap_read / investigation / planner_strong / implementer_standard / judge_strong / self_audit`.
- **G2**: Added `## 11. Model Routing Authority` to `AGENTS.md` — points to policy YAML and human guide, provides default tier-intent table (Haiku for reads, Sonnet for implementation, Opus for planning/audit), notes `VERIFY_WITH_VENDOR_DOCS` for exact selectors, and explicitly defers PAL chain rules to §5.

No runtime code, schemas, configs, CI, or CLI surfaces were touched.

## Authority Used

- Active Task Packet: `TP-DMX-AI-ROUTING-003` (this packet, `planner_strong` draft approved 2026-06-06)
- `task-packets/INDEX.md` — canonical registry authority
- `task-packets/TEMPLATE_TASK_PACKET.md` — template authority
- `AGENTS.md` — Codex/agent runtime authority
- `config/ai/model-routing.policy.yaml` — stage names source of truth (verbatim match required)
- `proof/TP-DMX-AI-ROUTING-001/PROOF.json` — closure state: `IMPLEMENTATION_COMPLETE`
- `proof/TP-DMX-AI-ROUTING-002/PROOF.json` — closure state: `IMPLEMENTATION_COMPLETE`

## Validation Performed

| Gate | Result | Evidence |
| --- | --- | --- |
| G0: INDEX contains -001 and -002 entries | **PASS** | `rg -n "TP-DMX-AI-ROUTING-001\|TP-DMX-AI-ROUTING-002" INDEX.md` → lines 126–127 |
| G1: No `plan_challenge` / `slice_review` in TEMPLATE | **PASS** | rg returns exit 1 (zero matches) |
| G1: All six policy stages present in TEMPLATE | **PASS** | rg hits line 95 with all six names |
| G2: AGENTS.md routing section present | **PASS** | rg hits `model routing`, `Opus`, `Sonnet`, `Haiku` in new §11 |
| G2: §5 PAL chains unchanged | **PASS** | `Codex minimum chain` and `Risky or architecture-sensitive chain` still on lines 72–73 |
| diff --stat shows allowlisted files only | **PASS** | INDEX.md (+2), TEMPLATE_TASK_PACKET.md (±1), AGENTS.md (+18) |
| PROOF.json well-formed | **PASS** | `python -m json.tool` exits 0 |
| Runtime/schema/config/CI unchanged | **PASS** | No diff outside allowlist |
| Sealed proofs -001/-002 unchanged | **PASS** | Not in allowlist; not touched |
| Embedded audit | **PASS_WITH_RISKS** | F1 LOW (date) ACCEPTED; F2 INFO (self-closure row) DEFERRED |

NOT_RUN: live model execution, CI pipeline, PR Steward merge-readiness verdict (awaiting PR creation and check run).

## Remaining Uncertainty / Risk

- **R1 (deferred)**: Schema enum drift in `schemas/proof/embedded_audit.schema.json` — catch-all values provide coverage. Track as `TP-DMX-AI-ROUTING-004` when prioritized.
- **R2 (deferred)**: `TP-DMX-AI-ROUTING-003` self-closure INDEX row — can be added post-merge in a trivial follow-up.
- **R3 (pre-existing, out-of-scope)**: `AGENTS.md` has duplicate `## 10.` headings from prior history. This packet adds `## 11.` but does not renumber — fixing the collision is a separate cleanup task.

## Files Touched

- `task-packets/INDEX.md` — +2 rows (Completed table)
- `task-packets/TEMPLATE_TASK_PACKET.md` — ±1 line (stage list fix)
- `AGENTS.md` — +18 lines (new §11)
- `proof/TP-DMX-AI-ROUTING-003/PROOF.json` — created
- `proof/TP-DMX-AI-ROUTING-003/SUMMARY.md` — created (this file)

## Git State

- Branch: `claude/tp-dmx-ai-routing-003-governance-residue`
- Base SHA: `b987da994`
- Slice SHAs: G0 `bf4781ea5` · G1 `984d70e3e` · G2 `52fcdbeb5`
- Proof commit SHA: see final commit after this file is staged
- Working tree: clean after proof commit

## Rollback Plan

```bash
# Per-slice (safe — no runtime callers):
git revert <slice_sha>

# Full rollback on PR branch:
git revert <proof_sha> <G2_sha> <G1_sha> <G0_sha>
# then close PR

# Never delete proof/TP-DMX-AI-ROUTING-001/ or -002/ (sealed)
# Never amend merged history — open TP-DMX-AI-ROUTING-003-REVERT instead
```

## Next Step

1. PR Steward review-intake (check-only gate) — open PR against `main`.
2. After PR Steward `MERGE_READINESS = READY`: merge.
3. Post-merge: add self-closure INDEX row for TP-DMX-AI-ROUTING-003 (trivial follow-up).
4. When schema enum drift is prioritized: open `TP-DMX-AI-ROUTING-004`.
