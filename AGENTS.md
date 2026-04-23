# AGENTS.md

## 1. Purpose

This is an operator-control document for the current repo state. It is meant to help you act safely without inventing a unified architecture, smoothing over drift, or hiding `UNKNOWN`.

Repo truth beats docs.

## 2. Read This First

- The task packet names `RULES.md`, `PROJECT.md`, `ARCHITECTURE.md`, `SYSTEM_BOUNDARIES.md`, `PM_PLANE.md`, `DOC_TRUST_MAP.md`, and `DOCS_VS_REPO_DIFF.md` as allowed authority.
- In this checkout, the exact packet-named top-level files were not present during this rewrite, but derived tracked references now exist for system boundaries and the PM plane under `docs/03-reference/`.
- The repo-truth artifacts present in this pass are tracked in:
  - `docs/03-reference/truth/truth-systems.md`
  - `docs/03-reference/truth/truth-canonicals.md`
  - `docs/03-reference/truth/truth-gaps.md`
  - `docs/03-reference/truth/truth-interfaces.md`
  - `docs/03-reference/truth/truth-data-events.md`
  - `docs/03-reference/truth/truth-scope.md`
- Do not invent the contents of `RULES.md`, `DOC_TRUST_MAP.md`, or any missing packet-named top-level file. For system boundaries and the PM plane, use the tracked derived references under `docs/03-reference/`, but repo truth beats docs.

## 3. Canonical Operator Surfaces

- `dopemux` CLI is the main operator control plane.
- `services/repo-truth-extractor/run_extraction_v5.py` is the canonical repo-truth extraction path.
- `scripts/dopetask` is the runtime authority for dopetask. `scripts/taskx` is a compatibility shim, not a separate runtime.
- `services/task-orchestrator/app/main.py` is the intended task-orchestrator runtime surface from this pass, but runtime packaging and Docker alignment are unresolved.
- `services/dopecon-bridge/dopecon_bridge/routes.py` exposes important routing and compatibility surfaces, but bridge is not authority.

## 4. PM Plane

- PM truth is split across multiple surfaces. This pass does not support a single-file PM authority claim.
- `services/task-orchestrator` is the workflow coordination and PM write-normalization surface.
- `src/dopemux/pm/writes.py` shows PM writes crossing Leantime, task-orchestrator, ConPort, and dope-memory mirror receipts.
- Agents do not own PM truth.
- Bridge is not authority for PM truth. Treat `/route/pm` as routing, not as canonical state.
- `PM_PLANE.md` is named by the packet, and the tracked derived PM-plane reference is `docs/03-reference/planes/pm/pm-plane.md`. Use the tracked doc as a secondary authority check, not as a replacement for runtime truth.

## 5. Memory and Retrieval

- `dope-memory` is the durable evidence-preserving memory sink.
- `dope-memory` is not the canonical PM status authority.
- `conport` is the structured memory, graph, and semantic retrieval surface.
- `dope-context` is the deterministic code and docs retrieval surface.
- `working-memory-assistant` overlaps with memory-related responsibilities, but this pass did not prove it is the canonical durable runtime for the same authority slice.

## 6. Agent Systems

- Agent system authority is `UNKNOWN`.
- This repo contains at least three agent families:
  - `services/agents`
  - `src/dopemux/agent_orchestrator.py`
  - `services/task-orchestrator/task_orchestrator/agents`
- Do not assume one unified agent architecture.
- Do not route operator decisions through agent abstractions unless you verify the exact runtime path in code and config.
- Agents do not own PM truth.

## 7. Working Rules

- Start from runtime code, config, and tests. Do not start from hopeful docs.
- Prefer canonical writers over bridges, adapters, aliases, and shims.
- Mark `UNKNOWN` explicitly when canonicality is unresolved.
- Treat `RULES.md` as a named-but-absent authority doc in this checkout. For system boundaries, use `docs/03-reference/systems/system-boundaries.md` as the tracked derived reference.
- If a doc conflicts with runtime behavior, repo truth beats docs.

## 8. Docs Trust

- For this rewrite pass, the usable truth docs are the tracked `docs/03-reference/truth/*` references, with `truth-systems.md`, `truth-canonicals.md`, and `truth-gaps.md` carrying the strongest direct operator guidance.
- `DOC_TRUST_MAP.md` and `DOCS_VS_REPO_DIFF.md` were named in the packet but not present in this checkout.
- Older docs and README surfaces may drift from runtime reality. Escalate the drift instead of normalizing it away.
- Repo truth beats docs.

## 9. Known Dangers

