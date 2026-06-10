# TP-DCP-MCP-RO-0007 — Command Log

Docs-only packet (Secure MCP Tunnel integration docs + manual validation). No
source code changed; no tunnel client or connector run in CI.

## Environment

```
$ pwd
/Users/hue/code/dopemux-mvp/.claude/worktrees/musing-visvesvaraya-c837f0
$ git rev-parse --show-toplevel
/Users/hue/code/dopemux-mvp/.claude/worktrees/musing-visvesvaraya-c837f0
$ git branch --show-current
dcp/chatgpt-mcp-ro-0007-secure-mcp-tunnel-integration-do
$ git rev-parse HEAD   # base before commit
06f3344b6de092b03912799ac9bf153763cf8673
```

## S2 — packet validation

### Tests (structural baseline unchanged by docs)

```
$ python -m pytest -q services/dcp-readonly-facade/tests
... 108 passed, 1 skipped ...
SKIPPED [1] tests/test_live_optional.py:26: set DCP_FACADE_LIVE_TESTS=1 to run live tests
exit_code = 0
```

### Secret scan (commit.verify regex)

```
$ rg -n "CONTROL_PLANE_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|sk-|Bearer |TOKEN=|PASSWORD=|SECRET=|tunnel_[A-Za-z0-9]" \
    docs/03-reference/dcp/chatgpt-mcp-readonly services/dcp-readonly-facade
exit_code = 0   (matches present; ALL classified as false positives — see AUDIT.md §2)
```

Hit classification (no real secrets):

- **New files (this packet):**
  - `FAILURE_RUNBOOK.md:108` — the literal documented scan command (operators must
    run it). Contains the pattern by design; no value.
  - `MANUAL_VALIDATION.md:101,103` and `TUNNEL_INTEGRATION.md:34` — substring `sk-`
    inside the word "ta**sk-**orchestrator". Not a key.
- **Pre-existing files (not modified here):** `chatgpt_tunnel_suitability` →
  `tunnel_s` matches `tunnel_[A-Za-z0-9]`; "task-orchestrator" → `sk-`; redaction
  code/tests intentionally contain `sk-`/`Bearer ` regex literals.

No `CONTROL_PLANE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`,
`GEMINI_API_KEY`, real `sk-…` value, `Bearer <token>`, `TOKEN=`, `PASSWORD=`,
`SECRET=`, or real `tunnel_<id>` value appears in any new file.

### Diff scope

```
$ git add -A && git diff --cached --stat
 docs/03-reference/dcp/chatgpt-mcp-readonly/FAILURE_RUNBOOK.md    | 135 ++++
 docs/03-reference/dcp/chatgpt-mcp-readonly/MANUAL_VALIDATION.md  | 114 ++++
 docs/03-reference/dcp/chatgpt-mcp-readonly/TUNNEL_INTEGRATION.md | 182 ++++
 3 files changed, 431 insertions(+)
```

All changed paths are within `commit.allowlist`
(`docs/03-reference/dcp/chatgpt-mcp-readonly/**`, `proof/TP-DCP-MCP-RO-0007/**`).
No `services/**`, `src/**`, `.env*`, `.dopemux/**`, or `compose*.yml` touched.

```
$ git status --short --branch
## dcp/chatgpt-mcp-ro-0007-secure-mcp-tunnel-integration-do
```
