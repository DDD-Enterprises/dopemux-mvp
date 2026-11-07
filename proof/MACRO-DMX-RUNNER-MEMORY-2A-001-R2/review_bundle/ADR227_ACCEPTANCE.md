# MACRO-DMX-RUNNER-MEMORY-2A-001-R2 — ADR-227 acceptance (J01-CARVEOUT)

**Operator words (verbatim, chat, 2026-10-31):** "Accept ADR-227"

**In answer to (verbatim):** "do you accept ADR-227 as written (exactly 20 files exempted, everything else stays blocked), or do you want to change something first?"

**Recorded at:** 2026-11-01T00:07:18Z (2026-10-31 local) by the team lead (Control Tower supervisor session).

## What was accepted

| Item | Value |
|---|---|
| ADR | `docs/90-adr/adr-227-memory-spine-seam-narrow-carveout.md` as committed in `95c54c4ec` |
| ADR sha256 at acceptance | `76f33e0de4b273c9b13eb03879ced0708fc73a2acde982c2685dabd9d3a5da48` |
| Rules file | `src/dopemux/dcp/red_lane_rules.py`, sha256 `9833b5d40adb4b3ee2cdd4a444356679e10a77518e03f7ad31f124a66eb5a59f` (unchanged since `95c54c4ec`) |
| Exemptions | exactly 20 file-exact paths: 9 under `services/working-memory-assistant/`, 9 under `docker/mcp-servers-source/conport/`, 2 under `services/dopecon-bridge/`; every other path in those trees stays blocked |

On acceptance the team lead changed only the ADR's front-matter `status` (proposed → accepted) and its Status entry. The rules file and tests are untouched.

## J01-CARVEOUT

| Condition | State |
|---|---|
| W09 committed (ADR, rules, tests; 196 passed) | MET (`95c54c4ec`) |
| Operator accepted ADR-227 | MET (this record) |

J01-CARVEOUT passes. W01, then W02 and W05 in their order, may edit the exempted files and no others (C12).

## Enforcement note for the R2 dispatch route

W09 reported `carveout_effective_in_worktree = YES` for a session whose working directory is the worktree root: the PreToolUse guard builds its root from the hook process's working directory (`src/dopemux/claude/native_hooks.py:275`).

This team-lead session's working directory is the main checkout (`/Users/hue/code/dopemux-mvp`). From there a worktree edit resolves to `.worktrees/runner-memory-2a/services/...`, which no `^`-anchored red-lane pattern matches (`.claude/hooks/dcp_surface_guard.py:85-104`). So for children dispatched from this session the guard neither allows nor denies on the carve-out: it does not fire at all. This is the known fail-open defect, reported separately and outside R2's scope.

C12 is therefore enforced by the team lead, not by the hook. Before each commit the team lead checks `git status --porcelain` against the child's write_surface, and fails the workstream on any path outside it.

## Still not authorized

The R6 gate for PR #1482, the keychain ACL procedure before W03, push or PR, signing, the audit route, token issuance, migrations against a real database, the enforce switch, the ADR-MCPINT-002 amendment, the live Codex run, and merge.
