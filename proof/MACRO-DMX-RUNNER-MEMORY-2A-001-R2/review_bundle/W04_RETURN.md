# W04 return — TP-DMX-RUNNERMEM2A-R2-W04-STDIO-BRIDGE-001

**Child status:** READY_FOR_AUDIT after one correction round. **Team lead disposition:** committed as `7675468a7` after a diff re-read, two rulings and one correction. Audit: NOT_RUN (held for J04-FREEZE).

## Route and counters

| Field | Value |
|---|---|
| Binding | `W04_EXECUTION_BINDING.json`, `ct validate-binding` PASS |
| Requested route | claude-code-agent, `claude-sonnet-5-5`, effort UNKNOWN |
| Observed model | `claude-sonnet-5-5` on all 59 assistant turns of the first round (harness record) |
| First round | 528 s / 148,265 tokens / 40 tool uses |
| Correction round | 65 s / 156,240 tokens / 8 tool uses (as the completion notice reported them) |
| Caps | 90 min / 1.0M / 200 |
| advisor calls / subagents | 0 / 0 (structural count, first round: Bash 20, Read 3, Write 6, Edit 10, SubagentHandback 1) |
| `cd` / edits through Bash / live or keychain commands | 0 / 0 / 0 |

## Team-lead clarification given at dispatch

B01 says the bridge reads only `*_PORT` keys from `.envrc.dopemux-mcp`; B04 says the ids come from the envrc. The ruling: read `*_PORT` plus the four id keys, nothing else. The file also exports a database password.

The bridge reads even less: three keys per server, filtered by name before parsing.
- dope-memory: `DOPE_MEMORY_PORT`, `DOPE_MEMORY_WORKSPACE_ID`, `DOPE_MEMORY_INSTANCE_ID`
- ConPort: `CONPORT_MCP_PORT`, `DOPEMUX_WORKSPACE_ID`, `DOPEMUX_INSTANCE_ID`

The keys are generated at `lifecycle.py:1219-1233`, and `envrc.py:90-96` lists them as non-secret.

## Rulings on the return

1. **Ids filled on read tools: accepted.** B04 says "mutating calls only". The bridge fills any tool that declares the id, read tools included, but only when the caller omitted it, only with the caller's own repo identity, and it never overrides. That widens nothing and matches dope-memory's read default (the bound workspace). Recorded for the audit.
2. **Correction: the forwarded `tools/list` no longer marks filled ids as required.** Before it, a model told `workspace_id` was required would invent a value; the server rejects a mismatched workspace, and the bridge never fills a supplied value. Now only the copy printed to the client changes; the bridge's own schema knowledge is untouched, and an id the envrc lacks stays required. This closes W01 residual 1 for runners on the bridge (Codex and Claude Code in 2A). Direct HTTP clients are unaffected.

## Validation (team lead re-ran)

| Command | Exit | Bucket |
|---|---|---|
| `pytest tests/unit/runner_memory_2a_r2_w04/` plus `tests/test_mcp_config_generation.py` and W03's tests | 0 | PASS: 111 passed (69 W04) |
| `git diff --check`, pre-commit (`SKIP=markdownlint`) | 0 | PASS (markdownlint NOT_RUN) |
| TDD failing-first (child, both rounds) | 1 | recorded: 25 failed and 37 errors before the code; 3 failed before the correction |
| Mutation checks (child) | 1 | id override, envrc boundary and a non-fatal 401 each broke tests; restored |
| Live servers, real keychain | — | NOT_RUN (C10) |

## What W07 must render

- Invocation: `<python> -m dopemux.mcp.http_stdio_bridge --server dope-memory|conport --principal <principal>`, with an optional `--timeout N`.
- The process must start inside the checkout: discovery walks up from `Path.cwd()` and has no `--workdir` option. Whether Codex starts stdio servers in the session's working directory is UNKNOWN, so W07 confirms it or sets the server's working directory explicitly.
- The legacy `--base-url` mode is unchanged. Its only runtime caller is `src/dopemux/config/manager.py:721`.

## Notes for the audit

- **Worktree boundary.** The envrc walk stops at the first directory that has its own `.git` (file or directory) and no envrc, so a worktree under `.worktrees/` never reads the main checkout's file (W00 design change 11).
- **Exit codes** (the child's choice; the packet did not set them): 2 for a startup failure, 3 for 401/403.
- **404 retry.** A 404 with a session id triggers one replay of the stored `initialize`; a second 404 is an error.
- **Token kept on 127.0.0.1.** Redirects are refused and environment proxies are ignored.
