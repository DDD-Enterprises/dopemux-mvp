# MACRO-DMX-CMD-REPAIR-001 — Aggregate Return 01

**Status**: `PARTIAL_BLOCKED`. W01–W04 implemented and committed. The integration head is NOT frozen and the final audit was NOT run. The stop is the packet's `semantic_out_of_allowlist` / `architecture_conflict` immediate-return trigger.
**Authority**: NONE. This aggregate mints no PASS/READY/DONE.
**Recorded**: 2026-10-16 ~20:20Z by the coordinator, session "Dopemux mods and plugins analysis" (`c311455f-f4c3-4513-b995-82ff91a5ca87`).

## Authorization consumed

- **Launch instruction**: `/Users/hue/Documents/Codex/2026-10-16/task-12/ORIGINAL_CLAUDE_LAUNCH.txt`, sha256 `c2404929…d4c1`. The operator pointed to it in chat ("use sonnet: <path>"). It carries `AUTHORIZE_MACRO_DMX_CMD_REPAIR_001_EXECUTION=YES`.
- **Operator override (chat AskUserQuestion)**: "Sonnet coordinator, now (Recommended)". The issued team-lead binding (`claude-opus-5-5`) was overridden to `claude-sonnet-5-5`; workers stayed as pinned.
  - **Override not realized**: a session cannot re-price its own turns (the app refused `set_session_model` on self). The operator had not selected Sonnet in the model menu, so `get_session` showed `claude-opus-5-5 / xhigh` at 20:06Z and 20:13Z. **Every coordinator turn so far ran on claude-opus-5-5.** The coordinator binding records Sonnet as requested and Opus as configured.

## Route and capacity facts

- **Plan and route**: Max plan; extra usage (paid) OFF at 20:06Z and 20:20Z. This native desktop session uses its own route. pxpipe (127.0.0.1:47821) is not in its path. The shared text-review runner was not used or changed.
- **Weekly quota**: all-models usage went from 98% to 99% during the run; it resets 2026-10-16T22:59:59Z.
- **Runner owner**: runner owner `01a145df…` was not messaged. The C06A release receipt (sha256 `68a486e4…`) was taken as given from the launch file and not re-verified here. No C06A budget was transferred.

## Custody

- **Worktree**: `/Users/hue/code/dopemux-mvp/.worktrees/cmd-repair-001`, branch `fix/cmd-repair-001`, created from a fresh `origin/main` = `95e95bee88cae5e6c95e6e34f7c28bb423ad9496`. HEAD was hard-equal and the porcelain status clean at creation.
- **Writers**: the coordinator was the sole committer. W01 and W03 ran concurrently on proven-disjoint files. Commits were deferred until both finished, because pre-commit stashes unstaged changes.
- **Main checkout**: untouched, including its dirty doctrine edits. Checkpoint `01a13db3` and audit `01a14638-0128` files were not touched.
- **Bindings**: recorded in the worktree's ignored state, `.control-tower/state/bindings/` (coordinator + 4 children). All 5 PASS `ct validate-binding`.

## Children (launched 4; resumed 1 for supervisor rulings)

| WS | Requested | Observed (transcript `message.model`) | Advisor | Commit | Files | Status |
|---|---|---|---|---|---|---|
| W01 ConPort names | claude-haiku-5-5 (Sonnet fallback allowed) | claude-haiku-5-5 ×35 | 0 | `55e4f6cad` | 18 | PASS after STOP + rulings R1–R6; fallback NOT used |
| W03 dead targets | claude-sonnet-5-5 | claude-sonnet-5-5 ×19 | 0 | `b0c505489` | 5 | PASS |
| W02 model pins | claude-haiku-5-5 | claude-haiku-5-5 ×8 | 0 | `08130eb5c` | 26 | PASS |
| W04 drift gate | claude-sonnet-5-5 | claude-sonnet-5-5 ×31 | 0 | `9c93afbb7` | 1 | Own test PASS; `tests/arch` FAIL (sibling, see blocker) |

- **Effort**: requested `runner-default`; observed UNKNOWN for all four.
- **Forbidden git**: none mutating. W04 ran `git stash list | head -0`, a read-only listing.
- **Edit method**: W01, W02 and W03 edited through the shell rather than the Edit tool. Each commit's diff was checked against its allowlist by the coordinator: W02 `diff == allowlist`; W01 and W03 used explicit allowlist pathspecs.

**W01 supervisor rulings**:
- **R1 `followup.md`**: removed the `linked_item_*` arguments, which are unsupported. The live `log_progress` only links decisions, and the custom_data target was never created. The slug is kept in the description.
- **R2 `bootstrap.md`**: decisions through `search_content`; caveats through `get_custom_data(category="caveats")`.
- **R3 `mem/summarize.md`**: `get_custom_data` for `mem` and `scratch`, plus `get_decisions`.
- **R4**: `update_progress` without `workspace_id` accepted, matching the live signature.
- **R5**: `update_context` patch-vs-replace semantics recorded as UNKNOWN.
- **R6 `caveat.md`**: the search hint now points to `get_custom_data`.
- **Why R2/R3/R6**: `search_content` covers decisions and progress only, per `server.py`'s docstring.

