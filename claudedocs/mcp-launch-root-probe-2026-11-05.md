---
id: mcp-launch-root-probe-2026-11-05
title: MCP launcher root-resolution probe (Task 3c, Step 1)
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-11-05'
last_review: '2026-11-05'
next_review: '2026-12-05'
status: MEASURED on this host 2026-11-05 (Claude Code 2.1.318, codex-cli 0.162.0-alpha.20); Codex and interactive EnterWorktree cases NOT_RUN
prelude: Records the working directory each runner gives a stdio MCP child, measured with a probe entry before `dopemux mcp launch` was built. Design D2 of claudedocs/mcp-just-works-design-2026-11-05.md requires this measurement; the launcher resolves its checkout from that directory.
---
# ━━━◆ Ø ◆━━━

# MCP launcher root-resolution probe

## Why

`.mcp.json` is tracked and identical in every checkout, so a launcher entry cannot carry a per-worktree `--root`. `dopemux mcp launch <server>` resolves its checkout from the process working directory (git top-level of it). This probe measures that directory per runner and per checkout kind before the launcher relies on it.

## Method

- Scratch repo: `git clone --local` of the `feat/mcp-just-works-m1` worktree into the session scratchpad (outside every real checkout), with one probe server committed as the scratch repo's `.mcp.json` and written to a separate `probe.json`:

  ```json
  {"mcpServers":{"probe":{"type":"stdio","command":"sh","args":["-c","printf 'cwd=%s\\nproject=%s\\n' \"$PWD\" \"${CLAUDE_PROJECT_DIR:-}\" >> \"$HOME/.dopemux/launch-probe.log\"; cat >/dev/null"]}}}
  ```

- Linked worktree: `git worktree add <scratch>/repo-wt -b probe-wt-branch`.
- Claude Code: `MCP_TIMEOUT=8000 timeout 120 claude -p --mcp-config probe.json --strict-mcp-config --setting-sources user --tools "" --model haiku "reply with the single word ok"`. `--setting-sources user` keeps the scratch repo's project hooks from running. The log was cleared before each case and read after it.
- Codex: the same probe as `[mcp_servers.probe]` in the scratch repo's project `.codex/config.toml`, run with `timeout 120 codex exec --ephemeral --ignore-user-config -s read-only -c 'projects."<scratch>".trust_level="trusted"' "reply with the single word ok"`.

## Results

| # | Runner | Session started in | Probe `cwd` | `CLAUDE_PROJECT_DIR` in server env | Result |
|---|---|---|---|---|---|
| 1 | Claude Code `-p` | scratch main checkout `<scratch>/repo` | `<scratch>/repo` | empty | RUN: cwd = session checkout |
| 1b | Claude Code `-p`, project `.mcp.json` only (no `--mcp-config`) | `<scratch>/repo` | none (probe not started) | n/a | RUN: project-scope servers are not started headless without approval |
| 2 | Claude Code `-p` | `git worktree add` linked worktree `<scratch>/repo-wt` | `<scratch>/repo-wt` | empty | RUN: cwd = session checkout |
| 2b | Claude Code `-p` | subdirectory `<scratch>/repo-wt/sub/dir` | `<scratch>/repo-wt/sub/dir` | empty | RUN: cwd = session directory, not the top-level |
| 3 | Claude Code `-p --worktree probe-wt` | `<scratch>/repo` (Claude-made worktree) | `<scratch>/repo/.claude/worktrees/probe-wt` | empty | RUN: cwd = the Claude-made worktree |
| 4 | Claude Code interactive `EnterWorktree` mid-session | n/a | n/a | n/a | NOT_RUN: interactive tool, cannot be driven headless |
| 5 | Codex `codex exec` (main checkout and linked worktree) | `<scratch>/repo` | none (probe not started) | n/a | NOT_RUN: the project `.codex/config.toml` was not loaded (header showed `approval: never`, not the project's `on-request`; probe log empty), so Codex could not be pointed at a project-level MCP config; the linked-worktree run was not attempted |

`<scratch>` is `/private/tmp/claude-501/-Users-hue-code-dopemux-mvp/a905a5d7-d220-4b74-9092-015deba24b0b/scratchpad/probe`.

## Conclusions

- In every case that ran, Claude Code starts a stdio MCP child in the session's working directory: the main checkout, a git-made linked worktree, or a Claude-made worktree. The launcher's root rule (git top-level of the process cwd) therefore resolves the session checkout for Claude Code.
- A session started in a subdirectory gives the child that subdirectory, so the launcher must take the git top-level, never the raw cwd (pinned by `test_resolve_launch_root_from_subdirectory`).
- Claude Code does not set `CLAUDE_PROJECT_DIR` in a stdio MCP server's environment, so the D2 fallback `--root ${CLAUDE_PROJECT_DIR:-.}` would expand to `.` and add nothing. No `--root` argument is added to the Task 3a renderer.
- Project-scope `.mcp.json` servers need the usual one-time approval before Claude Code starts them; headless `-p` runs without approval do not start them.
- Codex and the mid-session `EnterWorktree` case remain unmeasured (D11 still applies: entering a worktree mid-session keeps the original checkout's launchers until `/mcp reconnect`).
