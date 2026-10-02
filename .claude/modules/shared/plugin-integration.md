# Claude Code Plugin Integration Card

**Module Version**: 1.1.0
**Observed**: 2026-10-02 against `~/.claude/plugins/installed_plugins.json` (14 installed, user scope), 14 claude.ai-synced plugins, and `claude plugin list`
**Enforced by**: project `.claude/settings.json` `enabledPlugins` (25 explicit entries; marketplaces `openai-codex` and `karpathy-skills` registered in `extraKnownMarketplaces`). Project scope overrides user scope; `.claude/settings.local.json` overrides project.
**Scope**: Claude Code runtime only. Codex/Gemini/OpenCode do not load these plugins.
**Authority**: Subordinate to AGENTS.md and `.claude/claude.md`. When a plugin skill conflicts with repo doctrine, doctrine wins; follow the skill only where it agrees.

## Enabled — use automatically

Enabled for this project: `superpowers`, `codex`, `frontend-design`, `claude-md-management`, `pyright-lsp`, `andrej-karpathy-skills` (as the `developer` preload), and `superdevflow@synced`. The project setting enables a plugin but does not install it. A skill named here is only callable when its plugin shows in the session's skill list. If it does not, say `NOT_AVAILABLE` and proceed under doctrine.

| Trigger | Skill / command | Repo override |
|---|---|---|
| Bug, test failure, unexpected behavior | `superpowers:systematic-debugging` | Never bypass safety checks to clear a symptom (developer agent §Debugging). |
| Implementing a feature or bugfix | `superpowers:test-driven-development` | Narrow-first validation; Task Packet `commit.allowlist` is a hard edit boundary. |
| About to claim done/fixed/passing, commit, or open a PR | `superpowers:verification-before-completion` | Report PASS / FAIL / NOT_RUN; `VERIFIED` per AGENTS.md §9. |
| Multi-step task with spec, before touching code | `superpowers:writing-plans` | Place plan files per `docs/03-reference/filesystem-guide.md`; not a substitute for a Task Packet. |
| New feature/behavior with unclear intent | `superpowers:brainstorming` | Interactive, so supervisor only (needs the user). Max 3 options (ADHD decision reduction). |
| Receiving review feedback | `superpowers:receiving-code-review` | — |
| Isolated feature work | `superpowers:using-git-worktrees` | Use `<repo>/.worktrees/` (gitignored). Never put sibling dirs outside the repo, because codex-rescue sandboxes reject them. |
| Finishing a branch | `superpowers:finishing-a-development-branch` | **PR route only.** Never take option 1 (local merge to `main`). AGENTS.md §4 requires PR plus proof, then `pr-steward` finality. |
| Parallel/subagent execution | `superpowers:dispatching-parallel-agents`, `superpowers:subagent-driven-development` | Stay inside AGENTS.md §5 evidence-economy budgets (L1 ≤ 1 implementer; L2/L3 = 1 implementer + 1 final auditor). Pin model/effort per dispatch. Record exceptions. |
| Self-review before merge | `superpowers:requesting-code-review`, built-in `/code-review` | Advisory only. Never the §9.1 embedded audit. |
| Second implementation/diagnosis pass, stuck | `codex:rescue` (agent `codex:codex-rescue`) | Worktree must be inside the repo. |
| Independent review of a diff | `/codex:review`, `/codex:adversarial-review` | **Advisory only. Codex is forbidden as a formal auditor** (AGENTS.md §9.1). |
| New or reshaped UI (React Ink dashboard, web UIs) | `frontend-design:frontend-design` | AdOps UI uses `adops-design` first. |
| GitHub Actions failure | `superdevflow:gha` | Then `ci-remediation-specialist` for the fix runbook. |
| Context handoff to a new session | `superdevflow:handoff` | Also persist via `/save` / ConPort. A handoff file is not canonical memory. |
| CLAUDE.md audit / capture session learnings | `claude-md-management:revise-claude-md`, `superdevflow:review-claudemd` | Manual only. Keep AGENTS.md §10 three-file sync. |

### Python LSP (`pyright-lsp`)

Gives the `LSP` tool (hover, definition, references, diagnostics) for `.py`/`.pyi` through `pyright-langserver --stdio`. The plugin's config lives in the official marketplace entry (`strict: false`), so its cache dir correctly has no `plugin.json`. The server binary is a per-machine install: `uv tool install 'pyright[nodejs]'` (bundles Node; verified pyright 1.1.414 on 2026-10-02). Pyright auto-detects `<repo>/.venv` for third-party imports, so no `pyrightconfig.json` is needed.

Division of labor: use the `LSP` tool for fast type/hover/diagnostic checks after editing Python. Serena stays the authority for semantic navigation, symbol-level edits, and project memories (CLAUDE.md Authority Routing). Pre-existing pyright noise: `native_hooks.py` imports hook modules via a runtime `sys.path` change, which pyright reports as unresolved imports. Do not "fix" those as part of unrelated work.

Codex stop-review gate (`/codex:setup`) is **off** for this repo (observed `stopReviewGate: false`). Leave it off: it adds a Stop hook with a 900 s timeout that runs next to the project's `native_hooks.py` Stop save, and Codex review cannot satisfy finality anyway.

