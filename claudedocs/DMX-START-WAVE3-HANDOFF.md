# DMX-START Wave 3 — Session Handoff

**For:** a fresh thread continuing the `dopemux start` audit-and-fix program.
**Date:** 2026-06-09 · **Branch:** `claude/modest-cartwright-340c04` · **HEAD:** `7d87dfd93`
**Worktree:** `/Users/hue/code/dopemux-mvp/.claude/worktrees/modest-cartwright-340c04`

> **Orchestrator tracking:** this program is now also loaded in the task-orchestrator —
> root `400344c8` ("DMX-START-WAVE3: remaining work") with one child per remaining task.
> 3C-4 = `3738e834` (terminal/done). Each child's completion gate is a `proof-bundle`
> review note. Use the `/dx:*` skills (`/dx:tree 400344c8`, `/dx:next`, `/dx:start`,
> `/dx:complete`) to drive it, or just follow §4 below.

---

## 1. What this branch is
An in-flight **DMX-START** program: audit `dopemux start` (`src/dopemux/cli.py`), fix bugs, polish UI, add tests, and add a Codex/Copilot launcher seam. Prior waves (committed before this session) already shipped: CRIT C1–C3, NEW-C4, dup-fn removal, Wave 1 (loopback bind, dead code, except blocks), Wave 2 (`--altp` config_data). The committed audit `claudedocs/dopemux-start-audit-2026-06-06.md` describes the **PRE-FIX baseline** (most gaps it lists are already fixed — do NOT re-fix; verify against current code).

**Approved + PAL-validated plan:** `/Users/hue/.claude/plans/ok-i-need-to-mossy-twilight.md` (read it — it has the full track breakdown + advisor/PAL refinements).

## 2. Work done (commits are LOCAL ONLY, NOT pushed)
| # | SHA | What | Verify |
|---|---|---|---|
| 3A-1 | `3aae09746` | `setup_project_config` accepts `role=`; `--role X` no longer `TypeError`s; doctrine `.claude/CLAUDE.md` preserved (no clobber) | `tests/integration/test_start_wave3.py` |
| 3B-1 | `01df70de7` | GAP-H7 caplog test (H1–H7 + warning already shipped by Wave 1 — confirmed via git blame) | `test_start_crit_gaps.py` |
| 3C-1 | `11754e017` | Fix `gremlin.pink` (undefined in default `mint-mojo` → `[error]` in console.py/ui-logging/ui-errors); dangerous-mode `Panel`→`styled_panel` + theme tokens | brand_lint + dangerous-mode tests |
| 3C-2 | `b29888faa` | `_start_mcp_servers_with_progress`: `style="red"`→`error`, emoji→`Glyphs.SKIPPED/ERROR/SUCCESS` | `test_cli_mcp_startup.py` |
| 3C-3 | `5cb020a6f` | `worktree_recovery.py` menu + `worktrees_commands.py` switch guidance → themed console (markup=False on user/literal-bracket text; left stderr/data-capture/interactive plain) | `test_startup_integration.py` |
| 3C-4 | `7d87dfd93` | `routing_cli.py`: ~106 display `click.echo`→`console.print` (markup=False on interpolated f-strings); preserved 3 json.dumps + 21 `err=True` + 2 docker snippet bodies (26 plain echos) | `pytest -k routing` (38 pass) + brand_lint |

(Plus 2 handoff-doc commits `8eb801c08`, `ebfc75800` and proof-seal `f9db43a8f`.)

Working tree clean except `.claude/claude_config.json` (tool-managed by a hook — NOT ours; never stage it). `cli.py` is **6326 lines** (3C-1 removed a dead `from rich.panel import Panel`); routing_cli.py is **587 lines**.

