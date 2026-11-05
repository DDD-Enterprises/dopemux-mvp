# W10 return — TP-DMX-RUNNERMEM2A-R2-W10-SCOPE-EXTENSION-001

**Child status:** READY_FOR_AUDIT after one correction round. **Team lead disposition:** committed as `9e1b3df38` after a diff re-read and one ruling. Audit: NOT_RUN (held for J04-FREEZE). Authority: `AMENDMENT_01.md` (operator: "Yes, extend 2A").

## Route and counters

| Field | Value |
|---|---|
| Binding | `W10_EXECUTION_BINDING.json`, `ct validate-binding` PASS |
| Requested route | claude-code-agent, `claude-sonnet-5-5`, effort UNKNOWN |
| Observed model | `claude-sonnet-5-5` on all 119 assistant turns, both rounds (harness record) |
| First round | 333 s / 140,638 tokens / 67 tool uses |
| Correction round | 97 s / 160,092 tokens / 16 tool uses (as reported by the completion notice) |
| Caps | 60 min / 600,000 tokens / 150 tool uses |
| Attempts | 1 attempt plus the 1 allowed correction round |
| advisor calls / subagents | 0 / 0 (structural count: Bash 23, Read 12, Write 2, Edit 44, SubagentHandback 2) |
| `cd` / edits through Bash | 0 / 0 |

## Team-lead ruling: lowercase companions rejected

The first round also exempted the lowercase spellings `dockerfile` and `dockerfile.dope-memory`. The reason: Claude Code's guard checks the lowercase reading of every path (`dcp_surface_guard.py:104-113`), so a capitalized exempt name never passes it.

PR Steward's gate (`security_release_gate.py:72-73`) and the scanner (`red_lane_scanner.py:83-84`) match the rules case-sensitively. With the companions, a lowercase path in those two directories would also pass the PR gate on a case-sensitive system. The operator authorized exactly two paths, so the companions were removed in the correction round.

The result:
- The regex layer exempts exactly the two Dockerfiles.
- The guard still blocks Claude Code's Edit-tool edits to them. That fails closed and is accepted. A later guard change resolves it.
- ADR-227 Amendment 1 records this.

## Write surface

9 paths, all inside the W10 write_surface. The Dockerfile diffs are exactly +1 line each:
- `Dockerfile.dope-memory:48`: `COPY services/working-memory-assistant/auth_identity.py .`
- ConPort `Dockerfile:32`: `COPY docker/mcp-servers-source/conport/auth_identity.py .`

The order was rules file first, then the Dockerfiles (C12).

## Validation (team lead re-ran)

| Command | Exit | Bucket |
|---|---|---|
| commit.verify pytest line (W10, W09, guard, integration test) | 0 | PASS: 281 passed |
| W01, W02, W06, W09, W10, guard, ConPort wiring, hooks, capture, CLI capture, both integration ledger suites, dope-memory endpoint, MCP lifecycle (services venv) | 0 | PASS: 734 passed |
| every test referencing the red-lane rules, scanner or PR gate (`tests/dcp/`, `tests/pr_steward/`, `tests/contracts/`) | 0 | PASS: 414 passed |
| `tests/pr_steward` alone | 0 | PASS: 341 passed |
| `git diff --check`, pre-commit (`SKIP=markdownlint`) | 0 | PASS (markdownlint NOT_RUN) |
| TDD failing-first (child) | 1 | recorded: static test 2 failed before the COPY lines; rules tests 9 failed before the rules edit; integration test failed on the column count before the fix |
| Image build or start | — | NOT_RUN (C10, B05); the static COPY-versus-import test is the only evidence |

## What the static test checks

Each image copies every local module its entry files import, and nothing else is missing:
- dope-memory: `auth_identity`, `canonical_ledger`, `eventbus_consumer`, `mcp_http`, `postgres_mirror_sync`
- ConPort: `auth_identity`, `instance_detector`, `integration_bridge_client`, `unified_queries`

Package directories (`chronicle/` and so on) are out of its scope.

## Open items closed by W10

- `W02_RETURN.md` open item 1 (neither image would start): closed statically; a live build is NOT_RUN.
- `W06_RETURN.md` open item 1 (CI integration test): closed.