### Subagent preload

Subagents with a narrow `tools:` list (no `Skill`) cannot invoke skills dynamically. Frontmatter `skills:` injects the **full** skill text at spawn. Plugin-scoped names such as `superpowers:verification-before-completion` were verified to load on 2026-10-02. Every preload costs tokens on every spawn, so preload only small skills that apply to every dispatch of that agent (see `.claude/agents/_index.md`).

## Disabled for this project (`enabledPlugins: false`)

| Plugin | Verdict | Reason |
|---|---|---|
| `claude-mem@thedotmack` | **Uninstalled 2026-10-02** | Adds a 4th memory store plus an MCP server, with hooks on 7 lifecycle events. Violates the Memory Trinity ADR (ConPort / dope-memory / dope-context are the only canonical planes). Its worker daemon was stopped, `~/.claude-mem` (794 MB) was deleted, and the `thedotmack` marketplace was removed. |
| `caveman@caveman`, `ck@cavekit-marketplace` | **Uninstalled 2026-10-02** | Compressed "caveman" output conflicts with the required final response shape and ADHD gentle guidance. `ck`'s single `SPEC.md` loop also duplicates the Task Packet system. |
| `hookify@claude-plugins-official` | **Uninstalled 2026-10-02** | Registers its own hooks on 4 events, bypassing the single `native_hooks.py` dispatcher. Hooks are contract-sensitive surfaces. |
| `feature-dev@claude-plugins-official` | **Uninstalled 2026-10-02** | Its explorer/architect/reviewer agents duplicate the curated `.claude/agents/` set and push dispatch counts past §5 budgets. |
| `code-review@claude-plugins-official` | Leave disabled | Overlaps the built-in `/code-review` skill, which is what's live. Behavior if both share the name is `UNKNOWN` (untested). |
| `commit-commands@claude-plugins-official` | Leave disabled | `/commit-push-pr` pushes and opens PRs without the proof bundle or `pr-steward` gates. |
| `claude-code-setup@claude-plugins-official` | Disabled | One-shot automation recommender. Enable briefly in `settings.local.json` if wanted. |

`andrej-karpathy-skills` (audited 2026-10-02) is **enabled**: one 2.5 KB MIT skill with no hooks, MCP servers, or scripts. Its 4 rules (surface assumptions, simplicity, surgical changes, verifiable goals) restate governance doctrine. It replaced `superpowers:test-driven-development` (9.6 KB) as a `developer` preload. On the main thread, `superpowers:test-driven-development` still applies.

`hookify` and `feature-dev` stay `false` in `enabledPlugins` as a guard against a later user-wide reinstall. The `caveman`, `cavekit-marketplace`, and `thedotmack` marketplaces were removed, which also dropped their `enabledPlugins` entries.

### claude.ai-synced plugins (`<name>@synced`)

These load in every session unless disabled. A per-plugin `"<name>@synced": false` in `enabledPlugins` works (verified 2026-10-02 via `claude plugin list`). `syncClaudeAiPlugins: false` in `settings.local.json` would hide all of them.

| Plugin | Verdict | Reason |
|---|---|---|
| `superdevflow` | **Enabled** | GHA debugging + context handoff + CLAUDE.md review. Small, fits CI and ADHD handoff needs. |
| `crewmarshal` | **Disabled** | Runs `python3` hooks on every Bash, Edit, and Stop. Its executor-dispatch discipline duplicates AGENTS.md §5. |
| `ux-superpowers` | **Disabled** | SessionStart prompt hook pushes UX-discovery docs; not this repo's workflow. |
| `engineering` | **Disabled** | Duplicates superpowers, built-in `/code-review`, and the project agents. Bundles 10 SaaS MCP connectors. |
| `ultrapowers-dev` | **Disabled** | Dozens of multi-language skills (Angular, C#, Dart, …) crowd the skill-listing budget. |
| `desktop-commander` | **Disabled** | Native tools cover it. The fleet's `desktop-commander` MCP singleton is separate and unaffected. |
| `design`, `design-superpowers` | **Disabled** | `frontend-design` + `adops-design` cover UI work. |
| `brand-voice`, `searchfit-seo`, `product-management`, `airtable`, `supericons`, `cowork-plugin-management` | **Disabled** | Marketing, PM-SaaS, and plugin-authoring scope. PM truth here is Leantime/ConPort. |

## Changing enablement

Edit `.claude/settings.json` `enabledPlugins` through the `update-config` skill (settings carry hooks, which are contract-sensitive), then confirm with `claude plugin list`. Update this card in the same change. Personal overrides go in `.claude/settings.local.json`. Uninstalling a plugin (`claude plugin uninstall`) is user-scope and affects every project.

Supply chain: marketplace sources are registered without a ref pin. The exact plugin version each machine runs is whatever `~/.claude/plugins/installed_plugins.json` records (`version` / `gitCommitSha`), outside this repo. `skills:` preloads inject third-party skill text into the `developer` subagent, which has Bash/Edit/Write, so re-read a preloaded skill after a plugin update before keeping the preload.