- `dopecon-bridge` exposes broad surfaces that can look authoritative. It is not canonical task, workflow, decision, or progress authority.
- Task-orchestrator runtime authority is conflicted across `app/main.py`, `task_orchestrator/app.py`, and the Dockerfile.
- Memory-related surfaces overlap across `dope_memory_main.py`, `main.py`, and `mcp/server.py`.
- Agent responsibilities are duplicated across multiple families, and agent authority is `UNKNOWN`.
- `scripts/dopetask` is the observed runtime, but operator naming still drifts through TaskX language.
- MCP and proxy config surfaces are inconsistent in places, including stale port assumptions and missing launch targets.


<claude-mem-context>
# Memory Context

# [dopemux-mvp] recent context, 2026-04-23 8:04am PDT

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (15,639t read) | 2,704,189t work | 99% savings

### Apr 22, 2026
S2 Investigate and resolve 'find_file' policy warning (Apr 22 at 7:44 PM)
S1 Address policy file warning and confirm Claude-Mem functionality (Apr 22 at 7:44 PM)
S3 Identify and locate 'find_file' policy rules for removal (Apr 22 at 7:44 PM)
S4 Fix Antigravity MCP config JSON error (Apr 22 at 7:44 PM)
S5 Fix Antigravity MCP config JSON error (Apr 22 at 7:46 PM)
S6 Rerun claude-mem installer after fixing Antigravity config (Apr 22 at 7:46 PM)
S7 Rerun claude-mem installer after fixing Antigravity config (Apr 22 at 7:50 PM)
### Apr 23, 2026
1963 6:21a 🔵 Verified core dependencies in multiple project worktrees
1964 " 🔵 Identified uv cache directory
1965 " ✅ Replaced virtual environment with a symbolic link
1966 " 🔵 Verified core Python dependencies after symbolic link creation
1967 6:22a 🔵 Initiated unit tests for dopemux PM writes
1968 " 🔵 Initiated unit tests for dopemux UI PM writes
1969 " 🔵 Initiated unit tests for PM route contracts
1970 " 🔵 Initiated API tests for dopemux
1971 " 🔵 Unit tests for dopemux PM writes passed
1972 " 🔵 Unit tests for dopemux UI PM writes passed
1977 " 🔴 Fixed PM API test for unrecognized status classification
1986 " 🔵 Found remaining imports of dopemux.pm.writes
1988 " 🔵 Found references to workflow transition and update operations
1989 " ✅ Modified PM writes and related files
1990 " 🔄 Refactored PM write boundary and models
1991 " ✅ Staged modifications and untracked files
1992 6:23a 🔴 Pre-commit hooks failed due to missing YAML dependency
1960 " 🔵 Missing core Python dependencies in virtual environment
1993 " 🔴 Pre-commit hooks failed due to missing YAML and trailing whitespace issues
1994 " ✅ Staged modifications and untracked files after pre-commit hooks
1995 " ✅ Cleaned up trailing whitespace in audit report files
1997 " ✅ Applied patch to audit report files
1999 6:24a ✅ Applied patch to audit report files
2000 " 🔵 No staged changes detected in audit reports
2001 " ✅ Pre-commit hooks passed for documentation files
2002 " 🔴 Trailing whitespace detected and fixed in audit reports
2003 " ✅ Applied patch to audit report files
1976 6:26a 🔴 Fixed AttributeError in PM route contracts test
1987 6:29a 🔵 Found usage of dormant /api/pm/work-items/ routes
1998 6:31a ✅ Applied patch to audit report files
2082 7:11a ✅ Verify and harden phase-1 PM writes slice
2083 " 🔵 Staged modifications for PM writes slice
2084 7:12a 🔵 No diff found for audit report files
2085 " 🔵 GitHub CLI authentication status confirmed
2087 7:13a 🔵 Worktree verification and staged files confirmed
2086 " ✅ Staged changes for PM writes slice
2088 " ✅ Committed changes for PM writes verification
2089 " ✅ Pushed branch and created Pull Request
2090 " ✅ Branch pushed and Pull Request created
2091 " 🔵 Current commit hash confirmed
2211 7:48a 🔵 Current Git Worktree and Branch Status
2212 " 🔵 Codebase Search for PM Write and Mirroring Keywords
2210 " ⚖️ Verification Strategy for PM Write Implementation
2213 " 🔵 PM API Test Suite Structure and Functionality
2214 " 🔵 UI Rendering Tests for PM Writes and Confirmations
2215 " 🔵 Unit Tests for PM Write Functions and Classification
2216 " 🔵 Task Orchestrator Adapter Contract Tests
2217 7:49a 🔵 PM Writes Phase 1 Authority Map and Constraints
2218 " 🔵 PM Writes Module: Core Logic and API Definitions
2219 " 🔵 PM Writes UI Helper Functions for Confirmations and Receipts

Access 2704k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>