**W03 decisions**:
- **REMOVE** `adr_new.py`, `docs_manifest.py` ×2 and `set-profile.sh`. Each now has an "unavailable" note.
- **REPOINT** `plan.md` to `pal-stdio` `planner` (cited at `mcp_catalog.yaml`).
- **REPOINT** `plan-tasks.md` to task-orchestrator `create_work_tree` (live in the July capture).

## Validation (on head `9c93afbb75f4792c2dace665a5793a60c862fa51`)

| Check | Result |
|---|---|
| `rg 'conport_[a-z]'` / `rg '_fts\b'` / dead-target regex over `.claude/commands` | PASS (exit 1 = no matches, each) |
| No stale `*-4-5` pins | PASS |
| W02 one-line-per-file | PASS |
| `pytest tests/arch/test_claude_command_references.py` | PASS: 11 passed, 0.11 s |
| W04 negative control on the base tree (`95e95bee8`) | PASS as a control: check 1 = 25, check 3 = 26, check 4 = 3, check 2 = 0 (expected; only the synthetic tests exercise it) |
| `black --check` / `flake8` on the new test | PASS / PASS |
| `git diff --check 95e95bee8..HEAD` | PASS |
| `pytest tests/arch -q` | **FAIL**: 1 failed, 194 passed (see blocker) |
| Pre-commit hooks at commit time | Ran implicitly through `git commit` (exit 0). Explicit `pre-commit run --files` was NOT_RUN |
| Changed-contract preflight (`validate_change_contract.py`) | NOT_RUN (stopped before freeze) |
| Live ConPort runtime qualification | NOT_RUN. The July 2026-07-16 capture is historical provenance, not current runtime proof |
| Freeze / final independent audit (AGY Gemini, different family) | NOT_RUN. No frozen subject |
| Proof bundle (§9) | NOT_RUN |

## Blocker (immediate return: architecture conflict, outside allowlist)

`tests/arch/test_mcp_fleet_catalog_contract.py::test_claude_command_tool_surfaces_are_catalog_known_or_explicit_aliases` fails on the head. It checks commands against `_CONPORT_TOOL_SNAPSHOT` in `src/dopemux/mcp/fleet_catalog.py:33-57`, which is "a snapshot of the ConPort JSON-RPC dispatch map in enhanced_server.py" and lists `conport_*` names. That snapshot came from packet `DMX-HYG-CONPORTREFS-003` (2026-07-09), whose target was "Repoint broken ConPort command tool references to the runtime-backed JSON-RPC dispatch surface". So two repo authorities disagree:

- **JSON-RPC (`conport_*`)**: `enhanced_server.py` serves it at REST :3004 `/mcp`. Backed by the prior packet, the fleet snapshot, and the existing arch test.
- **SSE (unprefixed)**: `server.py sse` serves the MCP protocol on :3005 (`start_with_info.sh:6-7`). **This is what `.mcp.json` connects Claude to** (`type: sse`, `:3005/sse`). The 2026-07-16 live capture of that endpoint lists the unprefixed names, and Claude names tools `mcp__conport__<SSE tool name>`. Backed by this macro.

On that evidence the unprefixed names are what Claude Code actually calls, so W01 is runtime-correct for Claude. The fleet snapshot gates the wrong surface for `.claude/commands`. The fix lives in `src/dopemux/mcp/fleet_catalog.py`, which is excluded by I03, so the coordinator did not edit it.

**Decision needed (operator)**: authorize a W05 amendment with:
- **Allowlist**: `src/dopemux/mcp/fleet_catalog.py` only. L2. Route: claude-sonnet-5-5.
- **Change**: replace `_CONPORT_TOOL_SNAPSHOT` with the 17 SSE tool names (`mcp_tool_surfaces.json` conport, equal to `server.py`), and correct its comment to name the :3005 SSE surface.
- **Pass criteria**: `tests/arch` returns to green; existing negative tests (`missing_tool`) unaffected.

After that come freeze, the change-contract preflight, the single AGY final audit and the proof bundle. The alternative is to revert W01 to the JSON-RPC names, which would also require changing W04's check 1. That is not recommended: it contradicts `.mcp.json`.

## Process and custody closure

- **Children**: all 4 reached terminal state (completed). No background processes or agy runs are outstanding.
- **Branch and worktree**: retained.
- **Remote**: nothing pushed; no PR; no merge.
- **Local state**: binding records stay in the worktree's ignored state.
- **Generators**: the scripts for bindings and the transcript parser live in the session scratchpad, outside the repo.

## Rollback

```bash
git worktree remove .worktrees/cmd-repair-001
git branch -D fix/cmd-repair-001
```

Branch deletion is an operator-only gate. Alternatively, revert any single workstream commit.
