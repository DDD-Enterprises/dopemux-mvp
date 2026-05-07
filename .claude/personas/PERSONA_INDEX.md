# Persona Index — Decision Tree

**Purpose**: 48 persona files in this directory across two naming conventions (`*.agent.md` and `*-dopemux.md`). This index groups them by domain and flags overlap so you can pick the right persona without reading all 48.

**Naming convention** (historical, do not rename):
- `*-dopemux.md` — Dopemux-customized variants of standard personas (often paired with a `~/.claude/agents/<name>.md` global counterpart).
- `*.agent.md` — broader "agent" library, including non-engineering personas (mentors, advocates, etc.) and specialized roles.

If both forms exist for the same role, prefer the **dopemux variant** for project work (it has ADHD optimizations and ConPort integration baked in); use the `.agent.md` form for cross-project / general use.

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
| Implementation plans | `implementation-plan.agent.md` or `plan.agent.md` |
| Task planning / breakdown | `task-planner.agent.md` |
| Research | `task-researcher.agent.md` (focused) or `search-ai-optimization-expert.agent.md` (web/SEO) |
| Modernization / migration | `modernization.agent.md` |
| Tech debt cleanup | `tech-debt-remediation-plan.agent.md` |
| Issue triage / refinement | `refine-issue.agent.md` |
| Workspace cleanup | `janitor.agent.md` |
| Statusline config | `statusline-setup-dopemux.md` |
| MCP context lookup | `context7.agent.md` |
| Critical thinking / red-team | `critical-thinking.agent.md` or `devils-advocate.agent.md` |
| Senior engineering judgment | `principal-software-engineer.agent.md` |
| Mentoring / teaching | `mentor.agent.md`, `socratic-mentor-dopemux.md`, `learning-guide-dopemux.md` |
| Product strategy | `se-product-manager-advisor.agent.md` |
| Prompt engineering | `prompt-builder.agent.md` or `prompt-engineer.agent.md` |
| Code alchemy / cleanups | `wg-code-alchemist.agent.md` |
| Code-quality sentinel | `wg-code-sentinel.agent.md` |
| Workflow orchestration | `workflow-executor.agent.md` or `workflow-manager.agent.md` |
| General-purpose fallback | `general-purpose-dopemux.md` |
| Self-bootstrapping new agent system | `meta-agentic-project-scaffold.agent.md` |
| Maximum-rigor, transparent reasoning | `Ultimate-Transparent-Thinking-Beast-Mode.agent.md` |
| Snarky senior engineer voice | `gilfoyle.agent.md` |

## Known overlap (candidates for future consolidation)

Flagged here, **not** deleted — leave consolidation for a deliberate review pass:

- **Architecture review**: `se-system-architecture-reviewer.agent.md` ↔ `principal-software-engineer.agent.md` ↔ `system-architect-dopemux.md` — three perspectives on system design. Use `se-system-architecture-reviewer` for review, `system-architect-dopemux` for design, `principal-software-engineer` for senior judgment calls.
- **Plans**: `implementation-plan.agent.md` ↔ `plan.agent.md` ↔ `task-planner.agent.md` — pick `task-planner` for breaking down work, `implementation-plan` for "how to build feature X", `plan.agent.md` is a thin wrapper.
- **Mentoring**: `mentor.agent.md`, `socratic-mentor-dopemux.md`, `learning-guide-dopemux.md` — all teach. `socratic-mentor` asks questions; `learning-guide` walks through; `mentor` is the generic.
- **Tech writing**: `technical-writer-dopemux.md` ↔ `se-technical-writer.agent.md` — keep dopemux for project work.
- **Prompt work**: `prompt-builder.agent.md` ↔ `prompt-engineer.agent.md` — `builder` for templating, `engineer` for refinement and evaluation.
- **Workflow**: `workflow-executor.agent.md` ↔ `workflow-manager.agent.md` — manager designs, executor runs.
- **DevOps**: `devops-architect-dopemux.md` ↔ `devops-expert.agent.md` ↔ `se-gitops-ci-specialist.agent.md` — narrow CI/CD work to `gitops-ci`; broader infra to `devops-architect-dopemux`.

## Agents directory (curated active set)

The companion `agents/` directory contains a smaller curated set used directly by `/dx:` and `/sc:` flows: `architect`, `developer`, `project-manager`, `researcher`. See `agents/_index.md` for those. **personas/** is the full library; **agents/** is the curated active set.
