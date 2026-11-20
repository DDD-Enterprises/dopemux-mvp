# G02 return — PR 1513 head frozen (fourth freeze)

**Status**: READY_FOR_AUDIT (the team lead's word; acceptance belongs to the auditor and the operator).

**Subject (frozen content head)**: `72aa9c902ceec12a705f6993f98b7eb86e61c6ba` on `fix/guard-file-repo-root`, PR https://github.com/DDD-Enterprises/dopemux-mvp/pull/1513, base `main` at `ba5c3e07b01ad46cae0d55cefdfbb9f9b3b647d7` (merge base; `origin/main` unchanged, PR 0 commits behind).

**Audit**: NOT_RUN on this head. No audit has been run on any head that contains Amendment 11.

The commit that adds this file changes only proof files, so it sits on top of the frozen head. The audit prompt carries git's own list of that range in its trusted section.

## Earlier freezes (all spent)

| Freeze | Content head | Audit result |
|---|---|---|
| first | `6212c8db4` | Grok: NEEDS_SUPERVISOR |
| second | `7a469cb21` | Grok: FAIL; AGY: FAIL |
| third | `dc5aac697` | Grok: FAIL; AGY: FAIL |
| fourth (this file) | `72aa9c902` | NOT_RUN |

Amendment 11 (`72aa9c902`) answers the third freeze's audits: AGY found two more symlink shapes (a two-level link target followed by `..`; a link beside a symlinked red-lane ancestor), Grok found that an aborted walk let the path through. The third freeze record also said a chain longer than 40 links is hard-blocked. At that head it was not; since Amendment 11 it is. The operator's ruling set a stop rule: if the audits of this head FAIL on another symlink shape, there is no Amendment 12 and the supervisor brings the descope choice.

Verdicts and evidence of the earlier rounds are in `~/.local/share/dopemux/evidence/pr1513/r1` to `r3`, outside the repo. Amendments 02-11 each have a record (`AMENDMENT_02.md` to `AMENDMENT_11.md`) with the operator's words, the reason and the validation at that edit.

Against `main` the PR changes 24 files: the guard (`.claude/hooks/dcp_surface_guard.py`), its tests (`tests/unit/dcp_surface_guard/`, 2 files) and 21 files under `proof/MACRO-DMX-GUARD-FILE-REPO-001/`. No workflow file is touched.

| File at the frozen head | SHA-256 |
|---|---|
| `.claude/hooks/dcp_surface_guard.py` | `d81692f3562c2a5fd3d5925fe92c81356613e21bd363c69c1a4ef45f6da55765` |
| `tests/unit/dcp_surface_guard/test_file_repo_root.py` | `69cafe14d7537a3567dbd76140fbae74fdeaac8cc1cc5c748a79ca67b7d824c4` |

## State at freeze (observed 2026-11-20 about 04:10Z)

| Item | Result |
|---|---|
| Local head equals remote head | PASS: both `72aa9c902`; worktree clean |
| PR up to date with `main` | PASS: 0 behind, 21 ahead |
| PR out of draft | PASS |
| Review threads | PASS: 0 unresolved of 10 |
| Copilot review of the frozen head | NOT_RUN: two requests (the CLI one did not register; the REST one returned 201 Created), no review or work-started event in about 28 minutes. The last Copilot review, of `dc5aac697`, listed no open issues. |
| CI on the frozen head | 20 pass, 2 fail, 3 skipped. The failures are `independent embedded audit` and `PR Steward / final readiness`, which wait for the audit and have failed on every head. |

## Local validation on the frozen head

Clean env (`env -i`, `PATH=/usr/bin:/bin`, `PYTHONPATH=<worktree>/src`), repo `.venv` Python, clean worktree.

| Check | Result |
|---|---|
| Guard tests (`tests/unit/dcp_surface_guard`) | PASS: 59 passed |
| Same tests against the guard at `e95187bb2` | 9 failed, 50 passed (measured at the Amendment 11 edit) |
| 32 test files that mention the guard, native hooks or red lane | 1049 passed, 1 failed |
| `flake8 --select=E9,F,W` | PASS |
| `black --check` | FAIL: not reformatted; the files already failed it before Amendment 11 |
| Saved reproduction probes (AGY r2, Copilot x3, AGY r3, Grok r3) | PASS: every red-lane shape blocked; outputs `*.after_a11.out` in `r2/repro` and `r3/repro` |
| 14 ordinary paths on this machine (`/tmp`, `/var/folders`, repo, `~/.claude`, sibling projects) | PASS: none blocked, no walk abort |
| Full `make test` | NOT_RUN |

The one failure is `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`; it fails the same way on `main` and on every earlier head of this branch.

## Known limits carried into the audit

- **Open gap, same on `main`.** When a sibling checkout's red-lane folder is a symlink to a folder outside every repo, an edit addressed by that folder's own path is allowed. The guard does not search other checkouts for links that point at it. Needs a design decision; belongs in a follow-up (`AMENDMENT_10.md`, `AMENDMENT_11.md`).
- **Fail-closed cost.** A path is hard-blocked when its symlink walk cannot finish: more than 64 spellings (six stacked links), a loop, a chain past 40 links, or an unreadable link. That also blocks ordinary files behind that many links. The kernel refuses chains over about 32 links.
- **`file_repo_root`.** The exported helper returns the first `.git` above the realpath. The guard does not use it; a Wave 2B caller that blocks from it alone would miss a root the guard keeps.
- **Writer exception.** Amendments 02-11 were written by this supervisor session under one-off operator exceptions, outside the packet's named writer and attempt limits. Each is recorded with the operator's words. An auditor rated this a governance finding.
- **Family not closed by proof.** Reviews and audits found a new symlink / `..` variant on every earlier head. That the walk now closes the family is untested beyond the test file and the saved probes.

## Route

- Amendments 02-10 were written while the session model was `claude-fable-5-2`; Amendment 11 and this record under `claude-sonnet-5-5`, set by the operator with `/model`. Provider-attested model: UNKNOWN. `$CLAUDE_EFFORT` read `high`.
- Subagents spawned for this record: 0.

## Blockers

| Blocker | Action that clears it |
|---|---|
| Audit NOT_RUN | Grok governs and AGY gives a second look, both on the audited head. The sealed prompt is near AGY's size limit; the operator decides how to fit it. |
| Copilot review of this head NOT_RUN | A later review may add findings and would void an audit run before it. |
| Signing, steward release phrase, merge | The operator's, after the audit. |

If any commit that changes code or tests lands after this record, this freeze is void.

Files written: `proof/MACRO-DMX-GUARD-FILE-REPO-001/G02_RETURN.md`. Rollback: `git revert` of this file's commit restores the third freeze record. Closing the PR and deleting the branch is the operator's. Authority: NONE.
