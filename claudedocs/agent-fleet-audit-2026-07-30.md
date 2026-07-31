# Agent Fleet Audit Ledger — 2026-07-30

**Packet**: TP-DMX-AGENT-FLEET-0001
**Method**: deterministic inspection (grep/frontmatter parse/cmp), no runtime calls.
**Scope**: 104 repo files + 33 personal-lane files = 137 total.
**Note**: two cheap-model audit subagents (Kimi-K2.5, GLM-5.2) were delegated this audit and both stopped early without writing output (platform early-stop). Audit completed in-session deterministically. Recorded for proof honesty.

## Surface inventory

| Surface | Files | Role |
|---|---|---|
| `.github/agents/*.agent.md` | 6 | Copilot custom agents (VS Code target, handoff-chained) |
| `.claude/personas/*.agent.md` | 35 | Persona library (canonical, runtime-primary via `InstructionManager`) |
| `.claude/personas/*-dopemux.md` | 13 | Dopemux-tuned persona bodies (no frontmatter by design) |
| `.claude/personas/PERSONA_INDEX.md` | 1 | Hand-maintained index |
| `.claude/agents/*.md` | 6 | Curated active set (4 agents + `_index.md` + 1 stray duplicate) |
| `src/dopemux/personas/*.agent.md` | 10 | Packaged wheel fallback — **byte-identical copies** of canonical |
| `templates/skills/*/SKILL.md` | 20 | Skill templates (2 runner-variant families) |
| `~/.commandcode/agents/*.md` | 17 | Personal Command Code agents (lane S8) |
| `~/.claude/agents/*.md` | 16 | Personal Claude Code agents (lane S8) |

Runtime truth (`src/dopemux/claude/instruction_manager.py`): `.claude/personas/*.agent.md` resolves first (alias table lines 41-59), packaged `src/dopemux/personas/` is the `dopemux init` fallback. Aliased stems: task-researcher, task-planner, principal-software-engineer, janitor, workflow-manager, workflow-executor, se-system-architecture-reviewer, wg-code-sentinel, devops-expert.

## Verdicts — `.github/agents/` (6/6 KEEP)

All 6 conform to `config/instructions/agents.instructions.md`: description (single-quoted, 50-150 chars), name, least-privilege tools (readers = read+search; implementer/testgen add edit+execute — justified), `target: vscode` (correct: handoffs are VS Code-only), `infer: true`, handoff targets all resolve within the set.

- UNKNOWN: `model: 'Claude Sonnet 4.5'` external vendor verification NOT_RUN (web unavailable this session). Kept: matches the repo's own authoring-guide example and is marked "repo-established Copilot model" in-file.
- Minor: reviewer/testgen lack the lane comments the other 4 carry. Cosmetic; not changed (no cosmetic-only edits).

## Verdicts — `.claude/personas/*.agent.md` (35)

| Verdict | Files | Issues |
|---|---|---|
| KEEP | adr-generator, devops-expert, github-actions-expert, implementation-plan, prd, principal-software-engineer(FIX-name), se-* (6), specification(FIX-name), task-planner, task-researcher(FIX-tools), tech-debt-remediation-plan(FIX-name), wg-code-alchemist(FIX-name), wg-code-sentinel(FIX-name), workflow-executor, workflow-manager, critical-thinking(FIX-name), devils-advocate(FIX-name), search-ai-optimization-expert(FIX-name), prompt-engineer(FIX name+tools) | see FIX columns |
| FIX | 13 missing `name:`: critical-thinking, devils-advocate, gilfoyle→archive, janitor, mentor→archive, principal-software-engineer, prompt-builder, prompt-engineer, search-ai-optimization-expert, specification, tech-debt-remediation-plan, wg-code-alchemist, wg-code-sentinel | frontmatter |
| FIX | Raw legacy VS Code tool ids instead of least-privilege aliases — **16 files** (initial ledger listed 4; validation gate B2 caught the full set): janitor (worst: `vscode/installExtension`, `vscode/vscodeAPI`…), task-researcher, prompt-builder, principal-software-engineer, critical-thinking, specification, tech-debt-remediation-plan, wg-code-alchemist, wg-code-sentinel, search-ai-optimization-expert, devops-expert, github-actions-expert, implementation-plan, prd, se-gitops-ci-specialist, se-security-reviewer, se-system-architecture-reviewer, se-technical-writer, se-ux-ui-designer, task-planner, workflow-executor, workflow-manager (all FIXED to role-scoped aliases); meta-agentic-project-scaffold→archive | tools |
| FIX (gate-caught) | task-planner tools contained `context7` + azure/terraform leftovers; python-expert-dopemux.md:87 `Route to Task-Master` → Task-Orchestrator; templates/skills/ci-remediation-specialist description unquoted colon (YAML error). All found by S9 gates after truncated initial greps — ledger corrected | stale refs / yaml |
| FIX | 4 missing `tools:` (= all tools granted): adr-generator, prompt-engineer, python-mcp-expert, Beast-Mode→archive | tools |
| FIX | prompt-builder: body mandates `context7` (lines 56, 175) — service not in fleet | stale ref |
| ARCHIVE | gilfoyle (snark voice, zero operational value), Ultimate-Transparent-Thinking-Beast-Mode (29KB mandatory-sequential-thinking injection; service not in fleet), context7 (org-level-only `mcp-servers` block invalid at repo level; external hosted MCP not in fleet), meta-agentic-project-scaffold ("pull files from awesome-copilot" scraper; over-privileged: `updateUserPreferences`, `copilotCodingAgent`), plan (thin wrapper per PERSONA_INDEX), mentor (generic; superseded by socratic-mentor/learning-guide dopemux variants) | consolidation |
| KEEP (model note) | se-* ×6 pin `GPT-5`; modernization `GPT-5`; meta-scaffold/python-mcp-expert `GPT-4.1` — plausible Copilot ids, external verification NOT_RUN (web unavailable); kept per repo-established pattern | UNKNOWN |

