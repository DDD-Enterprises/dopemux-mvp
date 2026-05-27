# Task-Orchestrator Plugin Assessment (TP-CS-100)

**Date**: 2026-05-27
**Status**: Initial assessment — read-only investigation
**Workspace**: `/Users/hue/code/dopemux-mvp`
**Branch**: `task-orchestrator-claude-surface`

## Question

Does a `claude-plugins/task-orchestrator/` bundle exist locally that Dopemux could adopt as-is, fork, or treat as a reference?

## Findings

### What exists locally

Only one local plugin wraps task-orchestrator: `/Users/hue/plugins/dopemux-mission-control/`.

- **Manifest**: `.codex-plugin/plugin.json` — name `dopemux-mission-control`, version 0.1.0, **Codex-only** (no Claude Code plugin manifest).
- **MCP config**: `.mcp.json` declares two servers: `pal` (Docker exec into `mcp-pal` container) and `task-orchestrator` (stdio wrapper script).
- **Scripts**: `scripts/task-orchestrator-current-stdio.sh` — pulls `ghcr.io/jpicklyk/task-orchestrator@sha256:c73e1d4688363cdc96152145a110919b25438bbe5d8ad781f7b15751eabbb670` and pipes stdio.
- **Assets**: `assets/task-orchestrator-logback.xml` — logging config.
- **No skills, no hooks, no output style, no Claude-specific resources.**

### What does NOT exist locally

A bundled "Claude Code plugin" with the structure documented in the upstream wiki (`claude-plugins/task-orchestrator/` containing skills + hooks + output style). The wiki references this as the upstream default-mode single-agent integration; it lives in the `jpicklyk/task-orchestrator` repo, not vendored locally.

### What the upstream image provides

The pinned image (`@sha256:c73e1d...`) is the **server runtime**, not the agent-side plugin. It exposes the 13-tool MCP surface but does not ship Claude-specific skills, hooks, or output styles. Those would have to be either pulled from the upstream repo's `claude-plugins/task-orchestrator/` directory or built natively.

## Compatibility gap assessment (input for TP-CS-101)

Per the workflow guide §10 Scope note: "the bundled Claude Code plugin under `claude-plugins/task-orchestrator/` targets default-mode single-agent orchestration. Its skills, hooks, and output style assume the agent-owned phase-entry pattern (advance_item called directly) — they do not reference claim_item or coordinate claim-then-advance sequencing."

Dopemux's actual usage pattern (per repo doctrine):

- **Worktree-parallel**: 1–3 worktrees running concurrent Claude sessions on different branches. The upstream plugin's single-agent assumption breaks here without claim coordination.
- **MetaMCP role filtering**: Per `.claude/modules/coordination/authority-matrix.md`, Dopemux uses role-based tool filtering (QUICKFIX 8 tools, ACT 10, PLAN 9, RESEARCH 10, ALL 60+). Upstream plugin's skill set is fixed; doesn't integrate with role-based filtering.
- **ADHD-shaped output**: Dopemux UX requires max 10 results, max 3 options, progressive disclosure, complexity scoring. Upstream output style (whatever shape it takes) likely doesn't match these constraints.
- **Native hooks dispatcher**: All Dopemux hooks route through `src/dopemux/claude/native_hooks.py` per the project CLAUDE.md. Upstream plugin's hooks would need to dispatch via this rather than directly.
- **PAL chain integration**: Dopemux mandates `analyze → planner → codereview → precommit` per `AGENTS.md §5`. Upstream plugin's skills (per wiki) target `acceptance-criteria` / `done-criteria` schema notes, not PAL chain notes. No alignment.

## Recommendation (input for TP-CS-101)

Three-path decision tree (per Plan §9.10):

### Path A — Adopt upstream as-is

Vendor `claude-plugins/task-orchestrator/` from the upstream repo. Install in this project. Accept single-agent defaults.

- **Cost**: Low (clone + install).
- **Risk**: High mismatch with Dopemux assumptions (no worktree coordination, no MetaMCP, no ADHD output, no PAL chain integration). Likely degrades operator UX.
- **Recommendation**: Reject.

### Path B — Fork and adapt

Vendor upstream into `claude-plugins/task-orchestrator/` (or `.claude/plugins/`). Adapt skills for PAL chain notes (`analyze`, `planner`, `codereview`, `precommit`, `proof-bundle`). Swap output style for Dopemux ADHD style (per TP-CS-110). Wire hooks via `native_hooks.py` dispatcher (per `.claude/CLAUDE.md` hook section).

- **Cost**: Medium. Preserves upstream patterns where compatible; adapts where they clash.
- **Risk**: Drift from upstream — future upstream updates require re-adapting.
- **Recommendation**: Viable IF Dopemux benefits from upstream skill catalog and hook patterns. Worth checking what `claude-plugins/task-orchestrator/` actually contains before deciding.

### Path C — Native rebuild

Build Dopemux-original skills + hooks + output style. Skip the plugin entirely. Rely on §9.4 commands + §9.6 hooks + §9.11 output style as the surface.

- **Cost**: Highest in absolute terms but lower marginal cost (the plan already specs these TPs in §9).
- **Risk**: Reimplements wheels that upstream solved.
- **Recommendation**: Default IF Path B's upstream content turns out to be thin or heavily entangled with single-agent assumptions.

### Upstream content fetched (TP-CS-101 input)

Per operator authorization 2026-05-27, fetched `claude-plugins/task-orchestrator/` from `jpicklyk/task-orchestrator` main via `gh api`:

