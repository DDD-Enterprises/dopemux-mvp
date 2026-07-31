# Persona Index — Decision Tree

**Purpose**: 42 active persona files in this directory across two naming conventions (`*.agent.md` ×29 and `*-dopemux.md` ×13). This index groups them by domain and flags overlap so you can pick the right persona without reading all 42.

**Naming convention** (historical, do not rename):
- `*-dopemux.md` — Dopemux-customized variants of standard personas (often paired with a `~/.claude/agents/<name>.md` global counterpart).
- `*.agent.md` — broader "agent" library, including non-engineering personas (advocates, domain experts) and specialized roles.

If both forms exist for the same role, prefer the **dopemux variant** for project work (it has ADHD optimizations and ConPort integration baked in); use the `.agent.md` form for cross-project / general use.

**Archive**: `archive/` holds 6 retired personas (TP-DMX-AGENT-FLEET-0001, 2026-07-30): `gilfoyle`, `Ultimate-Transparent-Thinking-Beast-Mode`, `context7`, `meta-agentic-project-scaffold`, `plan`, `mentor`. Retired for: zero operational value, dead/unfleeted service mandates (context7, sequential-thinking), invalid org-level `mcp-servers` config, or exact redundancy. Nothing was deleted; `git log` and `archive/` preserve all content. Archived personas are not indexed below and are not loaded by `InstructionManager` (it globs only `*.agent.md` in this directory).

## Quick-pick by task

| You need… | Pick |
|---|---|
| System / architecture review | `se-system-architecture-reviewer.agent.md` (review) or `system-architect-dopemux.md` (design) |
| Backend implementation | `backend-architect-dopemux.md` |
| Frontend implementation | `frontend-architect-dopemux.md` |
| Security audit | `se-security-reviewer.agent.md` (review) or `security-engineer-dopemux.md` (design+impl) |
| Python work | `python-expert-dopemux.md` (general) or `python-mcp-expert.agent.md` (MCP servers) |
| Performance | `performance-engineer-dopemux.md` |
| QA / test strategy | `quality-engineer-dopemux.md` |
| DevOps / infra | `devops-architect-dopemux.md` (design) or `devops-expert.agent.md` (hands-on) or `se-gitops-ci-specialist.agent.md` (CI/CD specifically) |
| GitHub Actions | `github-actions-expert.agent.md` |
| Tech writing / docs | `technical-writer-dopemux.md` or `se-technical-writer.agent.md` |
| ADRs | `adr-generator.agent.md` |
| Specifications | `specification.agent.md` |
| PRD authoring | `prd.agent.md` |
| UX/UI design | `se-ux-ui-designer.agent.md` |
| Implementation plans | `implementation-plan.agent.md` |
| Task planning / breakdown | `task-planner.agent.md` |
| Research | `task-researcher.agent.md` (focused) or `search-ai-optimization-expert.agent.md` (web/SEO) |
| Modernization / migration | `modernization.agent.md` |
| Tech debt cleanup | `tech-debt-remediation-plan.agent.md` |
| Issue triage / refinement | `refine-issue.agent.md` |
| Workspace cleanup | `janitor.agent.md` |
| Statusline config | `statusline-setup-dopemux.md` |
| Critical thinking / red-team | `critical-thinking.agent.md` or `devils-advocate.agent.md` |
| Senior engineering judgment | `principal-software-engineer.agent.md` |
| Mentoring / teaching | `socratic-mentor-dopemux.md` (asks questions) or `learning-guide-dopemux.md` (walks through) |
| Product strategy | `se-product-manager-advisor.agent.md` |
| Prompt engineering | `prompt-builder.agent.md` or `prompt-engineer.agent.md` |
| Code alchemy / cleanups | `wg-code-alchemist.agent.md` |
| Code-quality sentinel | `wg-code-sentinel.agent.md` |
| Workflow orchestration | `workflow-executor.agent.md` or `workflow-manager.agent.md` |
| General-purpose fallback | `general-purpose-dopemux.md` |

## Known overlap (resolved TP-DMX-AGENT-FLEET-0001)

Consolidation pass completed 2026-07-30. Remaining overlap is deliberate — distinct scopes:

- **Architecture review**: `se-system-architecture-reviewer.agent.md` ↔ `principal-software-engineer.agent.md` ↔ `system-architect-dopemux.md` — three perspectives on system design. Use `se-system-architecture-reviewer` for review, `system-architect-dopemux` for design, `principal-software-engineer` for senior judgment calls.
- **Plans**: `implementation-plan.agent.md` ↔ `task-planner.agent.md` — `task-planner` breaks down work; `implementation-plan` covers "how to build feature X". (`plan.agent.md`, the thin wrapper, is archived.)
- **Mentoring**: `socratic-mentor-dopemux.md` ↔ `learning-guide-dopemux.md` — `socratic-mentor` asks questions; `learning-guide` walks through. (Generic `mentor.agent.md` is archived.)
- **Tech writing**: `technical-writer-dopemux.md` ↔ `se-technical-writer.agent.md` — keep dopemux for project work.
- **Prompt work**: `prompt-builder.agent.md` ↔ `prompt-engineer.agent.md` — `builder` for templating, `engineer` for refinement and evaluation.
- **Workflow**: `workflow-executor.agent.md` ↔ `workflow-manager.agent.md` — manager designs, executor runs.
- **DevOps**: `devops-architect-dopemux.md` ↔ `devops-expert.agent.md` ↔ `se-gitops-ci-specialist.agent.md` — narrow CI/CD work to `gitops-ci`; broader infra to `devops-architect-dopemux`.

## Agents directory (curated active set)

The companion `agents/` directory contains a smaller curated set used directly by `/dx:` and `/sc:` flows: `architect`, `developer`, `project-manager`, `researcher`. See `agents/_index.md` for those. **personas/** is the full library; **agents/** is the curated active set.

## Packaged fallback subset

`src/dopemux/personas/` contains 10 byte-identical copies (workflow-manager, workflow-executor, wg-code-sentinel, task-planner, task-researcher, se-system-architecture-reviewer, se-security-reviewer, principal-software-engineer, janitor, devops-expert) shipped in the wheel as the `dopemux init` fallback. **Generated, never hand-edited** — sync via `python scripts/sync_personas.py`; drift gate: `tests/arch/test_persona_fleet_contract.py`.
