# DR-DCP-015 Tooling Layer — Evidence Pack

**Assembled:** 2026-06-11 · **By:** Claude (Opus 4.8) orchestrating Sonnet/Haiku read-only sub-audits · **Branch:** `claude/intelligent-banach-8426ff`

Self-contained bundle for the DR-DCP-015 "DCP tooling layer" reconciliation. Every file is standalone markdown — copy/paste any one without needing the others. Read in numeric order for the full story.

## The three findings (TL;DR)

1. **The pasted DR-DCP-015 draft is SUPERSEDED.** It says `BUILD_TOOLING_LAYER_NOW`; the canonical ingested version says **`BUILD_AFTER_CORE_CONTRACTS`**. Use the canonical (file 03).
2. **The tooling layer is already partially built** — [PR #858](https://github.com/DDD-Enterprises/dopemux-mvp/pull/858) shipped 4 deterministic hooks + 5 skills + tests. It is *not* greenfield research.
3. **The `BUILD_AFTER_CORE_CONTRACTS` gate is CLOSED.** All 5 prerequisite contracts are `.v0`/PROVISIONAL; none is locked, and where enforcement exists it doesn't read the contract schema. So broad tooling build-out is correctly blocked until the contracts are promoted + wired.

## Manifest

| File | What it is | Confidence |
|---|---|---|
| [`01-reconciliation-memo.md`](01-reconciliation-memo.md) | **Findings** — pasted vs canonical divergence, 4 repo-evidence corrections, what's already shipped, the open frontier (TOOLING-0001 + D15) | high |
| [`02-core-contract-status-audit.md`](02-core-contract-status-audit.md) | **Findings** — per-contract status table (all 5 = PARTIAL), schema↔runtime decoupling, per-contract promotion path | high |
| [`03-DR-DCP-015-canonical.md`](03-DR-DCP-015-canonical.md) | **Source** — the canonical ingested DR-DCP-015 (verbatim, 316 lines), headline `BUILD_AFTER_CORE_CONTRACTS` | source |
| [`04-DR-DCP-015-pasted-draft-divergence.md`](04-DR-DCP-015-pasted-draft-divergence.md) | **Source** — the superseded pasted draft's §1 (both copies) + why it was overridden | source |
| [`05-source-synthesis-excerpts.md`](05-source-synthesis-excerpts.md) | **Source** — verbatim §8.3 / DR-015 summary / O-7 / D15 from the DCP 5.5 synthesis pack | source |
| [`06-repo-evidence-raw.md`](06-repo-evidence-raw.md) | **Evidence** — hook dispatcher + real payload schemas, no-plugin/no-`dcp`-CLI proof, DCP meaning, full schema inventory | high |

## Where the canonical & full design live (not copied here, to avoid drift)

- Canonical DR-DCP-015 in-tree: `claudedocs/dx-overhaul/research/DR-DCP-015-dcp-tooling-layer.md` @ branch `feat/dx-overhaul` ([PR #871](https://github.com/DDD-Enterprises/dopemux-mvp/pull/871))
- DX Overhaul Phase 1+2: `claudedocs/dx-overhaul/{00-process,01-research-synthesis,02-workflow-maps}.md` @ PR #871
- DCP 5.5 synthesis: `docs/03-reference/dcp/artifacts/DCP_5_5_SYNTHESIS_INPUT_PACK.md` (current branch)
- DR series constraints: `docs/03-reference/dcp/artifacts/DCP_DR_EXTERNAL_CONSTRAINTS_LEDGER.md`

## Related open PRs

[#871](https://github.com/DDD-Enterprises/dopemux-mvp/pull/871) (DX-overhaul docs + DR-015 intake) · [#858](https://github.com/DDD-Enterprises/dopemux-mvp/pull/858) (first hooks+skills impl) · [#862](https://github.com/DDD-Enterprises/dopemux-mvp/pull/862)/[#869](https://github.com/DDD-Enterprises/dopemux-mvp/pull/869)/[#854](https://github.com/DDD-Enterprises/dopemux-mvp/pull/854) (routing model + recon/red-lane ledger) · [#870](https://github.com/DDD-Enterprises/dopemux-mvp/pull/870) (read-only MCP facade docs)

## Suggested copy/paste order (e.g. for a GPT-5.5 synthesis prompt, per DR-015 §15)

`00-INDEX` → `01-reconciliation-memo` → `02-core-contract-status-audit` → `05-source-synthesis-excerpts` → `06-repo-evidence-raw` → (`03`/`04` if the recipient needs the full source + divergence).

## Recommended next step

Promote the 2 closest contracts first: **Contract 1** (couple `RedLaneScanner` to the taxonomy schema — already has enforcement + tests) and **Contract 5** (reconcile `dcp_project_resource_map` with the live `root_hygiene_policy.json`/`policy.py`). Those two flip the gate fastest. Do **not** build out the plugin package / `dopemux dcp` CLI (DR-015 §4/§7) until the gate opens.
