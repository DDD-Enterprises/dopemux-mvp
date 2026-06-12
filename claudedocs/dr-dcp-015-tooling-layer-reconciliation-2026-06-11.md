# DR-DCP-015 Tooling Layer — Reconciliation Memo

| | |
|---|---|
| **Date** | 2026-06-11 |
| **Author** | Claude (Opus 4.8), read-only grounding pass |
| **Type** | Reconciliation / analysis (no source changes) |
| **Trigger** | Operator pasted a `BUILD_TOOLING_LAYER_NOW` draft of DR-DCP-015 and asked to check open PRs for related research |
| **Branch** | `claude/intelligent-banach-8426ff` (worktree) |
| **Status** | Advisory. Supersedes the pasted draft's headline; does **not** alter the canonical ingested DR-DCP-015. |

---

## TL;DR

1. **The pasted draft is superseded.** It recommends `BUILD_TOOLING_LAYER_NOW`. The canonical DR-DCP-015 already ingested into the repo (PR #871) recommends **`BUILD_AFTER_CORE_CONTRACTS`**, and the Phase-2 workflow maps + DCP 5.5 synthesis pack are already built on that sequencing. Do **not** act on the pasted headline.
2. **The tooling layer is not greenfield research — it is partially built.** PR #858 already shipped 4 deterministic hooks + 5 skills that instantiate DR-DCP-015's deterministic-guard recommendation, with tests.
3. **Four of the pasted draft's assumptions about *this repo* are false** (no plugin manifest, no `dopemux dcp` CLI, hooks are one dispatcher not per-event scripts, "DCP" = Data Control Plane). Corrected below with file-path evidence.
4. **The real open work is narrow and named:** the 3 `TOOLING-0001` decisions (synthesis §8.3) + decision D15 (tooling boundaries), gated behind the 5 core contracts (P1). Everything else the draft proposes is either already decided or already built.

---

## 1. Version divergence (the crux)

| | Pasted draft | Canonical (ingested) |
|---|---|---|
| **§1 headline** | `BUILD_TOOLING_LAYER_NOW` | `BUILD_AFTER_CORE_CONTRACTS` |
| **Rationale** | "standards exist and are evolving; waiting risks stove-piped tooling" | lock 5 core contracts first, then build tooling on a stable substrate |
| **Location** | operator message (two copies) | [`claudedocs/dx-overhaul/research/DR-DCP-015-dcp-tooling-layer.md`](../dx-overhaul/research/DR-DCP-015-dcp-tooling-layer.md) on branch `feat/dx-overhaul` — [PR #871](https://github.com/DDD-Enterprises/dopemux-mvp/pull/871) |
| **Downstream use** | none | drives workflow-map primitive **P1** ("Five core contracts … Locked FIRST (DR: BUILD_AFTER_CORE_CONTRACTS)") and synthesis **O-7** / **D15** |

**Verified directly** via `gh pr diff 871`: the ingested copy's §1 reads `BUILD_AFTER_CORE_CONTRACTS`, and the workflow-maps P1 row cites that directive verbatim.

**Why the canonical sequencing is correct (not just newer):** the tooling layer's entire value is *deterministic* red-lane enforcement. You cannot deterministically enforce a red-lane taxonomy, receipt schema, mutation classes, approval artifact, or path/resource map that does not exist yet. Building enforcement tooling before its contracts produces exactly the failure mode the synthesis names a **"vibe plane, not a red-lane gate"** — probabilistic guards masquerading as hard gates. The pasted draft's "ship now to avoid stove-piping" argument is reasonable in the abstract but inverts the dependency: contracts are the anti-stovepipe mechanism, and they come first.

---

## 2. Repo-evidence corrections (report assumptions vs. reality)

The pasted draft reads as greenfield design. This repo is not greenfield, and four load-bearing assumptions are wrong. Each verified on the current branch this session.

| # | Draft assumes | Repo reality | Evidence |
|---|---|---|---|
| 1 | A `dcp-control-plane-plugin/.claude-plugin/plugin.json` package (§4) | **No plugin system exists.** Extensions are `.claude/commands/*.md` (path → slash-name) + global SuperClaude skills. The proposed package is a *new* architecture, not "standardize the existing pattern." | `find . -name plugin.json` and `find . -name .claude-plugin` → empty |
| 2 | A `dopemux dcp` CLI to "standardize deterministic actions" (§7) | **No `dcp` CLI subcommand exists.** `src/dopemux/dcp/` is a *library* (`red_lane.py`, `red_lane_scanner.py`, `control_snapshot.py`, `proof_pointer_reader.py`, `proof_family.py`). All §7 commands are greenfield. | `rg "\bdcp\b" src/dopemux/cli.py` → no match; `ls src/dopemux/dcp/` → 7 `.py` files, no CLI entry |
| 3 | Per-event hook scripts (`session-start`, `pre-tool-red-line`, …) (§6) | **All 11 lifecycle events route through one dispatcher** (`src/dopemux/claude/native_hooks.py`) keyed on `hook_event_name`; blocks via exit-2 + `permissionDecision: deny`. The legacy `.claude/hooks/*.sh` scripts are orphans not wired in settings.json. | project `.claude/CLAUDE.md` ("11 lifecycle hooks … one entry point: native_hooks.py"); `.claude/settings.json` |
| 4 | "DCP" used loosely | **DCP = Data Control Plane** (red-lane / mutation-class / proof governance). *Not* DopeContext (always "dope-context"). A second surface, `dcp-readonly-facade`, is the read-only MCP evidence projector built on top. | `schemas/dcp/README.md` ("the DCP (Data Control Plane) core contract floor") |

**Net:** the draft's §4 (plugin package) and §7 (CLI) describe *targets to build*, not patterns to adopt. Its §6 (hooks) target already partly exists in a different shape (single dispatcher) and is partly shipped (PR #858).

---

## 3. What already exists (open PRs + on-disk)

| Surface | PR / path | Status |
|---|---|---|
| **DX Overhaul Phase 1+2 + DR-015 intake** | [PR #871](https://github.com/DDD-Enterprises/dopemux-mvp/pull/871) — `claudedocs/dx-overhaul/{00-process,01-research-synthesis,02-workflow-maps}.md` + `research/DR-DCP-015-*.md` | open; highest-signal design set; contains a **§14 repo-evidence answers appendix** (the draft's own open questions answered) |
| **First tooling implementation** | [PR #858](https://github.com/DDD-Enterprises/dopemux-mvp/pull/858) | open; 4 hooks (`dcp_surface_guard` PreToolUse hard-deny, denylist nudge, MCP health probe, proof-tracking guard) + 5 skills (`/dcp:doctor`, `/dcp:denylist-check`, `/mcp:doctor`, `/proof:bundle`, `/tp:validate`) + tests |
| **Red-lane / routing substrate** | [PR #862](https://github.com/DDD-Enterprises/dopemux-mvp/pull/862), [#869](https://github.com/DDD-Enterprises/dopemux-mvp/pull/869), [#854](https://github.com/DDD-Enterprises/dopemux-mvp/pull/854) | routing domain model (9 schemas, dual-audited) + recon packets incl. **mutation red-lane ledger** + slash-command inventory |
| **Read-only MCP facade** | [PR #870](https://github.com/DDD-Enterprises/dopemux-mvp/pull/870) | ChatGPT MCP read-only facade docs (failure runbook, manual validation, tunnel integration) |
| **DCP 5.5 architecture synthesis** | [`docs/03-reference/dcp/artifacts/DCP_5_5_SYNTHESIS_INPUT_PACK.md`](../../docs/03-reference/dcp/artifacts/DCP_5_5_SYNTHESIS_INPUT_PACK.md) (on this branch) | §2.5 tooling surfaces, §8.3 TOOLING-0001, O-7, D15 |
| **DR-DCP-001..015 constraints** | [`docs/03-reference/dcp/artifacts/DCP_DR_EXTERNAL_CONSTRAINTS_LEDGER.md`](../../docs/03-reference/dcp/artifacts/DCP_DR_EXTERNAL_CONSTRAINTS_LEDGER.md) | full DR series summarized; DR-016 noted as memory+tooling synthesis |

---

## 4. What the canonical DR-015 actually mandates

Quoted from the synthesis pack's own DR-015 summary (`DCP_5_5_SYNTHESIS_INPUT_PACK.md` line ~410), so the constraints below are the *ingested* directive, not the pasted draft:

- **Directive:** `BUILD_AFTER_CORE_CONTRACTS` — lock first: **red-lane taxonomy · receipt schema · mutation classes · approval artifact · project path+resource maps**.
- **Control split:** *"LLMs reason → hooks enforce → CLI standardizes → proof records → supervisor decides."*
- **Deterministic vs LLM:** deterministic (hooks/CLI: forbidden-path, schema, receipts, red-lines, hard blocks across UserPromptExpansion + PreToolUse + pre-commit + CI) vs LLM (skills/subagents: teach/synthesize/author, **advisory only**). *"Probabilistic guard = vibe plane, not a red-lane gate."*
- **Plugin V1:** `defaultEnabled:false`; no monitors/channels/default-agent-override; side-effectful skills `disable-model-invocation:true`.
- **Cross-project packaging:** `dcp-core` + `dcp-profile-dopemux` + `dcp-profile-dnh-crm` + repo-local. Extend via rules/schemas/path-maps, **not** forked prompts; repo-local must **not** weaken core denies.
- **NEVER build:** channels · default-agent-override · auto-approve-merge-resolve · CRM-client-send-from-skills · broad live-writer plugin.
- **Git-hook caveat:** client-side Git hooks are bypassable (`--no-verify`) → must duplicate the check in CI.

This is materially richer and more conservative than the pasted draft's §12 ("Core hooks + CLI = v1"). The pasted draft and canonical agree on the *never* list and the deterministic/LLM split; they disagree only on **sequencing** — which is the whole point of the headline flip.

---

## 5. The real open frontier

Per synthesis §8.3 and D15, the genuinely undecided work is small and named:

**`TOOLING-0001` — three decisions requested (synthesis §8.3 / §9):**
1. Which surfaces map to **deterministic hooks** vs **LLM instruction**?
2. **Centralized** skill/agent/command registry vs **distributed** discovery?
3. **Enforce an MCP config schema + deprecation tracking?**

**D15 — tooling boundaries:** what belongs in a DCP Claude plugin vs skills vs deterministic hooks vs `dopemux dcp` CLI; advisory vs blocking hooks; how dNh (file-path-level) red-lane hooks differ from Dopemux (governance-level). Decision rule already noted: **block > ask > warn > allow**; client hooks bypassable → CI.

**Gate (O-7):** all of the above is "build after contracts." The 5 core contracts are the prerequisite. Status of those contracts was **not** audited in this pass (see uncertainty below) — that audit is the logical next step before any TOOLING-0001 resolution.

---

## 6. Recommendation

1. **Discard the pasted draft's `BUILD_TOOLING_LAYER_NOW` headline.** Treat the pasted text as a historical/alternate draft; the ingested `BUILD_AFTER_CORE_CONTRACTS` version (PR #871) is canonical.
2. **Before resolving TOOLING-0001, audit the 5 core-contract statuses** (red-lane taxonomy, receipt schema, mutation classes, approval artifact, path/resource maps). PR #862 (routing domain model) + the mutation red-lane ledger (PR #869) are substrate for contract #1; the others need a status check.
3. **Do not author a new plugin package or `dopemux dcp` CLI from the pasted §4/§7 yet** — those are downstream of TOOLING-0001/D15, which are still open.
4. **Anyone building from DR-DCP-015 should read the canonical file + this memo**, not the pasted draft, to avoid re-litigating sequencing and re-discovering the 4 repo-evidence corrections.

---

## 7. Evidence & confidence ledger

| Claim | Confidence | Basis |
|---|---|---|
| Pasted = `BUILD_NOW`, canonical = `BUILD_AFTER_CORE_CONTRACTS` | **certain** | direct `gh pr diff 871` + operator message |
| Workflow-map P1 encodes the canonical directive | **certain** | `gh pr diff 871` grep |
| No plugin manifest / no `dopemux dcp` CLI on this branch | **certain** | `find` / `rg` run this session |
| Hooks = single `native_hooks.py` dispatcher over 11 events | **high** | project `.claude/CLAUDE.md` + subagent read of dispatcher |
| DCP = Data Control Plane | **high** | `schemas/dcp/README.md` |
| PR #858 contents (4 hooks + 5 skills + tests) | **high** | subagent read of PR diff (not personally opened) |
| TOOLING-0001 three decisions + D15 text | **high** | grep of synthesis pack this session (lines 378–410, 694) |
| Status of the 5 core contracts | **UNKNOWN** | not audited this pass — explicit gap |
| §14 repo-evidence appendix exists in 02-workflow-maps.md | **medium** | relayed by subagent; not personally opened |

**Remaining uncertainty / risk:** core-contract completion status is unaudited, so "ready to build tooling" cannot be asserted. PR #858 may have already made some TOOLING-0001 §8.3-decision-(1) choices implicitly (surfaces → hooks); that PR's design rationale was not cross-checked against §8.3 in this pass.

## 8. Sources

- Operator-pasted DR-DCP-015 draft (two copies, headline `BUILD_TOOLING_LAYER_NOW`).
- Canonical DR-DCP-015 — `claudedocs/dx-overhaul/research/DR-DCP-015-dcp-tooling-layer.md` @ `feat/dx-overhaul` (PR #871).
- `claudedocs/dx-overhaul/02-workflow-maps.md` (primitive P1) @ PR #871.
- `docs/03-reference/dcp/artifacts/DCP_5_5_SYNTHESIS_INPUT_PACK.md` §2.5, §8.3, O-7, D15 (on current branch).
- `schemas/dcp/README.md`; project `.claude/CLAUDE.md` (hooks); `src/dopemux/cli.py`, `src/dopemux/dcp/` (this branch).
- PRs #858, #862, #869, #870, #871 (`gh`).
