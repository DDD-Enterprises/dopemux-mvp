# DMX-DCP-MODEL-ROUTING-MVP-0000 — COMMAND_HELP_LEDGER.md

## Dopemux CLI Commands

| Command | Exists? | Help captured? | Mutating? | Safe automation class | Evidence | Notes |
|---------|---------|----------------|-----------|-----------------------|----------|-------|
| dopemux --help | YES | YES | N/A | Read | uv run | 50+ commands listed |
| dopemux doctor | YES | Partial | Read | Diagnostic | uv run | Error: unpack (2,1) but surface captured |
| dopemux dcp | NO | N/A | N/A | N/A | uv run | No such command |
| dopemux kernel | YES | YES | Delegated | Subcommand tree | uv run | 8 lifecycle verbs under kernel |
| dopemux kernel doctor/compile/run/collect/gate/promote/feedback/loop | YES | YES | Mixed | Kernel lifecycle | uv run | All exist; mutating posture per verb |
| dopemux compile/run/collect/gate/promote/feedback/loop | NO | N/A | N/A | N/A | uv run | Only under kernel subcommand |
| dopemux mcp | YES | YES | Delegated | MCP management | uv run | 6 subcommands |
| dopemux routing | YES | YES | Delegated | Routing control | uv run | 9 subcommands |
| dopemux workflow | YES | YES | Delegated | Workflow orchestration | uv run | 7 subcommands |
| dopemux memory | YES | YES | Delegated | Memory capture/rollup | uv run | 2 subcommands |
| dopemux extractor | YES (legacy) | YES | N/A | Redirect | uv run | Redirects to rte |
| dopemux rte | YES | YES | Delegated | Repo Truth Extractor | uv run | Canonical entrypoint |

## Dopetask Wrapper Commands

| Command | Exists? | Help captured? | Mutating? | Safe automation class | Evidence | Notes |
|---------|---------|----------------|-----------|-----------------------|----------|-------|
| scripts/dopetask --help | YES | YES | N/A | Read | Direct | 20+ commands |
| scripts/dopetask doctor | YES | YES | Read | Diagnostic | Direct | PASSED (6/6) |
| scripts/dopetask compile-tasks | YES | YES | Read (compile) | TP scaffolding | Direct | --mode, --max-packets, --out |
| scripts/dopetask run-task | YES | YES | Write (workspace) | TP execution | Direct | --task-id required |
| scripts/dopetask collect-evidence | YES | YES | Read | Evidence harvest | Direct | --run required |
| scripts/dopetask gate-allowlist | YES | YES | Read | Compliance gate | Direct | --run, --diff-mode |
| scripts/dopetask promote-run | YES | YES | Write (token) | Promotion | Direct | --run required |
| scripts/dopetask commit-run | YES | YES | Write (git) | Commit (allowlist) | Direct | Enforces ALLOWLIST_DIFF.json |
| scripts/dopetask spec-feedback | YES | YES | Read | Feedback gen | Direct | --runs required |
| scripts/dopetask loop | YES | YES | Write | Full lifecycle | Direct | --loop-id, --mode |
| scripts/dopetask tp | YES | YES | Delegated | TP workflow | Direct | run/exec/git/series |
| scripts/dopetask tp series | YES | YES | Delegated | Series execution | Direct | exec/status/finalize |
| scripts/dopetask dopemux | YES | YES | Delegated | Dopemux-integrated | Direct | compile/run/collect/gate/promote/feedback |

**Total Commands Catalogued**: 26
**Mutating Commands Identified**: 8 (run-task, promote-run, commit-run, loop, tp run, tp series exec, tp series finalize, dopemux dopemux equivalents)
**Safe Automation Class Legend**: Read | Diagnostic | Compile | Execute (workspace) | Gate | Promote | Commit (allowlist) | Feedback | Loop