## 3. CRITICAL gotchas (read before doing anything)
1. **Subagents read the WRONG checkout.** Subagents resolve *relative* paths against the MAIN repo (`/Users/hue/code/dopemux-mvp`, often a different branch), NOT this worktree. The entire original audit was contaminated this way. **Every subagent prompt MUST**: `cd` to the absolute worktree path first, use absolute paths, and self-check `wc -l src/dopemux/cli.py == 6326` (STOP if it reports ~6414 = wrong checkout). See memory `feedback-subagent-worktree-path-resolution`.
2. **Network is OFFLINE.** `git fetch`/push/`gh`/docker/live Claude+Codex launch all fail. The 5 commits are LOCAL ONLY. PR #842 (open, →main) still shows the pre-Wave-3 state. Push/PR deferred to network + explicit user go-ahead.
3. **Concurrent branch activity.** The branch is externally managed (main merges, proof-seal commits push to `origin/claude/...`). `git fetch` + `git status` before EVERY commit; if behind, fast-forward (it's been strict-ancestor so far). Re-check when network returns.
4. **Model tiering** (memory `feedback-model-routing-policy`): Opus supervises; **Sonnet implements**; Haiku mechanical.
5. **brand_lint gate**: run `python scripts/brand_lint.py` after every UI change — enforces the danger-hue invariant (`error`/`chip.blocker`/`severity.critical` must be red-family) + palette purity (no raw `#hex` outside approved files). All 5 commits keep it 0/0.
6. **Don't clobber doctrine.** `configurator._create_claude_md` overwrites `.claude/claude.md` (== `.claude/CLAUDE.md` on case-insensitive macOS). 3A-1 guards the `--role` path; 3A-2 persona injection must preserve doctrine (separate file + idempotent `@import`, OR launcher injection).
7. **`click.confirm` vs `dopemux_confirm`**: dangerous-mode tests patch `dopemux.cli.click.confirm`; `dopemux_confirm` uses `rich.prompt.Confirm` (won't be intercepted). Don't switch confirms without updating test patches.
8. **Implementer subagents jump the orchestrator gate.** On 3C-4 the Sonnet subagent advanced its orchestrator item to `terminal` and wrote a proof-bundle note **before any commit existed**, and recorded the WRONG branch in that note. Opus had to independently re-verify, commit, and rewrite the proof note. **Supervisor keeps the gate:** the subagent implements + verifies + reports a diff ONLY; Opus reviews the diff, commits (staging only the work file), and writes/repairs the proof-bundle note with the real commit SHA. Tell the subagent explicitly: do NOT touch git, do NOT advance orchestrator items.

## 4. Remaining Wave 3 (priority order; user chose to finish 3C next)
- **3C-4 — `routing_cli.py`** ✅ **DONE** (`7d87dfd93`, orchestrator `3738e834` terminal). ~106 display echos themed; 26 plain preserved; brand_lint 0/0; 38 routing tests green.
- **3C-5 — SEV-3:** **(NEXT — offline-doable, unblocked by 3C-4; orchestrator `a7c36ef2`)** 8 unthemed `Console()` (`adhd/attention_monitor.py:19`, `adhd/context_manager.py:21`, `adhd/task_decomposer.py:22`, `update/health.py:37`, `update/rollback.py:36`, `update/manager.py:86`, `claude_tools/session_manager.py:56`, `startup_hints.py:406` test-only) → shared themed console; **`Glyphs._FALLBACK`** runtime application (Nerd-Font detection — currently dead; important because 3C-1/2/3 added `Glyphs.*` that garble on plain terminals); `splash.py` hardcoded hex; extend `brand_lint` to guard start-path files. Offline-doable.
- **3E — launcher seam + Codex** (offline-doable): extract `AgentRuntimeLauncher` Protocol; **add env-invariant canary tests FIRST** (esp. `ANTHROPIC_API_KEY` *removal* in legacy proxy mode, `launcher.py:~394-402`; and `__init__` signal/`atexit` side-effects → lazy-init) before refactoring `ClaudeLauncher` (keep the 26 shape-coupled `tests/test_claude_launcher.py` green — same `mcpServers` JSON shape + flags); `get_runtime_launcher` factory + `--runtime claude|codex|copilot` (default claude), replace call sites `cli.py:577` + `cli.py:2452`; `CodexLauncher` emits `~/.codex/config.toml` `[mcp_servers]` from runtime-neutral `config.mcp_servers`. Copilot = design doc only (`mcp-proxy-config.copilot.yaml` already matches shape). Quick win: delete unreachable `logger.error` after `raise` in `_create_settings_file`.
- **3A-2 — persona injection** (BLOCKED OFFLINE): spike first — does Claude Code honor `@import` in `.claude/CLAUDE.md` + pick up pre-launch edits? If not, inject via launcher `--settings` (then 3A-2 depends on 3E). Wire `InstructionManager.assemble_instructions(role, template)` (currently dead). Guard `_create_claude_md` from regenerating doctrine.
- **3D — MCP robustness + full-stack e2e** (BLOCKED OFFLINE): healthcheck honesty (`pal` `exit 0`, `dope-context` `||exit 0`, `qdrant` none → real probes or rely on `DiscoveryGate`); `.env.example` add `EXA_API_KEY`/`OPENAI_WEBHOOK_SECRET`/`MYSQL_ROOT_PASSWORD`; `tests/e2e/` **tools-first, two-tier** (no-secrets smoke + secrets-required), explicit skip summary, runtime-agnostic probes.
- **3B-2 — M-series tests** (optional, low value): M1 `--no-recovery`, M3 dangerous-expiry, M5 env-export, M7 `FORCE_INSTANCE_ID`, M8 `--session`, M9 `SKIP_MCP_AUTOCONFIG` — untested-but-correct branches.
- **Deferred (NOT Wave 3):** task-orchestrator stdio→HTTP transport migration (contract-sensitive); role attention-state realness → ADHD remediation program (`DOPEMUX_ROLE_ATTENTION_STATE` has no consumer; `AttentionMonitor` uses hardcoded thresholds).

## 5. Pre-existing issues noticed (out of scope, flag-only)
- `worktrees_commands.py:133` — `"." + Optional[str]` (latent crash if None). `worktree_recovery.py:254` — return-type mismatch. `cli.py` — `extraction_pipeline` import unresolved (4298/4515), `Console.logger` Pyright noise (the `_ConsoleAdapter` pattern), `stderr` param (687). Don't fix as part of UI polish.

## 6. Resume verification (run these to confirm green base)
```bash
cd /Users/hue/code/dopemux-mvp/.claude/worktrees/modest-cartwright-340c04
wc -l src/dopemux/cli.py                    # MUST be 6326 (else wrong checkout — STOP)
git log --oneline 6632772aa..HEAD          # expect 3C-1..3C-4 + 3A-1/3B-1 + handoff/proof commits; HEAD 7d87dfd93
python -m pytest tests/integration/test_start_crit_gaps.py tests/integration/test_start_command.py tests/integration/test_start_wave3.py -q
python -m pytest tests/ --ignore=tests/e2e -k routing -q    # 3C-4: expect 38 passed
python scripts/brand_lint.py               # expect 0 errors / 0 warnings
python -c "import sys; sys.path.insert(0,'src'); from dopemux import cli; print('ok')"
```
Each Sonnet implementation increment: failing-test-first where there's a code change; brand_lint after UI changes; commit per increment with `(DMX-START Wave 3, <id>)` in the message; do NOT push.
