# MACRO-DMX-CMD-REPAIR-001 — Issuance Record

**Issued**: 2026-10-16T19:35Z by the Control Tower supervisor session (Claude Code desktop · `claude-opus-5-5` · `$CLAUDE_EFFORT=xhigh`)
**Operator instruction**: "Issue the next packet for the dopemux-commands plugin repair first." (chat, 2026-10-16)
**Source**: `claudedocs/dopemux-mods-plugins-opportunity-map-2026-10-16.md` §4.2 (P-A), phase 1 only
**Base**: `origin/main` = `95e95bee88cae5e6c95e6e34f7c28bb423ad9496`. Inventory inputs were verified identical to origin/main: `.claude/commands`, `mcp_tool_surfaces.json`, ConPort `server.py`.
**Authority**: NONE. This record and the package grant no execution authority.

## Execution gate

Implementation starts only after the operator types, in chat:

```
AUTHORIZE_MACRO_DMX_CMD_REPAIR_001_EXECUTION=YES
```

## Package members (immutable; the macro pins each by SHA-256)

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `70f16ae0ed733068f17ecfdd417e2d94391f36c41f3aedd73ecfca86f60ef394` |
| `EXECUTION_BINDING.json` (coordinator) | `10dca84695fe6dd8207bf9b1388ae10721cc3ed13f0887cfa838a48a4ae067d9` |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `9ca0fc3ce33fc4a8bcdf488f7031d282b2ab90fa2960549d4bc7db5e4110282b` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `7f12e520b153facf582ead911532b026f6b921a981e7cf5a4d7f35c69d13d42e` |
| `WORKSTREAMS/W03/TASK_PACKET.json` | `1d9581f17a5aa7486d135a5e7446c2fa898bbd73a2df8544d8aea64fc4db2a5e` |
| `WORKSTREAMS/W04/TASK_PACKET.json` | `236af3f2e1b8b276e732d1bc51ec9e47f28301e616d57c7496c1896ac866d113` |

This `ISSUANCE.md` is not referenced by the macro and is not part of the pinned subject.

## Workstreams and TP_ROUTE

| WS | TP id | Defect class | Files | Deps | Group | Route (preferred → fallback) |
|---|---|---|---|---|---|---|
| W01 | `TP-DMX-CMD-REPAIR-W01-CONPORT-NAMES-001` | 8 dead `mcp__conport__conport_*` names + 2 dead FTS tools | 18 | — | P1 | claude-haiku-5-5 → claude-sonnet-5-5 (fallback only on an evidence-backed STOP) |
| W03 | `TP-DMX-CMD-REPAIR-W03-DEAD-TARGETS-001` | 5 dead targets: `adr_new.py`, `docs_manifest.py`, `set-profile.sh`, `sequential_thinking`, `task-master-ai` | 5 | — | P1 | claude-sonnet-5-5 |
| W02 | `TP-DMX-CMD-REPAIR-W02-MODEL-PINS-001` | 26 stale `*-4-5` `model:` pins → `claude-{sonnet,haiku}-5-5`, tier preserved | 26 | W01 | P2 | claude-haiku-5-5 |
| W04 | `TP-DMX-CMD-REPAIR-W04-DRIFT-GATE-001` | New `tests/arch/test_claude_command_references.py`, with a negative control against the base tree | 1 | W01–W03 | P3 | claude-sonnet-5-5 |

- **Runner**: every child runs as `claude-code-agent`.
- **Effort**: not settable per child from this runner, so it's recorded as `UNKNOWN`.
- **Final audit**: exactly one final independent audit on the frozen integration head. It runs from a different model family, under audit group `AGY-CMD-REPAIR-001`, via the Audit Broker route. Codex review is advisory only and never the auditor.
- **Lane**: L2 for every child. `.claude/commands/**` and `tests/arch/**` match no rule in `scripts/governance/validate_change_contract.py`, so they get the default L2 lane.

**Why W02 runs after W01**: three files carry both defects (`dx/context.md`, `dx/implement.md`, `dx/next.md`). W01 and W03 are DISJOINT and may run in parallel, with `max_mutating_workstreams = 2`.

## Validation at issuance

| Check | Result |
|---|---|
| `ct validate-macro --file MACRO_PACKET.json` | PASS — `STATIC_VALID`, 0 errors |
| `ct validate-binding --file EXECUTION_BINDING.json` | PASS — GEC v2 ExecutionBinding valid |
| `task_packet.v2` schema, W01–W04 | PASS ×4. First generation: W04 FAIL (a step had empty `validation`, which needs minItems 1); fixed and regenerated |
| Pair classification | W01/W03 and W02/W03 DISJOINT; all others DEPENDENCY_SERIALIZED |
| Tamper negative control (+1 byte in W02) | FAIL as expected: `immutable reference digest mismatch` |
| `.dopetaskroot` repo marker | present |
| DCP route / Task Orchestrator state | NOT_RUN. task-orchestrator is unreachable (ECONNREFUSED this session) |

## Execution outline (after the gate)

1. **Worktree.** Create `.worktrees/cmd-repair-001` on branch `fix/cmd-repair-001` from a freshly fetched `origin/main`. HEAD must hard-equal origin/main, with a clean porcelain status. Copy this package in byte-identical and re-verify the SHA-256s.
2. **Bind each child.** Run `ct bind-record` and then `ct validate-binding` for each child before dispatching it.
3. **Dispatch.** W01 and W03 run in parallel. Children edit only their allowlist; they never commit, push, or call `advisor`. The team lead commits one commit per workstream with an explicit pathspec.
4. **Dispatch W02**, after the W01 commit.
5. **Dispatch W04**, then verify on the integration head:
   - The new test and `tests/arch` pass.
   - `black` and `flake8` pass on the new test.
6. **Freeze (J02).** Then run the single final L2 audit, and write a proof bundle under `proof/MACRO-DMX-CMD-REPAIR-001/` per AGENTS.md §9.
7. **Return.** Write the aggregate return (authority NONE). Push the branch and open a **draft** PR only after the operator confirms. No merge.

## Out of scope (follow-up packets)

- Consolidating duplicate commands (`mem-query`/`mem-search`, `plan`/`plan-slice`, the note writers, the research variants)
- Plugin packaging and `marketplace.json`
- Porting `/dx:plan-enter|plan-exit|summary|schema` from the `task-orchestrator-claude-surface` series branch
- Fixing `pal` vs `pal-stdio` server naming
- The `get_active_context` / `get_recent_activity_summary` references in `.claude/claude.md`
- `scripts/ccr_model_tracker.sh` in `statusline.sh` (Pulse territory)

## Generator

The package was produced by a deterministic generator script kept outside the repo, in the issuing session's scratchpad. It recomputes the file inventories (`conport_[a-z]|_fts\b` and the `*-4-5` pin regex) from the checkout rather than hand-typing them. The hashes above are the authority; the script is not needed to verify them.