No Task-Master / Zen-MCP / mem4sprint / o3 / gemini-2.5 hits anywhere in `.claude/personas/` (grep, 0 hits). No file exceeds the 30k-char guide limit (max 29,019 = Beast-Mode, archived).

## Verdicts — `.claude/personas/*-dopemux.md` (13 KEEP, 1 FIX-note)

No frontmatter by design (persona bodies, paired with `~/.claude/agents` counterparts per index). Zero stale-fleet hits. Serena/ConPort "authority" claims verified against `mcp_catalog.yaml` — both servers exist in fleet (serena worktree-scoped pending P-20; conport worktree-scoped pending P-18), claims directionally correct.
- backend-architect, devops-architect, frontend-architect, general-purpose, learning-guide, performance-engineer, python-expert, quality-engineer, security-engineer, socratic-mentor, statusline-setup, system-architect, technical-writer: KEEP.

## Verdicts — PERSONA_INDEX.md (FIX)

- Claims "48 persona files" — accurate today (35 + 13); must be regenerated after archives (→ 42 + archive note).
- Quick-pick table: all entries resolve to on-disk files (verified). Post-archive entries for gilfoyle/Beast-Mode/context7/meta-scaffold/plan/mentor must be removed.
- Overlap section resolves as: archive plan.agent.md, mentor.agent.md; keep remaining groups (distinct scopes, documented).

## Verdicts — `.claude/agents/` (4 FIX-REWRITE + 1 stray + index FIX)

| File | Verdict | Evidence |
|---|---|---|
| architect.md | FIX-REWRITE | o3/o3-mini/o3-pro/gemini-2.5 ×6 (lines 16,26,27,31,49,92), Context7, Zen-MCP; no `tools:` |
| developer.md | FIX-REWRITE | same model staleness ×6, Context7 ×2, Task-Master (line 143); no `tools:` |
| project-manager.md | FIX-REWRITE | mem4sprint (lines 24,129), Task-Master ×4 (25,138,151,206), stale models ×5; no `tools:` |
| researcher.md | FIX-REWRITE | Context7 ×3 (25,39…), stale models ×6; no `tools:` |
| _index.md | FIX | Task-Master (108), mem4sprint (166), stale models (52-65), "48 personas" claim, Context7 |
| python-mcp-expert.agent.md | REMOVE (stray) | **byte-identical** to `.claude/personas/python-mcp-expert.agent.md` (cmp verified); `_index.md` defines curated set as 4 agents |

## Verdicts — `src/dopemux/personas/` (10 KEEP-as-generated)

Byte-identical to canonical (verified: `scripts/sync_personas.py --check` exit 0). Drift risk resolved by new sync script + `tests/arch/test_persona_fleet_contract.py`. No aliased/packaged stem is in the archive set — fallback resolution safe.

## Verdicts — `templates/skills/` (20 KEEP)

- name ↔ directory match: 20/20 OK.
- Variant families (testgen ×4, pr-docgen-sync ×4): consistent wrapper pattern — base skill + per-runner wrappers differing in frontmatter description, title, and routing section only (~93 lines, runner-scoped). By design; no change.
- Descriptions have clear delegation triggers. pr-docgen-sync base description is ~600 chars (long but functional) — left as-is (no cosmetic-only edits).

## Personal lane (S8) — `~/.commandcode/agents/` (17) + `~/.claude/agents/` (16)

- 16/17 commandcode files compliant (name, description, category). **FIXED**: `dopemux.md` missing required `name:` — added `name: dopemux`. Opencode keys (`mode`, `permission`, `color`) kept: harmless passthrough in Command Code, functional in opencode. Model `anthropic/claude-sonnet-4-5` kept (BYO-provider passthrough, observed live in roster).
- 15/16 cross-runtime pairs byte-identical; `security-engineer.md` differs by exactly one line (runtime name in context note) — intentional mirroring, no change.
- Neither set declares `tools:`. Doc says omitted = no tools; observed behavior = agents dispatch and use tools. **CONFLICT unresolved** — recorded UNKNOWN; no restrictive tools lists added to working agents without runtime evidence.
- Roster difference: `dopemux.md` exists only in commandcode set. Left as-is (intent UNKNOWN).
- Model pinning on personal agents: considered, **rejected** — inherit-session is the working default; TP lane tagging (done in packet) is the taste-compliant routing mechanism.
- Personal-lane edits are proof-recorded here and excluded from the PR diff.

## Archive set (S4) — final

`gilfoyle`, `Ultimate-Transparent-Thinking-Beast-Mode`, `context7`, `meta-agentic-project-scaffold`, `plan`, `mentor` → `.claude/personas/archive/`. None aliased in `ROLE_ALIASES`; none packaged; no repo-wide filename references outside PERSONA_INDEX (grep-verified at implementation time, recorded in proof).
