# MACRO-DMX-GUARD-FILE-REPO-001 — Issuance Record (Wave 2B Task 0, its own PR)

**Issued**: 2026-11-12 by the Control Tower supervisor session (Claude Code desktop, `claude-opus-5-5`, effort `xhigh`).
**Why**: the operator asked for Task 0's packet ("Yes, draft Task 0"). Wave 2B's hook core (R2 W09) imports `file_repo_root` and `tool_edit_path` from the guard, so W09 waits for this PR to merge (2B join J-T0).
**Source**: Task 0 and row C12 of `claudedocs/plans/2026-11-05-runner-memory-parity-2b.md`, sha256 `7479fa612d67037bd105edaf948266d8516f21ad2ad5584ed933f52ec9fc462b`. The plan is not in this PR; each packet restates what it needs.
**Base**: main `264c97b23ec1b3e007e62079d4f6d2632ad71775`. Authority NONE. **Nothing has run.**

## What changes

The DCP PreToolUse guard (`.claude/hooks/dcp_surface_guard.py`) runs before every edit in every Claude Code session in this repository. Two gaps today:

- **Sibling worktrees.** It reads an edit's path relative to the session's project root. An edit to a red-lane path in another worktree, for example `services/task-orchestrator/x.py` under `.worktrees/<other>/`, is outside that root, so it is not checked. After the change it is checked against the repository that actually holds the file.
- **Notebooks.** It reads only `file_path`, so `NotebookEdit`, which sends `notebook_path`, is never checked.

Edits made through a shell command or Codex's `apply_patch` are not in scope here; Wave 2B W09 handles those (plan row C17).

## Execution gates

```
AUTHORIZE_MACRO_DMX_GUARD_FILE_REPO_001_EXECUTION=YES
```

Covers: the worktree `.worktrees/guard-file-repo-root` on a new local branch `fix/guard-file-repo-root` from main `264c97b23`; an import commit of this package; G01 with one local commit.

```
AUTHORIZE_MACRO_DMX_GUARD_FILE_REPO_001_PUBLISH=YES
```

Covers G02 only: push `fix/guard-file-repo-root` without force, open one PR to main as a draft, mark it ready once CI is green (bot reviewers skip drafts), reply on and resolve review threads.

Both lines can be given together. Neither covers the audit route, signing, the solo-owner release phrase or the merge: those stay yours.

## Workstreams

| ID | Work | Lane | Runs after | Route | Caps (min / tokens / tool uses) |
|---|---|---|---|---|---|
| G01 | `file_repo_root`, `tool_edit_path`, six tests | L3 | — | Sonnet child | 60 / 0.6M / 150 |
| G02 | Push, PR, ready, settle CI and reviews, freeze | L3 | G01 + publish gate | supervisor | 90 / n/a / 120 |

Macro caps (PROPOSED, excluding operator and CI waiting time): 6 h, 1,200,000 subagent tokens, 2 child dispatches, 2 correction rounds, 0 intermediate audits, `advisor` 0. The final audit is one call on a route you pick.

## Joins

| Join | Holds until |
|---|---|
| J-IMPL | G01 committed and its suites re-run green by the team lead |
| J-FREEZE | CI and bot reviews settled, head frozen; then your audit route, signing and merge |

## Why the package is under `proof/`

The change-contract gate (`scripts/governance/validate_change_contract.py`, run by `embedded-audit.yml`) schema-checks every `task-packets/*.json` in a PR against the dopetask spec. GEC v2 packets do not follow that spec: all 14 files of the 2B R2 package fail it. 2A's packages reached main under `proof/<macro>/review_bundle/`, which the gate does not schema-check. This package follows that precedent.

## Package members

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `73247c2489570bc65efcb693974bd388937850bcf33c4b326bc53f59a67b2f90` |
| `EXECUTION_BINDING.json` (issuer) | `60db7c67ccb48f5e74e5bed648fcdc7a0d9357e59097d3a2798e033de4a91a0a` |
| `WORKSTREAMS/G01/TASK_PACKET.json` | `992d2a1be965d900f441a14bc101984274070e98e9be808b456a69af79f0b51d` |
| `WORKSTREAMS/G02/TASK_PACKET.json` | `0eac3339de1b2bb4e0f1da10a242e882c120dc8e5643c57851cf587f32b96003` |

## TP_ROUTE

```
TP_ROUTE   (issuer)
runner=claude-code-desktop
model=claude-opus-5-5
effort=xhigh
skills=task-packet
why=a change to the guard every Claude session here runs before each edit; scope and publishing stay with the supervisor

TP_ROUTE   (G01)
runner=claude-code-agent
model=claude-sonnet-5-5
effort=UNKNOWN
skills=superpowers:test-driven-development
why=one file and six named tests with exact signatures; same route as the 2B build children

TP_ROUTE   (G02)
runner=claude-code-desktop
model=claude-opus-5-5
effort=xhigh
skills=NONE
why=outward-facing steps (push, PR, ready, review replies) stay with the supervisor

TP_ROUTE   (final audit, after J-FREEZE)
runner=UNKNOWN
model=UNKNOWN
effort=UNKNOWN
skills=independent-audit
why=one L3 audit, different family from the implementer; the operator picks the route
```

## Validation at issuance

| Check | Result |
|---|---|
| `task_packet.v2` schema, G01 and G02 | PASS ×2 |
| `macro_packet.v2` and `execution_binding.v2` schemas | PASS ×2 |
| Negative controls (missing rollback; an intermediate audit; a macro claiming authority) | each rejected, as intended |
| `ct validate-macro` | PASS, STATIC_VALID, authority NONE (a first draft failed "child actions exceed global ceiling"; fixed by listing push, open_pr and mark_ready in the ceiling, still behind the publish gate) |
| `ct bind-record` + `ct validate-binding` (issuer) | PASS |
| `SHA256SUMS.txt` | PASS |
| Scan for home paths, e-mail addresses and the W0 scan terms | PASS, no match |
| `.claude/hooks/dcp_surface_guard.py` in `FORBIDDEN_PATHS` | no: no carve-out needed |
| Baseline of the guard's suites (`tests/test_dcp_surface_guard.py`, `tests/unit/runner_memory_2a_r2_w09`, `tests/dcp`) on code identical to main | 458 passed, 1 failed: `test_16_no_forbidden_files_modified`, pre-existing (it diffs an old packet base and trips on main's own workflow history) |
| Any code, test or runner behaviour | NOT_RUN |

## Decision for the operator

Authorize Task 0 with the execution line, and the publish line if you want the PR opened in the same pass.
