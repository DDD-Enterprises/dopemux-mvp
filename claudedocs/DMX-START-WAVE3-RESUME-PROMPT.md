# DMX-START Wave 3 — Resume Prompt (paste into the new thread)

> Copy everything in the fenced block below into a fresh thread to continue the remaining work.

```
You are continuing the DMX-START Wave 3 program (auditing/fixing/polishing `dopemux start`).

== ORIENT FIRST (read these, in order) ==
Worktree (your cwd for everything): /Users/hue/code/dopemux-mvp/.claude/worktrees/modest-cartwright-340c04
Branch: claude/modest-cartwright-340c04   HEAD should be 7d87dfd93 (3C-4 committed; all local, unpushed)
Orchestrator: root 400344c8; remaining children are queue items. 3C-4 (3738e834) = done/terminal.
1. claudedocs/DMX-START-WAVE3-HANDOFF.md   <- full state, gotchas, commit log
2. /Users/hue/.claude/plans/ok-i-need-to-mossy-twilight.md   <- approved + PAL-validated plan (per-track detail)
3. claudedocs/dopemux-start-audit-2026-06-06.md   <- the PRE-FIX baseline audit (most gaps already fixed; do NOT re-fix)

== HARD RULES ==
- Model tiering: Opus supervises (decompose/review/gate); Sonnet implements; Haiku mechanical. Delegate bulk work.
- SUPERVISOR KEEPS THE GIT + ORCHESTRATOR GATE: implementer subagents IMPLEMENT + VERIFY + return a diff ONLY. They must NOT touch git, must NOT commit, and must NOT advance/complete orchestrator items. (On 3C-4 the subagent advanced its item to terminal + wrote a proof note with the WRONG branch before any commit existed — Opus had to re-verify, commit, and repair the note.) Opus reviews the diff, commits (staging ONLY the work file), and writes/repairs the proof-bundle note with the real commit SHA.
- SUBAGENT PATH DISCIPLINE (non-negotiable): every subagent prompt must `cd` to the absolute worktree path above, use absolute paths, and self-check `wc -l src/dopemux/cli.py` == 6326. If it reports ~6414, it is in the WRONG checkout (the main repo, a different branch) — STOP. The whole original audit was contaminated by this.
- Failing-test-first for any code change (red -> green; mutation-check by reverting). brand_lint after every UI change: `python scripts/brand_lint.py` must stay 0 errors / 0 warnings (it enforces danger-hue invariant + palette purity).
- Commit per increment with `(DMX-START Wave 3, <id>)` in the message + the standard Co-Authored-By footer. Stage ONLY your files — NEVER stage `.claude/claude_config.json` (a hook keeps rewriting it).
- `git fetch` + `git status` before every commit (branch is externally managed). DO NOT push or open/modify PRs (network may be offline; PR #842 stays as-is) unless the user explicitly says so.
- Governance: minimal change; OBSERVED vs INFERRED; report PASS/FAIL/NOT_RUN honestly.

== VERIFY THE BASE (run before starting) ==
cd /Users/hue/code/dopemux-mvp/.claude/worktrees/modest-cartwright-340c04
wc -l src/dopemux/cli.py            # MUST be 6326 (else wrong checkout — STOP)
git log --oneline 6632772aa..HEAD   # expect: 3C-4 (7d87dfd93) + handoff + 3C-3 3C-2 3C-1 3B-1 3A-1
python -m pytest tests/integration/test_start_crit_gaps.py tests/integration/test_start_command.py tests/integration/test_start_wave3.py -q
python -m pytest tests/ --ignore=tests/e2e -k routing -q   # 3C-4 guard: expect 38 passed
python scripts/brand_lint.py
python -c "import sys; sys.path.insert(0,'src'); from dopemux import cli; print('ok')"

== REMAINING WORK (do in this order; one Sonnet increment at a time, commit each) ==

3C-4  routing_cli.py UI theming  [DONE — commit 7d87dfd93, orchestrator 3738e834 terminal]
  ~106 display `click.echo`→`console.print` (markup=False on interpolated f-strings); preserved 3
  json.dumps + 21 err=True + 2 docker snippet bodies. brand_lint 0/0; 38 routing tests green. Skip.

3C-5  SEV-3 cleanup  [OFFLINE-OK — DO THIS FIRST]
  (a) Route the 8 unthemed `Console()` to the shared themed console: adhd/attention_monitor.py:19,
      adhd/context_manager.py:21, adhd/task_decomposer.py:22, update/health.py:37, update/rollback.py:36,
      update/manager.py:86, claude_tools/session_manager.py:56, startup_hints.py:406 (test-only).
  (b) Apply Glyphs._FALLBACK at runtime (Nerd-Font/terminal capability detection) so Glyphs.* degrade to
      ASCII on plain terminals — important because 3C-1/2/3 added Glyphs.* that garble without it. Keep it
      simple (e.g. tie to PLAIN render mode + an env override); add a unit test.
  (c) splash.py hardcoded hex -> approved-file pattern or theme tokens.
  (d) Extend scripts/brand_lint.py to guard start-path files against new raw print/echo/Console()/hex.
  Verify: brand_lint 0/0; relevant unit tests; import ok.

3E  Multi-runtime launcher seam (Claude + Codex; Copilot design-only)  [OFFLINE-OK except live launch]
  - FIRST add env-invariant canary tests for ClaudeLauncher (the 26 tests in tests/test_claude_launcher.py
    are shape-coupled and miss these): assert ANTHROPIC_API_KEY *removal* in legacy proxy mode
    (launcher.py ~394-402), and that __init__ signal/atexit registration doesn't multiply when a factory
    builds launchers in more contexts (lazy-init or move behind launch()).
  - Extract `AgentRuntimeLauncher` Protocol (is_available/launch/get_status) in src/dopemux/claude/runtime_protocol.py;
    refactor ClaudeLauncher to satisfy it WITHOUT changing the concrete mcpServers JSON shape or CLI flags
    (keep all 26 launcher tests green). Single Claude-locked translation point = _generate_claude_config +
    _create_settings_file (launcher.py ~225-304); everything upstream (roles/catalog activate_role,
    config/manager _generate_server_config/_get_default_mcp_servers, MCPRegistry) is runtime-neutral.
  - Add get_runtime_launcher(runtime, config_manager) factory + `--runtime claude|codex|copilot` flag
    (default claude); replace call sites cli.py:577 and cli.py:2452.
  - CodexLauncher: discover `codex` binary; emit ~/.codex/config.toml [mcp_servers] from config.mcp_servers;
    OPENAI_API_KEY/CODEX_API_KEY env. (Live `codex` launch verification deferred until network returns.)
  - Copilot: design doc only (mcp-proxy-config.copilot.yaml already matches the mcpServers shape).
  - Quick win: delete the unreachable `logger.error` after `raise` in _create_settings_file.
  Verify: factory selection; Codex TOML emit unit test; test_claude_launcher.py green; brand_lint 0/0.

3A-2  Persona injection  [BLOCKED until network — needs a live Claude launch to verify the contract]
  Spike: does Claude Code honor `@import` inside .claude/CLAUDE.md and pick up edits made just before launch?
  If yes -> write persona to .claude/active-role.md + idempotent `@import` below a `<!-- DOPEMUX-ROLE -->`
  marker. If no -> inject via the launcher --settings hook (then this depends on 3E). Wire the currently-dead
  InstructionManager.assemble_instructions(role, template). Guard _create_claude_md from regenerating doctrine.
  Tests must prove the persona reaches the EFFECTIVE instruction source; doctrine .claude/CLAUDE.md untouched.

3D  MCP-startup robustness + full-stack e2e  [BLOCKED until network/docker]
  Healthcheck honesty (compose.yml: pal `exit 0`, dope-context `||exit 0`, qdrant none -> real probes or rely
  on DiscoveryGate's tools/list). .env.example: add EXA_API_KEY, OPENAI_WEBHOOK_SECRET, MYSQL_ROOT_PASSWORD.
  tests/e2e/ TOOLS-FIRST (not healthcheck-first), TWO-TIER (no-secrets smoke + secrets-required full),
  explicit skipped-capability summary, runtime-agnostic probes. New `e2e` marker; `-m "not e2e"` default.

3B-2  M-series contract tests  [OFFLINE-OK, OPTIONAL/low-value]
  Deterministic tests for untested-but-correct branches: M1 --no-recovery, M3 dangerous expiry, M5
  _persist_instance_env_exports, M7 DOPEMUX_FORCE_INSTANCE_ID, M8 --session vs restore_latest, M9
  DOPEMUX_SKIP_MCP_AUTOCONFIG. Behavior-based assertions (not line/identity).

DEFERRED (NOT Wave 3): task-orchestrator stdio->HTTP transport migration (contract-sensitive, separate TP);
role attention-state realness (-> ADHD remediation program; DOPEMUX_ROLE_ATTENTION_STATE has no consumer).

== KNOWN PRE-EXISTING SMELLS (out of scope; flag, don't fix during polish) ==
worktrees_commands.py:133 ("." + Optional[str], latent None crash); worktree_recovery.py:254 return-type;
cli.py extraction_pipeline import (4298/4515), Console.logger Pyright noise, stderr param (687).

When network/docker return: re-run `git fetch`+status, then decide push/PR (extend PR #842 vs new Wave-3 PR)
WITH the user, and unblock 3A-2 + 3D.
```