**Plugin manifest** (`.claude-plugin/plugin.json`, 274 B):
```json
{
  "name": "task-orchestrator",
  "version": "3.2.2",
  "description": "Claude Code integration for MCP Task Orchestrator — schema-aware context, note-driven workflow",
  "skills": "./skills",
  "hooks": "./hooks/hooks-config.json",
  "outputStyles": "./output-styles"
}
```

**11 skills** (each in its own directory with a `SKILL.md` doc, e.g. `quick-start/SKILL.md` = 12K):

- `batch-complete` — batch advance multiple items
- `create-item` — wraps `manage_items(create)` with schema awareness
- `dependency-manager` — wraps `manage_dependencies`
- `manage-schemas` — schema config editing
- `post-plan-workflow` — Claude Code plan-mode exit integration
- `pre-plan-workflow` — Claude Code plan-mode entry integration
- `quick-start` — operator onboarding (12K)
- `ralph` — workflow loop pattern (paired with `ralph-loop.mjs` script)
- `schema-workflow` — schema lifecycle skills
- `status-progression` — wraps `advance_item` triggers
- `work-summary` — generates work summaries from notes

**7 hooks** (Node.js `.mjs` files, total ~14K):

- `session-start.mjs` (1.1K) — fires on `SessionStart`; injects active items + guidancePointer
- `pre-plan.mjs` (505 B) — fires on `PreToolUse` matcher `EnterPlanMode`
- `post-plan.mjs` (505 B) — fires on `PostToolUse` matcher `ExitPlanMode`
- `skill-enforcement.mjs` (4.4K) — fires on `PreToolUse` matcher `manage_notes`
- `enforce-actor-attribution.mjs` (3.7K) — fires on `PreToolUse` matchers `advance_item|manage_notes`
- `subagent-start.mjs` (2.8K) — fires on `SubagentStart`; injects guidance into subagent prompt
- `hooks-config.json` (1.6K) — wires all of the above into Claude Code lifecycle events

**2 output styles** (Markdown files):

- `ralph-iteration.md` (4.8K) — output style for ralph-loop workflow iteration
- `workflow-orchestrator.md` (7.9K) — general orchestrator-aware response style

**1 substantial script**: `ralph-loop.mjs` (29K) — implements the "ralph" iteration loop pattern (self-running workflow execution).

### Decision: Path B (Fork + Adapt) — STRONGLY RECOMMENDED

Upstream content is substantial and well-architected. Key positives for Path B:

1. **Hook architecture matches Dopemux needs exactly**: `enforce-actor-attribution.mjs` + `subagent-start.mjs` + `skill-enforcement.mjs` cover the worktree-parallel + subagent + skill-injection patterns plan §9.6 specs.
2. **Hooks-config.json** wires into the exact Claude Code lifecycle events (`SessionStart`, `PreToolUse` with matchers, `PostToolUse`, `SubagentStart`) that Dopemux uses via its native_hooks.py dispatcher.
3. **Skill set covers most of plan §9.4 command specs** (create-item, dependency-manager, status-progression, batch-complete, work-summary, manage-schemas). Adapting these → /dx: commands beats native rebuild.
4. **Plan-mode integration via pre-plan / post-plan hooks** is a notable bonus Dopemux didn't spec — direct lifecycle hook into Claude Code's plan mode.

Path B adaptation requirements:

- Rewrite hooks-config.json paths to match Dopemux's `.claude/hooks/` layout (or wrap as command shims dispatched via `native_hooks.py`).
- Replace upstream MCP tool prefix `mcp__mcp-task-orchestrator__` with Dopemux's `mcp__task-orchestrator__` (per current `.mcp.json`).
- Audit `enforce-actor-attribution.mjs` against Dopemux's actor-ID convention (`{id: "worktree-<basename>-<branch>", kind: "subagent", parent: "<session>"}`) from TP-CS-046.
- Replace `ralph-iteration.md` output style or keep as opt-in alongside the Dopemux ADHD output style (TP-CS-110).
- Map upstream skill files → Dopemux `/dx:` slash command surface (skills and slash commands are different mechanisms; some adaptation needed).

Path C (native rebuild) is now NOT recommended — upstream content represents ~50K of well-tested code that would have to be reimplemented. Only justify Path C if upstream's `ralph-loop.mjs` (29K) embeds deep single-agent assumptions that can't be disentangled.

### Next action for TP-CS-101

TP-CS-101 (Plugin Decision + Implementation) should:

1. Clone `jpicklyk/task-orchestrator` to a scratch location.
2. Vendor `claude-plugins/task-orchestrator/` into `dopemux-mvp` at `claude-plugins/task-orchestrator/` (or `.claude/plugins/task-orchestrator/`).
3. Read each hook file (`enforce-actor-attribution.mjs`, `subagent-start.mjs`, `skill-enforcement.mjs`) and adapt the actor-ID convention + MCP tool prefix.
4. Wire hooks-config.json into Dopemux's `native_hooks.py` dispatcher (per `.claude/CLAUDE.md` hook section).
5. Decide whether to keep `ralph-iteration.md` output style or replace with TP-CS-110's Dopemux ADHD style.
6. Adapt skill files: keep upstream skills available; layer Dopemux `/dx:` slash commands on top for ADHD-optimized variants.

## Conclusion

TP-CS-100 closes with: **upstream `claude-plugins/task-orchestrator/` is substantial and well-architected; Path A rejected (single-agent assumptions); Path B (fork + adapt) STRONGLY RECOMMENDED with adaptation plan above. Implementation work moves to TP-CS-101.**
