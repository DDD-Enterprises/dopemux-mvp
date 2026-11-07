# W12 return — TP-DMX-RUNNERMEM2A-R2-W12-DEFAULT-TO-BINDING-001

**Child status:** NEEDS_SUPERVISOR (first round: `conport_mcp_stdio.py` was outside its write surface, an omission by the team lead), then READY_FOR_AUDIT after the correction round. **Team lead disposition:** write surface extended by the Amendment 04 addendum (`a706df85f`), one correction round, committed as `d314f2141`. Audit: NOT_RUN (held for J04-FREEZE).

## Route and counters

| Field | Value |
|---|---|
| Binding | `W12_EXECUTION_BINDING.json`, `ct validate-binding` PASS |
| Requested route | claude-code-agent, `claude-sonnet-5-5`, effort UNKNOWN |
| Observed model | `claude-sonnet-5-5` on all 237 assistant turns, both rounds (harness record) |
| First round | 884 s / 274,315 tokens / 152 tool uses |
| Correction round | 1,057 s and 307,950 tokens and 171 tool uses as cumulative notice values; the round itself was small (2 files) |
| Caps | 90 min / 1.0M / 200 |
| advisor calls / subagents | 0 / 0 (structural count: Bash 41, Read 28, Write 6, Edit 94, SubagentHandback 2) |
| Live, keychain, image or `dopemux mcp` commands | 0 |

**Process deviations (first round, disclosed by the child, no effect on the repo):**
- 15 read-only commands began with `cd /tmp`.
- One pre-commit log was written to the scratchpad through a shell redirect.
- Three other redirects went to `/dev/null`.

The correction round used none of these.

## Write surface

24 paths, all inside the W12 write surface plus the addendum file (`conport_mcp_stdio.py`). Every server file is among ADR-227's 22 exemptions. `instance_detector.py` was not needed.

## Validation (team lead re-ran)

| Command | Exit | Bucket |
|---|---|---|
| Whole 2A set, services venv: W01-W07, W09, W10, W12, guard, ConPort wiring, hooks, config generation, catalog and arch contracts, repair, capture, ledgers, dope-memory endpoint, MCP lifecycle, caller suites, `tests/pr_steward`, `tests/dcp` (deselecting the pre-existing `test_dcp_0002 … test_16`) | 0 | PASS: 2,066 passed |
| W12 commit.verify test lines, worktree venv | 0 | PASS: 583 passed, 32 skipped (MCP tests need fastmcp; NOT_RUN there, run in the services venv) |
| `git diff --check`, pre-commit on all 24 files (`SKIP=markdownlint`) | 0 | PASS (markdownlint NOT_RUN) |
| TDD failing-first (child, first round) | 1 | recorded: 155 failed, 49 passed (services venv) |
| TDD failing-first, correction round | — | NOT_RUN (disclosed by the child) |
| Live servers, rebuilt images | — | NOT_RUN |

## The rule as built

| Server | Omitted `workspace_id` becomes | Omitted `instance_id` becomes |
|---|---|---|
| dope-memory | `DOPE_MEMORY_WORKSPACE_ID` | `DOPE_MEMORY_INSTANCE_ID`, else `A` |
| ConPort | `DOPEMUX_WORKSPACE_ID` | where the table has an instance column: `DOPEMUX_INSTANCE_ID`, else `shared` (NULL) |

Blank values count as omitted. A caller's value is never replaced.

ConPort exceptions:
- `fork_instance` keeps `target_instance` required.
- `promote_all` refuses `shared`.
- `custom_data` has no instance column.
- `decisions.created_by_instance` takes the server instance (the child's reading of "where the table carries one").

**Kept rejections (each has a named test in `W12`):**
- a supplied workspace that is not the binding (both servers, REST and MCP);
- a ConPort path workspace that disagrees with the body or the binding;
- every write to an unbound server;
- an entry belonging to another workspace when the workspace is omitted.

**Schemas:** every MCP write tool on all four surfaces marks the ids optional, with a description naming the binding:
- dope-memory HTTP;
- ConPort SSE/streamable (`server.py`);
- ConPort stdio (`conport_mcp_stdio.py`);
- ConPort REST `/mcp`.

The REST models mark them optional too. When ConPort's `update_context` gets no workspace, it takes the path workspace from the binding; if the server is unbound it refuses and sends nothing.

`identity_required_writes` stays `true`, now meaning "writes are bound to this server's workspace".

## Notes for the audit

- **Docs updated** (how-to, ADR-MCPINT-002 amendment draft, `AGENTS.md`, `.claude/claude.md`). The child left the enforce-blocker items "container ids are unknown" and "bridge progress route drops instance_id" unchanged, as B05 asked. They are weaker now that the servers fill omitted ids.
- **The stdio tools' parameter order changed** (required arguments first). No code imports or calls them positionally; they are reached only by keyword as MCP tools (`git grep conport_mcp_stdio`).
