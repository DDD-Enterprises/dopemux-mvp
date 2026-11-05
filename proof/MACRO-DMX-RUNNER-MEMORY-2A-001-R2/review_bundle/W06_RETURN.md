# W06 return — TP-DMX-RUNNERMEM2A-R2-W06-LOCAL-WRITERS-001

**Child status:** INCOMPLETE (its code was done; two tests outside its write surface failed). **Team lead disposition:** committed as `e9418771d` after one diff re-read and one correction (a dropped space in `capture_client.py`); W01 test follow-up `fe5e3db28`. One failing integration test is outside every write surface and goes to the operator. Audit: NOT_RUN.

## Route and counters

| Field | Value |
|---|---|
| Binding | `W06_EXECUTION_BINDING.json`, `ct validate-binding` PASS |
| Requested route | claude-code-agent, `claude-sonnet-5-5`, effort UNKNOWN |
| Observed model | `claude-sonnet-5-5` on all 68 assistant turns (harness record) |
| Duration / tokens / tool uses | 211 s / 124,338 / 49 (caps 60 min / 600k / 150) |
| Attempts | 1 |
| advisor calls / subagents | 0 / 0 (structural count: Bash 19, Read 10, Write 2, Edit 17, SubagentHandback 1) |
| `cd` / edits through Bash | 0 / 0 |

## Write surface

5 paths before commit, all inside the W06 write_surface. No red-lane path is in this workstream.

## Validation (team lead re-ran)

| Command | Exit | Bucket |
|---|---|---|
| commit.verify pytest line | 0 | PASS: 58 passed |
| W01, W02, W06, W09, guard, ConPort wiring, hooks, capture, CLI capture, two integration ledger suites, dope-memory endpoint, MCP lifecycle (services venv) | 1 | FAIL: 2 failed, 655 passed (below) |
| after the W01 test follow-up, W01 + W06 + capture + hooks | 0 | PASS: 194 passed |
| `git diff --check`, pre-commit (`SKIP=markdownlint`) | 0 | PASS (markdownlint NOT_RUN) |
| TDD failing-first (child) | 1 | recorded: 21 failed, 2 passed (the two fail-open tests) |

## What W06 did

- `capture_client.py`: `PRINCIPAL_CLI = "internal:cli"` (default) and `PRINCIPAL_HOOKS = "internal:hooks"`; a `principal` keyword on the three emit functions; only `internal:*` is accepted (a local writer may not self-assert `runner:*`); the INSERT names both W01 columns and writes the self-asserted marker as the literal 1; a principal inside the event payload is ignored.
- `native_hooks.py`: passes `internal:hooks` to its capture call and adds `write_principal` / `write_principal_self_asserted` to the `dopemux:events` XADD envelope. No exit code or block decision changed; Redis and capture failures stay swallowed.
- Beyond B01's literal text, inside the surface: capture_client's `activity.events.v1` fan-out carries the same two fields. Accepted: additive, tested, consistent with design 5.3.

## Open items

1. **`tests/integration/test_dual_capture_convergence.py:250` fails, caused by W01.** Its column-less `INSERT INTO raw_activity_events VALUES (11 values)` now meets 13 columns, so it raises a column-count error before the read-only check it means to test. CI runs `tests/integration` (`ci-complete.yml:490`), so the PR would go red. The fix is one explicit column list in that test; the file is in no R2 write surface (operator decision). No production code inserts into the four ledger tables without a column list (checked across `src/`, `services/`, `scripts/`).
2. The Redis principal fields are provenance only today: `eventbus_consumer.py` stamps every row it writes `internal:wma` and ignores them. The design does not say it should honour them; changing that is a red-lane edit.
3. Hook error captures use `emit_event_bus=False`, so they produce ledger rows with `internal:hooks` but no capture_client Redis event.
