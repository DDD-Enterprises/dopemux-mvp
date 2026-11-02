# MACRO-DMX-RUNNER-MEMORY-2A-001-R2 — Amendment 04: omitted write ids default to the server's binding (W12)

**Recorded:** 2026-11-01 (UTC), by the team lead (Control Tower supervisor session), after W08 (`05c1def3e`).

**Operator words (verbatim):** "Default to the binding (Recommended)"

**In answer to (verbatim):** "Claude Code (on direct HTTP until 2B) must now send each server's exact workspace id on every write, which it can't know, so its memory writes would mostly fail once the new images run. How should 2A handle it?"

The chosen option read: "Each server fills an omitted workspace_id (and instance_id) from its own binding; a supplied workspace that doesn't match is still rejected, so nothing can be filed under another workspace. Claude's writes keep working. Small W12 change to the already-exempt dope-memory/ConPort server files plus docs; relaxes design G1 from 'reject a write without workspace_id' to 'never store a write under any workspace but the server's own'."

## Why

W01 and W02 reject any HTTP write that omits `workspace_id` (and `instance_id` where the row has one), in every auth mode. The values differ per server (`lifecycle.py:1218-1228`):

| Server | Binds to | Example |
|---|---|---|
| dope-memory | `Path(worktree_root).name` | `dopemux-mvp` |
| ConPort | `identity.workspace_id` or `worktree_root` | the full path |

Instance ids are a worktree hash. W08 flagged the problem. Under Amendment 02, Claude Code stays on direct HTTP until 2B and gets no help filling these values, so once the new images run its writes would succeed only when the model guessed them right. The team lead missed this when recommending Amendment 02.

## Effect

**Omitted ids are filled from the server's own binding.**

| Server | Omitted `workspace_id` | Omitted `instance_id` |
|---|---|---|
| dope-memory | its binding | `DOPE_MEMORY_INSTANCE_ID`, else `A` |
| ConPort | its binding | `DOPEMUX_INSTANCE_ID` where the table has an instance column, else `shared` (NULL) |

Empty strings count as omitted. A caller's value is never replaced.

**Still rejected:**
- a supplied `workspace_id` that differs from the binding;
- a ConPort path workspace that disagrees with the body workspace;
- every write to a server with no binding.

**Schemas:** MCP write tools and REST request models mark the ids optional. The health field `identity_required_writes` stays `true`, now meaning "writes are bound to this server's workspace". W07's gate reads it, and its name is kept.

**Design deviation (2A revision 2):** G1 changes:

| | Wording |
|---|---|
| Before | "reject an HTTP write without `workspace_id`" |
| After | "never store an HTTP write under any workspace but the server's own; reject a mismatched one" |

The incident behind ADR-MCPINT-002 (writes filed under another repo's workspace) stays impossible, because the binding check is unchanged and the old env defaults (`default`) are not restored. G2 (verified principal on HTTP writes; tokenless writes rejected in `enforce`) is unchanged.

**Docs:** W08's docs (`05c1def3e`) are corrected in W12 (B05). That removes the "writes without ids are rejected" claims and the caveat that Claude Code's direct writes may get 400s.

## W12

| Field | Value |
|---|---|
| Packet | `task-packets/MACRO-DMX-RUNNER-MEMORY-2A-001-R2/WORKSTREAMS/W12/TASK_PACKET.json` (copy: `W12_TASK_PACKET.json`) |
| Packet sha256 | `5d021f2a03691aec03a6dcbd264a5bedede7c1faf94d7bdafe10a8099f5d2f55` |
| Schema | `task_packet.v2` PASS |
| Depends on | W01, W02, W07, W08 |
| Lane | L3 |
| Red-lane files | Every one it touches is already among ADR-227's 22 exemptions |
| Route | claude-code-agent, `claude-sonnet-5-5` |
| Caps | 90 min, 1.0M tokens, 200 tool uses |

## Still not authorized

Push or PR; signing; the audit route; token issuance; migrations against a real database; the enforce switch; the ADR-MCPINT-002 amendment's acceptance; image rebuilds; the live Codex run; merge.
