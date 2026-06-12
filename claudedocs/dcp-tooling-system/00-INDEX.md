# DCP Contract-Promotion + Tooling Layer v1 — Design Pack

**Date:** 2026-06-12 · **Branch:** `claude/intelligent-banach-8426ff` · **Status:** investigated, scoped, designed, planned, adversarially validated — **awaiting operator approval** for Phase-4 TP authoring + orchestrator load.

End-to-end architecture for opening the `BUILD_AFTER_CORE_CONTRACTS` gate: promote the 5 DCP core contracts from `.v0`/PROVISIONAL to enforced, couple the runtime to the schemas, ship receipts + approval artifacts + the `dopemux dcp` CLI, and resolve TOOLING-0001/D15 operationally. Executes the Phase-3-grade architecture work the DX-overhaul workflow maps anticipated, scoped to the DCP contracts+tooling system.

## Reading order

| File | What it is |
|---|---|
| [10-investigation.md](10-investigation.md) | Corrected ground truth: enforcement runtime map, lane↔rule namespace split, contract states, PR #858 cross-check, approval plumbing, CI wiring, binding constraints, open questions |
| [20-scope.md](20-scope.md) | System boundary, 10 workstreams, explicit exclusions, the L0–L3 promotion ladder, gate-open criteria, risks |
| [30-design.md](30-design.md) | The architecture: manifest+versioning, schema-driven scanner (B), sanctioned-change protocol (B.6), receipts (C), mutation classifier (D), approval/`accept` (E), resource map (F), CLI (G), hooks (H), TOOLING-0001 resolutions (I), plugin (J), threat model (K), decision register (L), **amendments A1–A16** |
| [40-plan.md](40-plan.md) | rev-2 plan: 14 TPs + 1 operator action across 5 waves, dependency graph, per-TP validation, gate-open declaration |
| [50-validation.md](50-validation.md) | Adversarial validation record: 4 lenses, 39 findings, blocker dispositions, rejected-with-reasons, constraint-adherence table, PASS/FAIL/NOT_RUN |

Companion evidence: [`claudedocs/dr-dcp-015-evidence-pack/`](../dr-dcp-015-evidence-pack/00-INDEX.md) (canonical DR-015, contract audit, repo evidence).

## The five headlines

1. **All 5 contracts are real but none is enforced from its schema** — where enforcement exists (red-lane scanner, repo hygiene) it's a parallel hardcoded implementation with no lane IDs. The design couples them via a taxonomy instance file + detector schema + loader with a fail-closed frozen fallback.
2. **The validation round caught the design itself weakening the most important guard** — the lane protecting contract files was drafted `project_gate` (non-blocking); it's restored to `hard_block` with an approval-artifact carve-out (B.6) so sanctioned changes flow and unsanctioned ones BLOCK.
3. **`supervisor_accepted` gets its first writer**: `dcp accept` (TTY + typed-confirm, agent-refusing) → `proof/<TP>/APPROVAL.json` → consumed by the scanner and the sanctioned-change protocol.
4. **Receipts align with DR-015 §8 and existing runtime artifacts** (PROOF.json, cockpit gate receipts) — hash-locked into committed proof bundles; honest v1 trust model (asserted identity, repo-review boundary, crypto = V2).
5. **TOOLING-0001 resolved**: det-vs-LLM ADR + manifest `enforcement_side` (1); hybrid registry — distributed discovery, centralized governance metadata (2); MCP catalog schema as CI lint (3).

## First actions on approval

1. **OP-0** (operator, minutes): CODEOWNERS entries for `schemas/dcp/`, `config/dcp/`, `proof/`.
2. Author + load **TP-101** (manifest+ADR — after PR #862 merges or enumerating its schemas) and **TP-102** (taxonomy instance) as the first wave.
3. Critical path to gate-open: 102 → 103 → 104/105 → 112.
