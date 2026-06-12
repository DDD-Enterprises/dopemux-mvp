# TP-DCP-MCP-RO-0008 — Command Log

## Environment
```
$ git rev-parse --show-toplevel
/Users/hue/code/dopemux-mvp/.claude/worktrees/musing-visvesvaraya-c837f0
$ git branch --show-current
dcp/chatgpt-mcp-ro-0008-hardening-cross-project-isolatio
$ git rev-parse HEAD  # base before commit
a0f8cbb3d0d02090c2fefcf013de27b6b0bb6dfa
```

## S2 — validation

### Full facade suite
```
$ python -m pytest -q services/dcp-readonly-facade/tests
...........................................................              [100%]
=========================== short test summary info ============================
SKIPPED [1] services/dcp-readonly-facade/tests/test_live_optional.py:26: set DCP_FACADE_LIVE_TESTS=1 to run live tests
exit_code=0
```

### compileall
```
$ python -m compileall -q services/dcp-readonly-facade
exit_code=0
```

### No-write / hazard scan (src) — all hits classified benign in NO_WRITE_REVIEW.md
```
$ rg -n 'write_text|mkdir|unlink|rmtree|os.system|shell=True|.put(|.patch(|.delete(' services/dcp-readonly-facade/src
(no write/shell/mutating-verb hits)
```

### Secret scan (no real secrets)
```
$ rg -n 'OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|sk-|Bearer |TOKEN=|PASSWORD=|SECRET=' services/dcp-readonly-facade docs/03-reference/dcp/chatgpt-mcp-readonly
exit_code=0; verdict=NO_REAL_SECRETS
All matches are false positives: 'sk-' substring of 'task-orchestrator'; redaction.py + test_redaction.py + test_packet_0008.py contain the pattern literals by design (redaction regexes / denial-assertion test inputs). No real credential value present.
```

### Diff scope
```
$ git diff --cached --stat
 .../dcp/chatgpt-mcp-readonly/ARCHITECTURE.md       |   2 +-
 .../RESPONSE_ENVELOPE_SCHEMA.md                    |  26 ++
 .../dcp-readonly-facade/src/dcp_facade/envelope.py |  14 +-
 .../dcp-readonly-facade/src/dcp_facade/tools.py    |   4 +
 .../dcp-readonly-facade/tests/test_packet_0008.py  | 375 +++++++++++++++++++++
 5 files changed, 419 insertions(+), 2 deletions(-)
```
All paths within commit.allowlist (services/dcp-readonly-facade/**, docs/03-reference/dcp/chatgpt-mcp-readonly/**, proof/TP-DCP-MCP-RO-0008/**).
